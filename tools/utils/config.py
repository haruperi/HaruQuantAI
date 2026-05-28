"""Runtime configuration loader for HaruQuant.

Provides the canonical HaruQuant runtime configuration loader.

This module merges the earlier lightweight ``config.py`` behavior with the
richer ``settings.py`` runtime-settings model. It supports:

- non-secret application settings;
- environment-variable and dotenv loading;
- prefixed runtime settings for tools and agentic workflows;
- mapping-based validation for tests and deterministic workflows;
- optional injection into a mutable runtime container.

This file contains official AI-callable tools only when exported from
``tools/utils/__init__.py``. The small convenience helpers remain normal
production utilities.

Exported AI Tools:
    - load_runtime_settings
    - load_runtime_settings_from_mapping
    - inject_runtime_settings

Public Utility Helpers:
    - get_settings
    - get_environment
    - is_production
    - is_test
    - parse_env_file
    - collect_prefixed_values
    - normalize_mapping

Internal Helpers:
    - _metadata
    - _success_response
    - _error_response
    - _normalize_env_file
    - _parse_dotenv_line
    - _setting
    - _load_runtime_settings
    - _load_runtime_settings_from_mapping
    - _inject_runtime_settings

Classes:
    - SettingsError
    - Settings
    - RuntimeSettings
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Final, Mapping, MutableMapping

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from tools.utils.errors import ConfigurationError
from tools.utils.logger import logger

TOOL_VERSION: Final[str] = "1.0.0"
TOOL_CATEGORY: Final[str] = "utils"
TOOL_RISK_LEVEL: Final[str] = "low"
READ_ONLY: Final[bool] = True
WRITES_FILE: Final[bool] = False
MODIFIES_DATABASE: Final[bool] = False
PLACES_TRADE: Final[bool] = False
REQUIRES_NETWORK: Final[bool] = False

DEFAULT_ENV_FILE: Final[str] = ".env"
DEFAULT_ENVIRONMENT: Final[str] = "local"
DEFAULT_RUNTIME_ENVIRONMENT: Final[str] = "development"
DEFAULT_APP_NAME: Final[str] = "haruquantai"
DEFAULT_LOG_LEVEL: Final[str] = "INFO"
DEFAULT_ENV_DIR: Final[Path] = Path("agentic/config/environments")
DEFAULT_ENV_PREFIX: Final[str] = "HQT_"

VALID_ENVIRONMENTS: Final[frozenset[str]] = frozenset(
    {
        "local",
        "development",
        "dev",
        "test",
        "staging",
        "production",
        "prod",
        "paper",
        "live",
    }
)

ENVIRONMENT_ALIASES: Final[dict[str, str]] = {
    "dev": "development",
    "prod": "production",
}

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


class SettingsError(ValueError):
    """Raised when runtime settings cannot be loaded or validated."""


class Settings(BaseModel):
    """
    Lightweight non-secret HaruQuant application settings.

    This model preserves the earlier ``config.py`` behavior while using the
    same validation style as RuntimeSettings.

    Args:
        environment (str): Runtime environment name.
        app_name (str): Human-readable application name.
        log_level (str): Logging level name.
    """

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    environment: str = DEFAULT_ENVIRONMENT
    app_name: str = DEFAULT_APP_NAME
    log_level: str = DEFAULT_LOG_LEVEL

    @field_validator("environment")
    @classmethod
    def _validate_environment(cls, value: str) -> str:
        """Normalize and validate the runtime environment."""
        return normalize_environment(value)

    @field_validator("app_name")
    @classmethod
    def _validate_app_name(cls, value: str) -> str:
        """Validate the app name."""
        if not value.strip():
            raise ValueError("HARUQUANT_APP_NAME cannot be empty.")
        return value.strip()

    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, value: str) -> str:
        """Normalize and validate logging level."""
        return normalize_log_level(value)


class RuntimeSettings(BaseModel):
    """
    Validated runtime settings shared across HaruQuant tools and workflows.

    Secret values should not be included here. Use secret references or a
    dedicated secret provider for passwords, API keys, broker tokens, and other
    sensitive material.
    """

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    environment: str = DEFAULT_RUNTIME_ENVIRONMENT
    app_name: str = DEFAULT_APP_NAME
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    ui_origin: str = "http://localhost:3000"
    database_url: str = "sqlite:///data/database/haruquant.db"
    event_backend: str = "inmemory"
    log_level: str = DEFAULT_LOG_LEVEL
    allow_live_mutations: bool = False
    mt5_enabled: bool = False
    extra_config: dict[str, str] = Field(default_factory=dict)

    @field_validator("environment")
    @classmethod
    def _validate_environment(cls, value: str) -> str:
        """Normalize and validate the runtime environment."""
        return normalize_environment(value)

    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, value: str) -> str:
        """Normalize and validate logging level."""
        return normalize_log_level(value)

    @field_validator("api_port")
    @classmethod
    def _validate_api_port(cls, value: int) -> int:
        """Validate API port range."""
        if value < 1 or value > 65535:
            raise ValueError("api_port must be between 1 and 65535.")
        return value


def normalize_environment(value: str) -> str:
    """
    Normalize and validate a HaruQuant environment value.

    Args:
        value (str): Environment name.

    Returns:
        str: Canonical environment name.

    Raises:
        ValueError: If the environment is invalid.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError("environment must be a non-empty string.")

    normalized = value.strip().lower()
    if normalized not in VALID_ENVIRONMENTS:
        expected = ", ".join(sorted(VALID_ENVIRONMENTS))
        raise ValueError(
            f"Unsupported environment '{value}'. Expected one of: {expected}."
        )

    return ENVIRONMENT_ALIASES.get(normalized, normalized)


