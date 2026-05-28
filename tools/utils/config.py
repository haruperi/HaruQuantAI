"""Configuration loading helpers for HaruQuantAI.

Loads validated HaruQuant environment settings without exposing secrets.

This module is a utility configuration helper, not an official AI tool file.
It reads non-secret runtime settings from environment variables and an optional
dotenv file. Environment variables always take precedence over dotenv values.

Supported dotenv syntax is intentionally simple:
    - KEY=VALUE
    - export KEY=VALUE
    - blank lines and full-line comments are ignored
    - single or double quotes around values are stripped

Exported AI Tools:
    None.

Public Helpers:
    - get_settings: Load validated runtime settings.
    - get_environment: Return the configured environment name.
    - is_production: Return whether the environment is production.
    - is_test: Return whether the environment is test.

Internal Helpers:
    - _normalize_env_file
    - _parse_dotenv_line
    - _read_dotenv
    - _setting

Classes:
    - Settings
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from tools.utils.errors import ConfigurationError
from tools.utils.logger import logger

DEFAULT_ENV_FILE: Final[str] = ".env"
DEFAULT_ENVIRONMENT: Final[str] = "local"
DEFAULT_APP_NAME: Final[str] = "haruquantai"
DEFAULT_LOG_LEVEL: Final[str] = "INFO"

VALID_ENVIRONMENTS: Final[frozenset[str]] = frozenset(
    {
        "local",
        "development",
        "test",
        "staging",
        "production",
    }
)

VALID_LOG_LEVELS: Final[frozenset[str]] = frozenset(
    {
        "TRACE",
        "DEBUG",
        "INFO",
        "SUCCESS",
        "WARNING",
        "ERROR",
        "CRITICAL",
    }
)


@dataclass(frozen=True)
class Settings:
    """
    Runtime settings for the HaruQuant application.

    Settings intentionally exclude secrets. Add secret handling through a
    dedicated secrets/config provider when needed.

    Args:
        environment (str): Runtime environment name.
        app_name (str): Human-readable application name.
        log_level (str): Logging level name.

    Raises:
        ConfigurationError: If any setting is invalid.
    """

    environment: str = DEFAULT_ENVIRONMENT
    app_name: str = DEFAULT_APP_NAME
    log_level: str = DEFAULT_LOG_LEVEL

    def __post_init__(self) -> None:
        """
        Normalize and validate settings after dataclass construction.

        Raises:
            ConfigurationError: If environment, app_name, or log_level is invalid.
        """
        environment = _require_non_empty_string(
            self.environment,
            "HARUQUANT_ENV",
        ).lower()
        app_name = _require_non_empty_string(
            self.app_name,
            "HARUQUANT_APP_NAME",
        )
        log_level = _require_non_empty_string(
            self.log_level,
            "HARUQUANT_LOG_LEVEL",
        ).upper()

        if environment not in VALID_ENVIRONMENTS:
            expected = ", ".join(sorted(VALID_ENVIRONMENTS))
            raise ConfigurationError(
                f"Invalid HARUQUANT_ENV '{self.environment}'. "
                f"Expected one of: {expected}."
            )

        if log_level not in VALID_LOG_LEVELS:
            expected = ", ".join(sorted(VALID_LOG_LEVELS))
            raise ConfigurationError(
                f"Invalid HARUQUANT_LOG_LEVEL '{self.log_level}'. "
                f"Expected one of: {expected}."
            )

        object.__setattr__(self, "environment", environment)
        object.__setattr__(self, "app_name", app_name)
        object.__setattr__(self, "log_level", log_level)


def _require_non_empty_string(value: object, field_name: str) -> str:
    """
    Validate and normalize a required string setting.

    Args:
        value (object): Candidate string value.
        field_name (str): Human-readable field name used in error messages.

    Returns:
        str: Trimmed non-empty string.

    Raises:
        ConfigurationError: If the value is not a string or is empty.
    """
    if not isinstance(value, str):
        raise ConfigurationError(f"{field_name} must be a string.")

    normalized = value.strip()
    if not normalized:
        raise ConfigurationError(f"{field_name} cannot be empty.")

    return normalized


def _normalize_env_file(env_file: str | Path) -> Path:
    """
    Normalize and validate a dotenv file path.

    Missing dotenv files are allowed and handled by ``_read_dotenv``. Existing
    directories are rejected because they cannot be read as dotenv files.

    Args:
        env_file (str | Path): Dotenv file path.

    Returns:
        Path: Normalized dotenv path.

    Raises:
        ConfigurationError: If the input type is invalid or points to a directory.
    """
    if not isinstance(env_file, (str, Path)):
        raise ConfigurationError("env_file must be a string or pathlib.Path.")

    path = Path(env_file).expanduser()
    if path.exists() and path.is_dir():
        raise ConfigurationError(f"env_file points to a directory: {path}")

    return path


def _parse_dotenv_line(line: str) -> tuple[str, str] | None:
    """
    Parse a single dotenv line.

    Args:
        line (str): Raw dotenv line.

    Returns:
        tuple[str, str] | None: Parsed key/value pair or ``None`` when the line
        is empty, a comment, or malformed.
    """
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None

    if stripped.startswith("export "):
        stripped = stripped[len("export ") :].strip()

    if "=" not in stripped:
        return None

    key, value = stripped.split("=", 1)
    key = key.strip()
    if not key:
        return None

    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]

    return key, value


def _read_dotenv(path: Path) -> dict[str, str]:
    """
    Read simple key-value pairs from a dotenv file.

    Missing files return an empty mapping. Existing but unreadable files raise
    ``ConfigurationError`` with a clear message.

    Args:
        path (Path): Dotenv path to read.

    Returns:
        dict[str, str]: Parsed settings.
    """
    if not path.exists():
        return {}

    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as error:
        logger.exception("Failed to read dotenv file | path=%s", path)
        raise ConfigurationError(
            f"Failed to read dotenv file '{path}': {error}"
        ) from error

    values: dict[str, str] = {}
    for raw_line in raw_text.splitlines():
        parsed = _parse_dotenv_line(raw_line)
        if parsed is None:
            continue

        key, value = parsed
        values[key] = value

    return values


def _setting(name: str, dotenv_values: dict[str, str], default: str) -> str:
    """
    Resolve a setting from environment variables, dotenv values, or a default.

    Args:
        name (str): Environment variable name.
        dotenv_values (dict[str, str]): Values parsed from the dotenv file.
        default (str): Default value when no configured value exists.

    Returns:
        str: Resolved setting value.
    """
    return os.getenv(name) or dotenv_values.get(name) or default


def get_settings(env_file: str | Path = DEFAULT_ENV_FILE) -> Settings:
    """
    Load HaruQuant settings from environment variables or a dotenv file.

    Environment variables take precedence over dotenv values. Secret values are
    intentionally not represented in this settings object.

    Args:
        env_file (str | Path, optional): Dotenv file path. Defaults to ``.env``.

    Returns:
        Settings: Validated application settings.

    Raises:
        ConfigurationError: If the dotenv path cannot be read or any setting is
            invalid.
    """
    path = _normalize_env_file(env_file)
    dotenv_values = _read_dotenv(path)
    settings = Settings(
        environment=_setting("HARUQUANT_ENV", dotenv_values, DEFAULT_ENVIRONMENT),
        app_name=_setting("HARUQUANT_APP_NAME", dotenv_values, DEFAULT_APP_NAME),
        log_level=_setting("HARUQUANT_LOG_LEVEL", dotenv_values, DEFAULT_LOG_LEVEL),
    )

    logger.info(
        "Settings loaded | environment=%s | app_name=%s | log_level=%s",
        settings.environment,
        settings.app_name,
        settings.log_level,
    )
    return settings


def get_environment(env_file: str | Path = DEFAULT_ENV_FILE) -> str:
    """
    Return the configured HaruQuant environment name.

    Args:
        env_file (str | Path, optional): Dotenv file path. Defaults to ``.env``.

    Returns:
        str: Validated environment name.

    Raises:
        ConfigurationError: If settings cannot be loaded.
    """
    return get_settings(env_file=env_file).environment


def is_production(env_file: str | Path = DEFAULT_ENV_FILE) -> bool:
    """
    Return whether HaruQuant is configured for production.

    Args:
        env_file (str | Path, optional): Dotenv file path. Defaults to ``.env``.

    Returns:
        bool: ``True`` when environment is ``production``.

    Raises:
        ConfigurationError: If settings cannot be loaded.
    """
    return get_environment(env_file=env_file) == "production"


def is_test(env_file: str | Path = DEFAULT_ENV_FILE) -> bool:
    """
    Return whether HaruQuant is configured for tests.

    Args:
        env_file (str | Path, optional): Dotenv file path. Defaults to ``.env``.

    Returns:
        bool: ``True`` when environment is ``test``.

    Raises:
        ConfigurationError: If settings cannot be loaded.
    """
    return get_environment(env_file=env_file) == "test"


__all__ = [
    "DEFAULT_APP_NAME",
    "DEFAULT_ENV_FILE",
    "DEFAULT_ENVIRONMENT",
    "DEFAULT_LOG_LEVEL",
    "Settings",
    "VALID_ENVIRONMENTS",
    "VALID_LOG_LEVELS",
    "get_environment",
    "get_settings",
    "is_production",
    "is_test",
]
