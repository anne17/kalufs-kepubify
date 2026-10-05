"""Run the FastAPI development server."""

import argparse
import logging.config
from pathlib import Path

import uvicorn

from kepubify.config import settings

settings.debug = True

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(name)s - %(message)s",
            "use_colors": None,
        },
    },
    "handlers": {
        "default": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "root": {"handlers": ["default"], "level": "DEBUG"},
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the FastAPI app with Uvicorn.")
    parser.add_argument("--host", "-H", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
    parser.add_argument("--port", "-p", type=int, default=8082, help="Port to bind to (default: 8082)")
    args = parser.parse_args()

    logging.config.dictConfig(LOGGING_CONFIG)
    logging.getLogger("kepubify").info("Starting kepubify in development mode")

    # Suppress some chatty logs
    logging.getLogger("watchfiles.main").setLevel("WARNING")

    uvicorn.run(
        "kepubify.main:app",
        host=args.host,
        port=args.port,
        reload=True,
        reload_excludes=[
            str(Path(settings.instance_path).resolve()),
            "run.py",
            "**/__pycache__/*",
            "kepubify/__pycache__",
            "**/*.pyc",
            "**/*.pyo",
        ],
        log_config=None,  # Prevents uvicorn from overriding the above logging config
    )
