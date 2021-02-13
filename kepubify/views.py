"""
Small application for uploading files to a server.

Inspired by: http://flask.pocoo.org/docs/0.11/patterns/fileuploads/
"""

import logging
import random
import re
import shlex
import string
import subprocess
import traceback
from pathlib import Path

from flask import Blueprint, current_app, jsonify, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename

general = Blueprint("general", __name__)
log = logging.getLogger("validatems" + __name__)


@general.route("/", methods=["GET"])
def index():
    """Render index.html."""
    return render_template("index.html")


@general.route("/upload", methods=["POST"])
def upload():
    """Upload epub file, convert it and return download URL."""
    try:
        upload_file = request.files["file"]

        if not upload_file:
            # User did not select a file
            log.warning("No file uploaded!")
            return jsonify({"status": "fail", "message": "No file uploaded!"})
        else:
            filepath, filename = create_filepath(secure_filename(upload_file.filename))
            save_as = Path(current_app.instance_path) / filepath / filename
            upload_file.save(str(save_as))
            try:
                new_filename = convert(save_as)
            except Exception as err:
                current_app.logger.error(traceback.format_exc())
                return jsonify({"status": "fail", "message": str(err)})
            download_url = url_for("general.download", filename=new_filename, path=filepath)
            return jsonify({"status": "success", "filename": new_filename, "download": download_url})

    # Unexpected error
    except Exception as e:
        log.exception("Unexpected error: %s" % e)
        return jsonify({"status": "fail", "message": "unexpected error"})


@general.route("/download")
def download():
    """Download file."""
    filename = request.args.get("filename")
    random_path = request.args.get("path")
    path = Path(current_app.instance_path) / Path(random_path) / Path(filename)
    return send_file(str(path), mimetype="application/epub+zip", as_attachment=True)


def convert(in_filepath):
    """Convert in_file to kepub and return new file name."""
    new_filename = in_filepath.stem + ".kepub" + ".epub"
    new_filepath = str(in_filepath.parent / Path(new_filename))
    p = subprocess.run([current_app.config.get("KEPUBIFY_PATH"), str(in_filepath), "-o", new_filepath],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        stderr = p.stderr.decode() or ""
        current_app.logger.error(stderr)
        stderr = re.sub(str(in_filepath), in_filepath.name, stderr)
        raise Exception(f"Conversion failed: {stderr}")

    return new_filename


def create_filepath(in_filename):
    """Create random filepath."""
    random_str_len = 10
    random_dir = Path("".join(random.choices(string.ascii_lowercase + string.digits, k=random_str_len)))
    (Path(current_app.instance_path) / random_dir).mkdir()
    filename = Path(shlex.quote(in_filename))
    return random_dir, filename
