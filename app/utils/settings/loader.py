"""Explicit runtime-settings loading and opaque secret resolution."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping

from pydantic import SecretStr
from pydantic import ValidationError as PydanticValidationError

from app.utils.errors.exceptions import ConfigurationError, SecurityError
from app.utils.settings.models import AppSettings, LoggingSettings, RuntimeSettings

_SUPPORTED_KEYS = frozenset(
    {
        "ENVIRONMENT",
        "RUNTIME_PROFILE",
        "LOG_LEVEL",
        "LOG_RENDER",
        "LOG_FILE_PATH",
        "LOG_DIRECTORY",
        "LOG_MAX_BYTES",
        "LOG_BACKUP_COUNT",
        "LOG_RETENTION_DAYS",
        "LOG_COMPRESSION",
        "LOG_ENQUEUE",
        "LOG_COLORIZE",
    }
)
_SECRET_REFERENCE = re.compile(r"secret://[A-Za-z0-9._/-]{1,255}\Z")


class _EnvironmentSettings(AppSettings):
    """Raw supported environment values loaded through the settings boundary.

    Attributes:
        environment: Standard environment name override.
        runtime_profile: Standard runtime profile override.
        log_level: Configured log severity filter name.
        log_render: Rendering output format, human or json.
        log_file_path: Optional single log file destination.
        log_directory: Optional multiple log files destination directory.
        log_max_bytes: Size boundary for log rotation.
        log_backup_count: Max count of backup log files to retain.
        log_retention_days: Expiry time boundary for rotating log files.
        log_compression: Compression mode (zip or none) for rotated files.
        log_enqueue: True if log records are written in background queue.
        log_colorize: True if human-rendered logs are colored.
    """

    environment: str | None = None
    runtime_profile: str | None = None
    log_level: str | None = None
    log_render: str | None = None
    log_file_path: str | None = None
    log_directory: str | None = None
    log_max_bytes: str | None = None
    log_backup_count: str | None = None
    log_retention_days: str | None = None
    log_compression: str | None = None
    log_enqueue: str | None = None
    log_colorize: str | None = None


_ENVIRONMENT_FIELDS = {
    "ENVIRONMENT": "environment",
    "RUNTIME_PROFILE": "runtime_profile",
    "LOG_LEVEL": "log_level",
    "LOG_RENDER": "log_render",
    "LOG_FILE_PATH": "log_file_path",
    "LOG_DIRECTORY": "log_directory",
    "LOG_MAX_BYTES": "log_max_bytes",
    "LOG_BACKUP_COUNT": "log_backup_count",
    "LOG_RETENTION_DAYS": "log_retention_days",
    "LOG_COMPRESSION": "log_compression",
    "LOG_ENQUEUE": "log_enqueue",
    "LOG_COLORIZE": "log_colorize",
}


def _load_environment_settings() -> dict[str, str]:
    """Return supported dotenv/process values through one typed settings model.

    Returns:
        Mapping of uppercase environment key names to raw string values.
    """
    settings = _EnvironmentSettings()
    values: dict[str, str] = {}
    for environment_name, field_name in _ENVIRONMENT_FIELDS.items():
        value = getattr(settings, field_name)
        if value is not None:
            values[environment_name] = value
    return values


def _select_environment(environment: Mapping[str, str]) -> dict[str, object]:
    """Filter environment configuration keys to keep only supported settings.

    Args:
        environment: Full environment map to filter.

    Returns:
        Filtered map containing only supported settings.
    """
    return {key: environment[key] for key in _SUPPORTED_KEYS if key in environment}


def _parse_integer(value: object, key: str) -> int:
    """Parse an environment setting value to a bounded integer.

    Args:
        value: Raw value from settings.
        key: Settings key name for diagnostic logging.

    Returns:
        Parsed integer value.

    Raises:
        ConfigurationError: If the value cannot be parsed to an integer.
    """
    if isinstance(value, bool):
        raise ConfigurationError("CONFIGURATION_INVALID", f"{key}_INVALID")
    try:
        return int(str(value))
    except ValueError:
        raise ConfigurationError("CONFIGURATION_INVALID", f"{key}_INVALID") from None


def _parse_boolean(value: object, key: str) -> bool:
    """Parse an environment setting value to a boolean.

    Args:
        value: Raw value from settings.
        key: Settings key name for diagnostic logging.

    Returns:
        Parsed boolean value.

    Raises:
        ConfigurationError: If the value is not a valid boolean indicator.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.casefold()
        if normalized == "true":
            return True
        if normalized == "false":
            return False
    raise ConfigurationError("CONFIGURATION_INVALID", f"{key}_INVALID")


