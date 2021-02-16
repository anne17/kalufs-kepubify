"""
Small application for uploading files to a server.

Inspired by: http://flask.pocoo.org/docs/0.11/patterns/fileuploads/
"""

import logging
import random
import re
import string
import subprocess
import traceback
from pathlib import Path

from flask import Blueprint, current_app, jsonify, render_template, request, send_from_directory, url_for

general = Blueprint("general", __name__)
log = logging.getLogger("validatems" + __name__)


@general.route("/", methods=["GET"])
def index():
    """Render index.html."""
    return render_template("index.html")


@general.route("/upload", methods=["POST"])
def upload():
    """Upload epub file, convert it and return download URL."""
    file_id = ""
    try:
        upload_file = request.files["file"]

        if not upload_file:
            # User did not select a file
            log.warning("No file uploaded!")
            return jsonify({"status": "fail", "message": "No file uploaded!"})
        else:
            if upload_file.filename.endswith(".kepub.epub"):
                return jsonify({"status": "fail", "message": 'Wrong file extension: ".kepub.epub". '
                                'Looks like you tried to upload a kepub file!'})

            random_filename = create_filename(upload_file.filename)
            file_id = random_filename[:-5]
            new_name = Path(upload_file.filename).stem + ".kepub.epub"
            tmp_dir = Path(current_app.instance_path) / Path(current_app.config.get("TMP_DIR"))
            tmp_dir.mkdir(exist_ok=True)
            save_as = tmp_dir / Path(random_filename)
            upload_file.save(str(save_as))
            try:
                new_filename = convert(save_as)
            except Exception as err:
                current_app.logger.error(traceback.format_exc())
                return jsonify({"status": "fail", "message": str(err), "id": file_id})
            download_url = url_for("general.download", file=new_filename, name=new_name, id=file_id)
            return jsonify({"status": "success", "filename": new_name, "download": download_url})

    # Unexpected error
    except Exception as e:
        log.exception("Unexpected error: %s" % e)
        return jsonify({"status": "fail", "message": "unexpected error", "id": file_id})


@general.route("/download")
def download():
    """Download file."""
    filename = request.args.get("file")
    new_name = request.args.get("name")
    tmp_dir = Path(current_app.instance_path) / Path(current_app.config.get("TMP_DIR"))
    return send_from_directory(str(tmp_dir), filename, attachment_filename=new_name, as_attachment=True)


def convert(in_filepath):
    """Convert in_file to kepub and return new file name."""
    new_filename = in_filepath.stem + ".kepub.epub"
    new_filepath = str(in_filepath.parent / Path(new_filename))
    p = subprocess.run([current_app.config.get("KEPUBIFY_PATH"), str(in_filepath), "-o", new_filepath],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        stderr = p.stderr.decode() or ""
        current_app.logger.error(stderr)
        stderr = re.sub(str(in_filepath), in_filepath.name, stderr)
        raise Exception(f"Conversion failed: {stderr}")

    return new_filename


def create_filename(in_filename):
    """Create random filepath."""
    random_str_len = 10
    random_name = "".join(random.choices(string.ascii_lowercase + string.digits, k=random_str_len))
    return random_name + ".epub"
