# kalufs-kepubify

Small FastAPI application for converting epub into kepub.

## Requirements

* [Python 3.12](http://python.org/) or newer
* [uv](https://github.com/astral-sh/uv)
* [kepubify](https://pgaskin.net/kepubify/)

Local, non-Docker runs require a Linux x86-64 kepubify binary; see the setup steps below. Docker downloads kepubify
v4.0.4 for Linux x86-64 and verifies its pinned SHA-256 checksum, so no local binary is needed for a Docker build. The
Compose image targets `linux/amd64` (64-bit x86). It runs natively on x86-64 hosts; ARM hosts need Docker's AMD64
emulation support.

## Setup

1. For non-Docker runs, download the [kepubify binary](https://pgaskin.net/kepubify/) and place it at
   `instance/kepubify-linux-64bit`. Make sure it is executable (e.g. `chmod +x instance/kepubify-linux-64bit`).
2. Install the dependencies with `uv sync`.
3. For development, run `uv run run.py`. This launcher enables debug logging and automatic reload; do not use it for
   deployment.
4. For a deployment without the development launcher, run Uvicorn directly:
   `uv run uvicorn kepubify.main:app --host 0.0.0.0 --port 8082`.

## Settings

Settings are loaded from environment variables and the project-root `.env` file, with environment variables taking
priority. Available values include `DEBUG`, `LOG_DIR`, `APPLICATION_ROOT`, `INSTANCE_PATH`, `KEPUBIFY_PATH`, `TMP_DIR`,
and `MAX_UPLOAD_SIZE_BYTES`.

The upload limit defaults to 10 MB (`10485760` bytes). Set `MAX_UPLOAD_SIZE_BYTES` to change it; values must be
positive. The server rejects larger files with HTTP 413, and the upload page checks the selected file before submitting.

Converted files are removed after download, and failed uploads are cleaned up immediately. At startup, temporary files
older than `temp_file_retention_seconds` are removed. The default retention period is 24 hours.

## Docker

Build and start the container with:

```sh
docker compose up --build
```

The Docker build downloads kepubify v4.0.4 directly from its GitHub release and verifies the pinned SHA-256 checksum;
the local binary is not required for Docker builds.

Open `http://localhost:8082`. Compose stores temporary files and application logs in named volumes. Override `PORT`,
`DEBUG`, `APPLICATION_ROOT`, `MAX_UPLOAD_SIZE_BYTES`, or `TEMP_FILE_RETENTION_SECONDS` in a project-root `.env` file.
Stop the container with `docker compose down`; named volumes are retained unless removed explicitly.

## Deploying

For a Linux server:

1. Install Docker Engine with the Compose plugin, clone this repository, and make sure the server can reach GitHub to
   download the pinned converter during the image build.
2. Optionally create a project-root `.env` file. Keep `DEBUG=false`; set `PORT` if the local reverse-proxy upstream
   should use a port other than `8082`.
3. Start the service with `docker compose up --build --detach`. Follow startup with `docker compose logs --follow app`.
4. Configure DNS and a host-installed TLS reverse proxy such as Caddy or Nginx to forward requests to
   `http://127.0.0.1:8082` (or the configured `PORT`). The Compose port is loopback-only by default, so it is not
   directly exposed to the network.

The upload endpoint is unauthenticated. Before exposing it publicly, configure rate limiting at the reverse proxy and
allow at least the configured upload limit plus multipart overhead. To deploy an update, pull the new code and run
`docker compose up --build --detach`. `docker compose down` stops the service while retaining its named volumes; `docker
compose down --volumes` also deletes temporary files and logs.
