"""Initialise Flask application."""

import logging
import os
import sys
import time
from pathlib import Path

import flask_reverse_proxy
from flask import Flask, request

log = logging.getLogger("kepubify" + __name__)



def create_app():
    """Instanciate app."""
    app = Flask(__name__)

    # Set default config
    app.config.from_object("config")

    # Overwrite with instance config
    if os.path.exists(os.path.join(app.instance_path, "config.py")):
        app.config.from_pyfile(os.path.join(app.instance_path, "config.py"))

    app.secret_key = app.config["SECRET_KEY"]

    # Configure logger
    logfmt = "%(asctime)-15s - %(levelname)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    if app.config.get("DEBUG"):
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
                            format=logfmt, datefmt=datefmt)
    else:
        today = time.strftime("%Y-%m-%d")
        logdir = app.config.get("LOG_DIR")
        logfile = os.path.join(logdir, f"{today}.log")
        # Create log dir if it does not exist
        if not os.path.exists(logdir):
            os.makedirs(logdir)
        logging.basicConfig(filename=logfile, level=logging.INFO,
                            format=logfmt, datefmt=datefmt)

    # Create instance_folder if it does not exist
    if not os.path.exists(app.instance_path):
        os.makedirs(app.instance_path)

    log.info("Application restarted")

    # Fix proxy chaos
    app.wsgi_app = flask_reverse_proxy.ReverseProxied(app.wsgi_app)
    app.wsgi_app = FixScriptName(app.wsgi_app, app.config)

    from . import views
    app.register_blueprint(views.general)

    # Cleanup uploaded files
    @app.after_request
    def cleanup(response):
        tmp_dir = Path(app.instance_path) / Path(app.config.get("TMP_DIR"))
        # Cleanup on error
        if response.json:
            if response.json.get("status") == "fail" and response.json.get("id"):
                for child in tmp_dir.iterdir():
                    if str(child.name).startswith(response.json.get("id")):
                        try:
                            child.unlink()
                        except Exception as e:
                            log.error('Failed to remove %s. Reason: %s' % (child, e))
        # Cleanup after download
        if str(request.url_rule) == "/download":
            for child in tmp_dir.iterdir():
                if str(child.name).startswith(request.args.get("id")):
                    try:
                        child.unlink()
                    except Exception as e:
                        log.error('Failed to remove %s. Reason: %s' % (child, e))
        return response
    return app


class FixScriptName(object):
    """Set the environment SCRIPT_NAME."""
    def __init__(self, app, config):
        self.app = app
        self.config = config

    def __call__(self, environ, start_response):
        script_name = self.config["APPLICATION_ROOT"]
        if script_name:
            environ["SCRIPT_NAME"] = script_name

        return self.app(environ, start_response)