def _build_logging_values(merged: Mapping[str, object]) -> dict[str, object]:
    """Map raw settings values into LoggingSettings initialization keys.

    Args:
        merged: Merged setting key-value pairs.

    Returns:
        Dictionary mapping model fields to parsed settings values.
    """
    values: dict[str, object] = {}
    simple_keys = {
        "LOG_LEVEL": "level",
        "LOG_RENDER": "render",
        "LOG_COMPRESSION": "compression",
    }
    for source_key, model_key in simple_keys.items():
        if source_key in merged:
            values[model_key] = merged[source_key]
    if "LOG_FILE_PATH" in merged:
        raw_path = merged["LOG_FILE_PATH"]
        values["file_path"] = None if raw_path in (None, "") else raw_path
    if "LOG_DIRECTORY" in merged:
        raw_directory = merged["LOG_DIRECTORY"]
        values["log_directory"] = None if raw_directory in (None, "") else raw_directory
    if "LOG_MAX_BYTES" in merged:
        values["max_bytes"] = _parse_integer(
            merged["LOG_MAX_BYTES"],
            "LOG_MAX_BYTES",
        )
    if "LOG_BACKUP_COUNT" in merged:
        values["backup_count"] = _parse_integer(
            merged["LOG_BACKUP_COUNT"],
            "LOG_BACKUP_COUNT",
        )
    if "LOG_RETENTION_DAYS" in merged:
        values["retention_days"] = _parse_integer(
            merged["LOG_RETENTION_DAYS"],
            "LOG_RETENTION_DAYS",
        )
    if "LOG_ENQUEUE" in merged:
        values["enqueue"] = _parse_boolean(merged["LOG_ENQUEUE"], "LOG_ENQUEUE")
    if "LOG_COLORIZE" in merged:
        values["colorize"] = _parse_boolean(
            merged["LOG_COLORIZE"],
            "LOG_COLORIZE",
        )
    return values


def load_settings(
    explicit_values: Mapping[str, object] | None = None,
    environment: Mapping[str, str] | None = None,
) -> RuntimeSettings:
    """Load immutable settings using explicit, environment, default precedence.

    Args:
        explicit_values: Optional exact uppercase settings.
        environment: Optional explicit mapping; centralized settings when omitted.

    Returns:
        Validated immutable runtime settings.

    Raises:
        ConfigurationError: If a key or value is invalid.
    """
    explicit = dict(explicit_values or {})
    unknown = set(explicit) - _SUPPORTED_KEYS
    if unknown:
        raise ConfigurationError("CONFIGURATION_UNKNOWN_KEY")
    source_environment = (
        _load_environment_settings() if environment is None else environment
    )
    merged = _select_environment(source_environment)
    merged.update(explicit)

    try:
        logging_settings = LoggingSettings.model_validate(_build_logging_values(merged))
    except PydanticValidationError:
        raise ConfigurationError("CONFIGURATION_INVALID") from None
    runtime_values: dict[str, object] = {"logging": logging_settings}
    if "ENVIRONMENT" in merged:
        runtime_values["environment"] = merged["ENVIRONMENT"]
    if "RUNTIME_PROFILE" in merged:
        runtime_values["runtime_profile"] = merged["RUNTIME_PROFILE"]
    try:
        return RuntimeSettings.model_validate(runtime_values)
    except PydanticValidationError:
        raise ConfigurationError("CONFIGURATION_INVALID") from None


def resolve_secret_reference(
    reference: str,
    source: Callable[[str], str],
) -> SecretStr:
    """Resolve an opaque secret reference through an injected source.

    Args:
        reference: Valid opaque ``secret://`` reference.
        source: Injected secret-source callable.

    Returns:
        A masked Pydantic secret value.

    Raises:
        ConfigurationError: If the reference is malformed.
        SecurityError: If resolution fails or returns no secret.
    """
    if _SECRET_REFERENCE.fullmatch(reference) is None:
        raise ConfigurationError("SECRET_REFERENCE_INVALID")
    try:
        resolved = source(reference)
    except Exception:  # noqa: BLE001 - injected sources may use arbitrary clients.
        raise SecurityError("SECRET_RESOLUTION_FAILED") from None
    if not isinstance(resolved, str) or not resolved:
        raise SecurityError("SECRET_RESOLUTION_FAILED")
    return SecretStr(resolved)
