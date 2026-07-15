"""Immutable validated runtime and logging settings models."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic import ValidationError as PydanticValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.utils.errors.exceptions import ConfigurationError

LogLevel = Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]
LogRender = Literal["json", "human"]
LogCompression = Literal["zip", "none"]
Environment = Literal["dev", "test", "staging", "production"]
RuntimeProfile = Literal["research", "simulation", "paper", "live"]
_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


class AppSettings(BaseSettings):
    """Immutable base for typed settings loaded from the central environment."""

    model_config = SettingsConfigDict(
        env_file=_REPOSITORY_ROOT / ".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        case_sensitive=False,
        extra="ignore",
        frozen=True,
    )


class _ConfigurationModel(BaseModel):
    """Base model that maps Pydantic failures to shared configuration errors."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    def __init__(self, **data: object) -> None:
        try:
            super().__init__(**data)
        except PydanticValidationError:
            raise ConfigurationError("CONFIGURATION_INVALID") from None


class LoggingSettings(_ConfigurationModel):
    """Immutable bounded structured-logging settings."""

    level: LogLevel = "DEBUG"
    render: LogRender = "human"
    file_path: Path | None = None
    log_directory: Path | None = Path("data/logs")
    max_bytes: int = Field(default=10_000_000, ge=1_024, le=100_000_000)
    backup_count: int = Field(default=10, ge=1, le=20)
    retention_days: int = Field(default=10, ge=1, le=365)
    compression: LogCompression = "zip"
    enqueue: bool = True
    colorize: bool = True


class RuntimeSettings(_ConfigurationModel):
    """Immutable generic runtime settings."""

    environment: Environment = "dev"
    runtime_profile: RuntimeProfile = "research"
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
