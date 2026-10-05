FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY kepubify/ ./kepubify/

ARG KEPUBIFY_VERSION=v4.0.4
ARG KEPUBIFY_SHA256=37d7628d26c5c906f607f24b36f781f306075e7073a6fe7820a751bb60431fc5
RUN apt-get update \
    && apt-get install --no-install-recommends --yes ca-certificates curl \
    && curl --fail --location --silent --show-error \
        "https://github.com/pgaskin/kepubify/releases/download/${KEPUBIFY_VERSION}/kepubify-linux-64bit" \
        --output /usr/local/bin/kepubify \
    && echo "${KEPUBIFY_SHA256}  /usr/local/bin/kepubify" | sha256sum --check --status \
    && chmod 0755 /usr/local/bin/kepubify \
    && apt-get purge --auto-remove --yes curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system app \
    && useradd --system --gid app --home-dir /app app \
    && mkdir -p /app/instance/tmp /app/logs \
    && chown -R app:app /app/instance /app/logs

ENV PATH="/app/.venv/bin:${PATH}" \
    DEBUG=false \
    LOG_DIR=/app/logs \
    INSTANCE_PATH=/app/instance \
    KEPUBIFY_PATH=/usr/local/bin/kepubify \
    TMP_DIR=/app/instance/tmp \
    TEMP_FILE_RETENTION_SECONDS=86400

USER app

EXPOSE 8082

CMD ["uvicorn", "kepubify.main:app", "--host", "0.0.0.0", "--port", "8082"]
