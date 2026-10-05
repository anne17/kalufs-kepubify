"""FastAPI application factory."""

import logging
import time
import tomllib
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from kepubify.config import settings
from kepubify.views import router

logger = logging.getLogger(__name__)


def get_app_version_from_pyproject() -> str:
    """Get the version of the project from the pyproject.toml file.

    Args:
        path: Path to the pyproject.toml file.
    """
    pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
    if not pyproject_path.exists() or not pyproject_path.is_file():
        logger.error("Could not find pyproject.toml file at %s", pyproject_path)
        raise FileNotFoundError(f"Could not find pyproject.toml file at {pyproject_path}")
    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)
    return data["project"]["version"]


def preflight() -> None:
    """Perform preflight setup before starting the application."""
    # Set logging configuration based on debug mode
    log_format = "%(asctime)s - %(levelname)s: %(message)s"
    if settings.debug:
        logging.basicConfig(level=logging.DEBUG, format=log_format)
    else:
        settings.log_dir.mkdir(parents=True, exist_ok=True)
        logfile = settings.log_dir / f"{time.strftime('%Y-%m-%d')}.log"
        logging.basicConfig(filename=logfile, level=logging.INFO, format=log_format)

    logger.info("Starting kalufs-kepubify")
    logger.debug("Debug: %s", settings.debug)

    # Create instance and tmp path if it doesn't exist
    settings.instance_path.mkdir(parents=True, exist_ok=True)
    settings.tmp_dir.mkdir(parents=True, exist_ok=True)
    cleanup_stale_files(settings.tmp_dir)


def cleanup_stale_files(tmp_dir: Path) -> None:
    """Remove temporary files older than the retention period."""
    cutoff = time.time() - settings.temp_file_retention_seconds
    for path in tmp_dir.iterdir():
        try:
            if path.is_file() and path.stat().st_mtime < cutoff:
                path.unlink()
                logger.info("Removed stale temporary file %s", path)
        except FileNotFoundError:
            continue
        except OSError:
            logger.exception("Failed to remove stale temporary file %s", path)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator:
    """Lifespan context manager for the FastAPI app.

    Args:
        app (FastAPI): The FastAPI application instance.

    Yields:
        None: Indicates the lifespan context.
    """
    try:
        yield
    except Exception:
        logger.exception("Unhandled exception during application lifespan")
        raise
    finally:
        logger.info("Application shutdown complete; temporary files are retained for stale cleanup")


preflight()

# Deactivate default Redoc, Swagger UI and openapi_url because we use custom routes
app = FastAPI(
    title="kalufs-kepubify",
    debug=settings.debug,
    lifespan=lifespan,
    version=get_app_version_from_pyproject(),
    root_path=settings.application_root,
    redoc_url=None,
    docs_url=None,
    openapi_url=None,
)


# ------------------------------------------------------------------------------
# Mount static files and include routes
# ------------------------------------------------------------------------------
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
app.include_router(router)