def normalize_log_level(value: str) -> str:
    """
    Normalize and validate a logging level.

    Args:
        value (str): Logging level name.

    Returns:
        str: Uppercase logging level.

    Raises:
        ValueError: If the log level is invalid.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError("log_level must be a non-empty string.")

    normalized = value.strip().upper()
    if normalized not in VALID_LOG_LEVELS:
        expected = ", ".join(sorted(VALID_LOG_LEVELS))
        raise ValueError(
            f"Unsupported log level '{value}'. Expected one of: {expected}."
        )

    return normalized


def _metadata(
    tool_name: str, request_id: str | None, execution_ms: float
) -> dict[str, Any]:
    """Build standard tool metadata."""
    return {
        "tool_name": tool_name,
        "tool_version": TOOL_VERSION,
        "tool_category": TOOL_CATEGORY,
        "tool_risk_level": TOOL_RISK_LEVEL,
        "request_id": request_id,
        "execution_ms": execution_ms,
        "read_only": READ_ONLY,
        "writes_file": WRITES_FILE,
        "modifies_database": MODIFIES_DATABASE,
        "places_trade": PLACES_TRADE,
        "requires_network": REQUIRES_NETWORK,
    }


def _success_response(
    *,
    tool_name: str,
    message: str,
    data: Any,
    request_id: str | None,
    started_at: float,
) -> dict[str, Any]:
    """Build a standard successful AI-tool response."""
    execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
    return {
        "status": "success",
        "message": message,
        "data": data,
        "error": None,
        "metadata": _metadata(tool_name, request_id, execution_ms),
    }


def _error_response(
    *,
    tool_name: str,
    message: str,
    code: str,
    details: str,
    request_id: str | None,
    started_at: float,
) -> dict[str, Any]:
    """Build a standard error AI-tool response."""
    execution_ms = round((time.perf_counter() - started_at) * 1000, 3)
    return {
        "status": "error",
        "message": message,
        "data": None,
        "error": {"code": code, "details": details},
        "metadata": _metadata(tool_name, request_id, execution_ms),
    }


def _normalize_env_file(env_file: str | Path) -> Path:
    """
    Normalize and validate a dotenv file path.

    Missing files are allowed. Existing directories are rejected.
    """
    if not isinstance(env_file, (str, Path)):
        raise ConfigurationError("env_file must be a string or pathlib.Path.")

    path = Path(env_file).expanduser()
    if path.exists() and path.is_dir():
        raise ConfigurationError(f"env_file points to a directory: {path}")

    return path


def _parse_dotenv_line(line: str) -> tuple[str, str] | None:
    """
    Parse one dotenv line.

    Supported syntax:
        - KEY=VALUE
        - export KEY=VALUE
        - quoted values
        - full-line comments
    """
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None

    if stripped.startswith("export "):
        stripped = stripped[len("export ") :].strip()

    if "=" not in stripped:
        return None

    key, raw_value = stripped.split("=", 1)
    key = key.strip()
    if not key:
        return None

    value = raw_value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]

    return key, value


def parse_env_file(path: Path) -> dict[str, str]:
    """
    Parse a dotenv file into key-value strings.

    Args:
        path (Path): Dotenv path.

    Returns:
        dict[str, str]: Parsed dotenv values.

    Raises:
        ConfigurationError: If an existing file cannot be read.
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


