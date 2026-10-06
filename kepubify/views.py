"""HTTP routes for the EPUB conversion service."""

import logging
import re
import shutil
import subprocess
from pathlib import Path
from secrets import token_hex
from typing import Annotated

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
from starlette.background import BackgroundTask

from .config import settings

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
logger = logging.getLogger(__name__)


@router.get("/", name="index")
def index(request: Request):
    """Render the upload page."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"max_upload_size_bytes": settings.max_upload_size_bytes},
    )


@router.post("/upload", name="upload")
def upload(request: Request, file: Annotated[UploadFile | None, File()] = None):
    """Upload epub file, convert it and return download URL."""
    file_id = ""
    try:
        if file is None or not file.filename:
            logger.warning("No file uploaded!")
            return JSONResponse({"status": "fail", "message": "No file uploaded!"}, status_code=400)
        if file.size is not None and file.size > settings.max_upload_size_bytes:
            max_size_mib = settings.max_upload_size_bytes / (1024 * 1024)
            return JSONResponse(
                {"status": "fail", "message": f"File exceeds the {max_size_mib:g} MB upload limit."},
                status_code=413,
            )

        original_filename = Path(file.filename.replace("\\", "/")).name
        lowercase_filename = original_filename.lower()
        if lowercase_filename.endswith(".kepub.epub"):
            return JSONResponse(
                {
                    "status": "fail",
                    "message": 'Wrong file extension: ".kepub.epub". Looks like you tried to upload a kepub file!',
                },
                status_code=400,
            )
        if not lowercase_filename.endswith(".epub"):
            return JSONResponse(
                {"status": "fail", "message": "Please upload an .epub file."},
                status_code=400,
            )

        file_id = token_hex(5)
        new_name = Path(original_filename).stem + ".kepub.epub"
        save_as = settings.tmp_dir / f"{file_id}.epub"
        with save_as.open("wb") as destination:
            shutil.copyfileobj(file.file, destination)

        try:
            new_filename = convert(save_as, settings.kepubify_path)
        except ConversionError as err:
            logger.exception("Conversion failed for upload %s", file_id)
            cleanup_files(settings.tmp_dir, file_id)
            return JSONResponse({"status": "fail", "message": str(err), "id": file_id}, status_code=422)

        download_url = request.url_for("download").include_query_params(file=new_filename, name=new_name, id=file_id)
        relative_download_url = f"{download_url.path}?{download_url.query}"
        return JSONResponse({"status": "success", "filename": new_name, "download": relative_download_url})
    except Exception:
        logger.exception("Unexpected error")
        if file_id:
            cleanup_files(settings.tmp_dir, file_id)
        return JSONResponse({"status": "fail", "message": "unexpected error", "id": file_id}, status_code=500)


@router.get("/download", name="download")
def download(file: str, name: str, id: str) -> Response:
    """Return the converted EPUB and remove its temporary files after sending."""
    if not re.fullmatch(r"[0-9a-f]{10}", id) or file != f"{id}.kepub.epub":
        return JSONResponse({"status": "fail", "message": "Invalid download information."}, status_code=400)
    if not name or Path(name.replace("\\", "/")).name != name:
        return JSONResponse({"status": "fail", "message": "Invalid download name."}, status_code=400)

    converted_file = settings.tmp_dir / file
    if not converted_file.is_file():
        return JSONResponse({"status": "fail", "message": "Converted file not found."}, status_code=404)

    return FileResponse(
        converted_file,
        media_type="application/epub+zip",
        filename=name,
        background=BackgroundTask(cleanup_files, settings.tmp_dir, id),
    )


def convert(in_filepath: Path, kepubify_path: Path) -> str:
    """Convert in_file to kepub and return new file name."""
    new_filename = in_filepath.stem + ".kepub.epub"
    new_filepath = in_filepath.parent / new_filename
    p = subprocess.run(
        [str(kepubify_path), str(in_filepath), "-o", str(new_filepath)],
        capture_output=True,
        check=False,
    )
    if p.returncode != 0:
        stderr = p.stderr.decode(errors="replace") or ""
        logger.error("kepubify failed: %s", stderr)
        stderr = stderr.replace(str(in_filepath), in_filepath.name)
        raise ConversionError(stderr)

    return new_filename


def cleanup_files(tmp_dir: Path, file_id: str) -> None:
    """Remove temporary files belonging to an upload."""
    for path in tmp_dir.glob(f"{file_id}.*"):
        try:
            path.unlink()
        except OSError:
            logger.exception("Failed to remove temporary file %s", path)


class ConversionError(Exception):
    """Exception used for conversion errors."""

    def __init__(self, stderr: str) -> None:
        """Initialize the exception with a message."""
        super().__init__(f"Conversion failed: {stderr}")
