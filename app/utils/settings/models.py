"""Immutable validated runtime and logging settings models."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal, override

from pydantic import BaseModel, ConfigDict, Field
from pydantic import ValidationError as PydanticValidationError
from pydantic_settings import (
    BaseSettings,
    JsonConfigSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from app.utils.errors.exceptions import ConfigurationError

LogLevel = Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]
LogRender = Literal["json", "human"]
LogCompression = Literal["zip", "none"]
Environment = Literal["dev", "test", "staging", "production"]
RuntimeProfile = Literal["research", "simulation", "paper", "live"]
_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


class _CentralJsonSettingsSource(JsonConfigSettingsSource):
    """Central JSON source matching aliases, uppercase, and exact field names.

    The stock JSON source matches file keys to field names case-sensitively,
    while the repository central settings file uses uppercase environment-style
    keys. This source reproduces the previous dotenv name-matching behavior so
    every ``AppSettings`` subclass loads identically from the JSON file.
    """

    @override
    def __call__(self) -> dict[str, Any]:
        """Return field values loaded from the central JSON settings file.

        Returns:
            Mapping of field aliases or names to raw JSON values; empty when the
            configured file is missing or its root is not an object.
        """
        json_file = self.settings_cls.model_config.get("json_file")
        if json_file is None or not Path(str(json_file)).is_file():
            return {}
        raw: object = json.loads(Path(str(json_file)).read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return {}
        values: dict[str, Any] = {}
        for field_name, field in self.settings_cls.model_fields.items():
            alias = (
                field.validation_alias
                if isinstance(field.validation_alias, str)
                else None
            )
            candidates = ([alias] if alias else []) + [field_name.upper(), field_name]
            for key in candidates:
                if key in raw:
                    values[alias or field_name] = raw[key]
                    break
        return values


class AppSettings(BaseSettings):
    """Immutable base for typed settings loaded from the central environment."""

    model_config = SettingsConfigDict(
        json_file=_REPOSITORY_ROOT / "app" / "configs" / "env.json",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        case_sensitive=False,
        extra="ignore",
        frozen=True,
    )

    @override
    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Add the centralized JSON settings file after process overrides.

        Args:
            settings_cls: The settings class being constructed.
            init_settings: Explicit constructor values source.
            env_settings: Process environment source.
            dotenv_settings: Dotenv file source (unused; no env_file configured).
            file_secret_settings: File secrets source.

        Returns:
            Settings sources in precedence order.
        """
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            _CentralJsonSettingsSource(settings_cls),
            file_secret_settings,
        )


class _ConfigurationModel(BaseModel):
    """Base model that maps Pydantic failures to shared configuration errors."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    def __init__(self, **data: object) -> None:
        """Initialize the configuration model, mapping Pydantic validation errors.

        Args:
            data: Arbitrary keyword settings arguments.

        Raises:
            ConfigurationError: If any of the values violate field
                validation constraints.
        """
        try:
            super().__init__(**data)
        except PydanticValidationError:
            raise ConfigurationError("CONFIGURATION_INVALID") from None


class LoggingSettings(_ConfigurationModel):
    """Immutable bounded structured-logging settings.

    Attributes:
        level: Log severity filter level.
        render: Log output style format, human or json.
        file_path: Optional path to write a single log file to.
        log_directory: Optional directory path to write structured logs.
        max_bytes: Size in bytes at which log files roll over.
        backup_count: Maximum count of rotated log files to retain.
        retention_days: Number of days to keep rotated logs before deletion.
        compression: Mode of compression to apply to rotated logs.
        enqueue: If True, writes logs asynchronously via a background queue.
        colorize: If True, adds color escape sequences to terminal logs.
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
    """Immutable generic runtime settings.

    Attributes:
        environment: Standard environment classification name.
        runtime_profile: Standard runtime profile categorization name.
        logging: Configured sub-settings representing logging configuration.
    """

    environment: Environment = "dev"
    runtime_profile: RuntimeProfile = "research"
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