def collect_prefixed_values(source: Mapping[str, str], prefix: str) -> dict[str, str]:
    """
    Collect environment values starting with a prefix.

    Args:
        source (Mapping[str, str]): Source mapping, usually os.environ.
        prefix (str): Prefix to strip, for example ``HQT_``.

    Returns:
        dict[str, str]: Lowercase setting keys without prefix.
    """
    if not isinstance(prefix, str) or not prefix:
        raise SettingsError("prefix must be a non-empty string.")

    values: dict[str, str] = {}
    for key, value in source.items():
        if key.startswith(prefix):
            values[key[len(prefix) :].lower()] = value
    return values


def normalize_mapping(
    values: Mapping[str, Any],
    *,
    environment: str | None = None,
) -> dict[str, Any]:
    """
    Normalize mapping keys to lowercase and optionally inject environment.

    Args:
        values (Mapping[str, Any]): Raw setting values.
        environment (str | None): Optional environment override.

    Returns:
        dict[str, Any]: Normalized mapping.

    Raises:
        SettingsError: If values is not a mapping.
    """
    if not isinstance(values, Mapping):
        raise SettingsError("values must be a mapping.")

    data = {str(key).lower(): value for key, value in values.items()}
    if environment is not None:
        data["environment"] = environment
    return data


def _setting(name: str, dotenv_values: Mapping[str, str], default: str) -> str:
    """Resolve a simple setting from environment, dotenv, or default."""
    return os.getenv(name) or dotenv_values.get(name) or default


def get_settings(env_file: str | Path = DEFAULT_ENV_FILE) -> Settings:
    """
    Load lightweight non-secret HaruQuant application settings.

    Environment variables take precedence over dotenv values.

    Args:
        env_file (str | Path): Dotenv file path.

    Returns:
        Settings: Validated lightweight settings.

    Raises:
        ConfigurationError: If the env file cannot be read or settings are invalid.
    """
    path = _normalize_env_file(env_file)
    dotenv_values = parse_env_file(path)

    try:
        settings = Settings(
            environment=_setting("HARUQUANT_ENV", dotenv_values, DEFAULT_ENVIRONMENT),
            app_name=_setting("HARUQUANT_APP_NAME", dotenv_values, DEFAULT_APP_NAME),
            log_level=_setting("HARUQUANT_LOG_LEVEL", dotenv_values, DEFAULT_LOG_LEVEL),
        )
    except ValidationError as error:
        raise ConfigurationError(str(error)) from error

    logger.info(
        "Settings loaded | environment=%s | app_name=%s | log_level=%s",
        settings.environment,
        settings.app_name,
        settings.log_level,
    )
    return settings


def get_environment(env_file: str | Path = DEFAULT_ENV_FILE) -> str:
    """
    Return the configured lightweight HaruQuant environment name.

    Args:
        env_file (str | Path): Dotenv file path.

    Returns:
        str: Canonical environment name.
    """
    return get_settings(env_file=env_file).environment


def is_production(env_file: str | Path = DEFAULT_ENV_FILE) -> bool:
    """
    Return whether HaruQuant is configured for production.

    Args:
        env_file (str | Path): Dotenv file path.

    Returns:
        bool: True if environment is production.
    """
    return get_environment(env_file=env_file) == "production"


def is_test(env_file: str | Path = DEFAULT_ENV_FILE) -> bool:
    """
    Return whether HaruQuant is configured for tests.

    Args:
        env_file (str | Path): Dotenv file path.

    Returns:
        bool: True if environment is test.
    """
    return get_environment(env_file=env_file) == "test"


