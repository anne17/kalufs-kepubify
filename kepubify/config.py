"""Pydantic settings for the application."""

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and dotenv files."""

    debug: bool = False  # Set log level to debug
    log_dir: Path = PROJECT_ROOT / "logs"
    application_root: str = ""  # Needed if application is not mounted in root

    instance_path: Path = PROJECT_ROOT / "instance"  # Path to the instance dir
    kepubify_path: Path = PROJECT_ROOT / "instance" / "kepubify-linux-64bit"  # kepubify binary
    tmp_dir: Path = PROJECT_ROOT / "instance" / "tmp"  # Dir for temporary file storage

    temp_file_retention_seconds: int = 24 * 60 * 60  # Retention period for temporary files in seconds

    @field_validator("application_root")
    @classmethod
    def normalize_application_root(cls, value: str) -> str:
        """Normalize the optional application_root path."""
        return f"/{value.strip('/')}" if value.strip("/") else ""

    model_config = SettingsConfigDict(
        case_sensitive=False,
        env_file=".env",  # Load variables from a .env file if it exists
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra environment variables from other modules (e.g. SPARV_*)
    )


settings = Settings()
