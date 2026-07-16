"""Define immutable generic runtime and structured-logging settings.

This module owns the repository's centralized ``BaseSettings`` boundary but
does not select domain policy or validate execution-route compatibility.
"""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic import ValidationError as PydanticValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.utils.errors.exceptions import ConfigurationError

type LogLevel = Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]
type LogRender = Literal["json", "human"]
type LogCompression = Literal["zip", "none"]
type Environment = Literal["dev", "test", "staging", "production"]
type RuntimeProfile = Literal["research", "simulation", "paper", "live"]

_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


class AppSettings(BaseSettings):
    """Provide the frozen repository ``.env`` and process-settings boundary.

    Subclasses inherit case-insensitive environment lookup, UTF-8 ``.env``
    loading from the repository root, rejection of extra values, and immutable
    model instances.
    """

    model_config = SettingsConfigDict(
        env_file=_REPOSITORY_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
        frozen=True,
    )


class _ConfigurationModel(BaseModel):
    """Map Pydantic model failures to boundary-safe configuration errors."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    def __init__(self, **data: object) -> None:
        """Validate and freeze a generic configuration model.

        Args:
            **data: Explicit field values accepted by the concrete model.

        Raises:
            ConfigurationError: Any supplied field is missing, extra, or
                outside its declared type or bounds.
        """
        try:
            super().__init__(**data)
        except PydanticValidationError:
            raise ConfigurationError("CONFIGURATION_INVALID") from None


class LoggingSettings(_ConfigurationModel):
    """Represent immutable bounded structured-logging settings.

    Attributes:
        level: Minimum standard log level accepted by configured handlers.
        render: Structured ``json`` or source-aware ``human`` rendering.
        file_path: Optional standalone rotating application-log path.
        log_directory: Optional directory for the four specialized log files.
        max_bytes: Per-file size threshold that triggers rotation.
        backup_count: Maximum numbered rotations retained per active file.
        retention_days: Maximum rotation age removed during rollover.
        compression: ``zip`` compression or uncompressed rotation.
        enqueue: Whether records use one in-process queue listener.
        colorize: Whether human console level and message text use ANSI color.
    """

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
    """Represent immutable business-neutral runtime settings.

    Attributes:
        environment: Deployment environment label.
        runtime_profile: Requested research or execution profile.
        logging: Nested immutable structured-logging configuration.
    """

    environment: Environment = "dev"
    runtime_profile: RuntimeProfile = "research"
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