def _load_runtime_settings(
    *,
    environment: str | None = None,
    environ: Mapping[str, str] | None = None,
    env_dir: Path = DEFAULT_ENV_DIR,
    prefix: str = DEFAULT_ENV_PREFIX,
) -> RuntimeSettings:
    """Load runtime settings with env-file and process-env precedence."""
    process_env = environ if environ is not None else os.environ
    selected_env_raw = (
        environment
        or process_env.get(f"{prefix}ENVIRONMENT")
        or DEFAULT_RUNTIME_ENVIRONMENT
    )
    selected_env = normalize_environment(selected_env_raw)

    env_file = env_dir / f"{selected_env}.env"
    example_file = env_dir / f"{selected_env}.env.example"
    file_values = parse_env_file(env_file)
    if not file_values:
        file_values = parse_env_file(example_file)

    merged: dict[str, Any] = normalize_mapping(file_values, environment=selected_env)
    merged.update(collect_prefixed_values(process_env, prefix))
    merged.setdefault("environment", selected_env)

    extra = {
        key: value
        for key, value in merged.items()
        if key not in RuntimeSettings.model_fields
    }
    merged["extra_config"] = {str(key): str(value) for key, value in extra.items()}

    return RuntimeSettings.model_validate(merged)


def load_runtime_settings(
    *,
    environment: str | None = None,
    environ: Mapping[str, str] | None = None,
    env_dir: Path = DEFAULT_ENV_DIR,
    prefix: str = DEFAULT_ENV_PREFIX,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Load validated runtime settings from env files and process overrides.

    Use this tool when an agent or workflow needs read-only configuration
    metadata for the current runtime. It does not expose secrets.

    Args:
        environment (str | None): Optional environment override.
        environ (Mapping[str, str] | None): Optional environment mapping for tests.
        env_dir (Path): Directory containing env files.
        prefix (str): Environment variable prefix.
        request_id (str | None): Optional workflow/request trace ID.

    Returns:
        dict[str, Any]: Standard AI-tool response.
    """
    tool_name = "load_runtime_settings"
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s", tool_name, request_id)

    try:
        settings = _load_runtime_settings(
            environment=environment,
            environ=environ,
            env_dir=env_dir,
            prefix=prefix,
        )
    except ValidationError as error:
        return _error_response(
            tool_name=tool_name,
            message="Settings validation failed.",
            code="VALIDATION_FAILED",
            details=str(error),
            request_id=request_id,
            started_at=started_at,
        )
    except (SettingsError, ConfigurationError, ValueError) as error:
        return _error_response(
            tool_name=tool_name,
            message="Invalid settings input.",
            code="INVALID_INPUT",
            details=str(error),
            request_id=request_id,
            started_at=started_at,
        )
    except Exception as error:
        logger.exception("%s failed | request_id=%s", tool_name, request_id)
        return _error_response(
            tool_name=tool_name,
            message="Failed to load settings.",
            code="TOOL_EXECUTION_FAILED",
            details=str(error),
            request_id=request_id,
            started_at=started_at,
        )

    logger.info(
        "%s completed | request_id=%s | environment=%s",
        tool_name,
        request_id,
        settings.environment,
    )
    return _success_response(
        tool_name=tool_name,
        message="Settings loaded successfully.",
        data=settings.model_dump(),
        request_id=request_id,
        started_at=started_at,
    )


def _load_runtime_settings_from_mapping(
    values: Mapping[str, Any],
    *,
    environment: str | None = None,
) -> RuntimeSettings:
    """Validate mapping-based runtime settings."""
    normalized = normalize_mapping(values, environment=environment)
    extra = {
        key: value
        for key, value in normalized.items()
        if key not in RuntimeSettings.model_fields
    }
    normalized["extra_config"] = {str(key): str(value) for key, value in extra.items()}

    try:
        return RuntimeSettings.model_validate(normalized)
    except ValidationError as error:
        raise SettingsError(str(error)) from error


def load_runtime_settings_from_mapping(
    values: Mapping[str, Any],
    *,
    environment: str | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Validate a prebuilt mapping as RuntimeSettings.

    Use this tool to validate deterministic configuration data before using it
    in an agentic runtime or tool workflow.

    Args:
        values (Mapping[str, Any]): Raw settings mapping.
        environment (str | None): Optional environment override.
        request_id (str | None): Optional workflow/request trace ID.

    Returns:
        dict[str, Any]: Standard AI-tool response.
    """
    tool_name = "load_runtime_settings_from_mapping"
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s", tool_name, request_id)

    try:
        settings = _load_runtime_settings_from_mapping(values, environment=environment)
    except SettingsError as error:
        return _error_response(
            tool_name=tool_name,
            message="Settings validation failed.",
            code="VALIDATION_FAILED",
            details=str(error),
            request_id=request_id,
            started_at=started_at,
        )
    except Exception as error:
        return _error_response(
            tool_name=tool_name,
            message="Tool failed.",
            code="TOOL_EXECUTION_FAILED",
            details=str(error),
            request_id=request_id,
            started_at=started_at,
        )

    return _success_response(
        tool_name=tool_name,
        message="Settings validated.",
        data=settings.model_dump(),
        request_id=request_id,
        started_at=started_at,
    )


def _inject_runtime_settings(
    target: MutableMapping[str, Any],
    settings: RuntimeSettings,
) -> None:
    """Inject settings into a mutable container."""
    target.update(settings.model_dump())


def inject_runtime_settings(
    target: Any,
    settings: RuntimeSettings | Mapping[str, Any],
    request_id: str | None = None,
) -> dict[str, Any]:
    """
    Copy validated runtime settings into a mutable container.

    This tool mutates only the provided in-memory target mapping. It does not
    write files, databases, or broker state.

    Args:
        target (MutableMapping[str, Any]): Mutable container to update.
        settings (RuntimeSettings | Mapping[str, Any]): Settings to inject.
        request_id (str | None): Optional workflow/request trace ID.

    Returns:
        dict[str, Any]: Standard AI-tool response.
    """
    tool_name = "inject_runtime_settings"
    started_at = time.perf_counter()
    logger.info("%s called | request_id=%s", tool_name, request_id)

    if not isinstance(target, MutableMapping):
        return _error_response(
            tool_name=tool_name,
            message="Invalid target.",
            code="INVALID_INPUT",
            details="target must be a mutable mapping.",
            request_id=request_id,
            started_at=started_at,
        )

    try:
        settings_obj = (
            settings
            if isinstance(settings, RuntimeSettings)
            else RuntimeSettings.model_validate(dict(settings))
        )
        _inject_runtime_settings(target, settings_obj)
    except ValidationError as error:
        return _error_response(
            tool_name=tool_name,
            message="Settings validation failed.",
            code="VALIDATION_FAILED",
            details=str(error),
            request_id=request_id,
            started_at=started_at,
        )
    except Exception as error:
        return _error_response(
            tool_name=tool_name,
            message="Injection failed.",
            code="TOOL_EXECUTION_FAILED",
            details=str(error),
            request_id=request_id,
            started_at=started_at,
        )

    return _success_response(
        tool_name=tool_name,
        message="Settings injected.",
        data={"updated_keys": sorted(settings_obj.model_dump().keys())},
        request_id=request_id,
        started_at=started_at,
    )


__all__ = [
    "DEFAULT_APP_NAME",
    "DEFAULT_ENV_DIR",
    "DEFAULT_ENV_FILE",
    "DEFAULT_ENV_PREFIX",
    "DEFAULT_ENVIRONMENT",
    "DEFAULT_LOG_LEVEL",
    "DEFAULT_RUNTIME_ENVIRONMENT",
    "RuntimeSettings",
    "Settings",
    "SettingsError",
    "VALID_ENVIRONMENTS",
    "VALID_LOG_LEVELS",
    "collect_prefixed_values",
    "get_environment",
    "get_settings",
    "inject_runtime_settings",
    "is_production",
    "is_test",
    "load_runtime_settings",
    "load_runtime_settings_from_mapping",
    "normalize_environment",
    "normalize_log_level",
    "normalize_mapping",
    "parse_env_file",
]
