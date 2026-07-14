"""Explicit runtime-settings loading and opaque secret resolution."""

from __future__ import annotations

import os
import re
from collections.abc import Callable, Mapping

from pydantic import SecretStr
from pydantic import ValidationError as PydanticValidationError

from app.utils.errors.exceptions import ConfigurationError, SecurityError
from app.utils.settings.models import LoggingSettings, RuntimeSettings

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


def _select_environment(environment: Mapping[str, str]) -> dict[str, object]:
    return {key: environment[key] for key in _SUPPORTED_KEYS if key in environment}


def _parse_integer(value: object, key: str) -> int:
    if isinstance(value, bool):
        raise ConfigurationError("CONFIGURATION_INVALID", f"{key}_INVALID")
    try:
        return int(str(value))
    except ValueError:
        raise ConfigurationError("CONFIGURATION_INVALID", f"{key}_INVALID") from None


def _parse_boolean(value: object, key: str) -> bool:
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
        environment: Optional environment mapping; ``os.environ`` when omitted.

    Returns:
        Validated immutable runtime settings.

    Raises:
        ConfigurationError: If a key or value is invalid.
    """
    explicit = dict(explicit_values or {})
    unknown = set(explicit) - _SUPPORTED_KEYS
    if unknown:
        raise ConfigurationError("CONFIGURATION_UNKNOWN_KEY")
    source_environment = os.environ if environment is None else environment
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
