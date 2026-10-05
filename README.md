# kalufs-kepubify

Small FastAPI application for converting epub into kepub.

## Requirements

* [Python 3.12](http://python.org/) or newer
* [uv](https://github.com/astral-sh/uv)
* [kepubify](https://pgaskin.net/kepubify/)

## Setup

1. Download the [kepubify binary](https://pgaskin.net/kepubify/) and place it at
   `instance/kepubify-linux-64bit`. Make sure it is executable (e.g. `chmod +x instance/kepubify-linux-64bit`).
2. Install the dependencies with `uv sync`.
3. For development, run `uv run run.py`. This launcher enables debug logging and automatic reload; do not use it for
   deployment.
4. For a deployment without the development launcher, run Uvicorn directly:
   `uv run uvicorn kepubify.main:app --host 0.0.0.0 --port 8082`.

## Settings

Settings are loaded from environment variables and the project-root `.env` file, with environment variables taking
priority. Available values include `DEBUG`, `LOG_DIR`, `APPLICATION_ROOT`, `INSTANCE_PATH`, `KEPUBIFY_PATH`, and
`TMP_DIR`.

Converted files are removed after download, and failed uploads are cleaned up immediately. At startup, temporary files
older than `temp_file_retention_seconds` are removed. The default retention period is 24 hours.
