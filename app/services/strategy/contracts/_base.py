"""Shared private validation, coercion, and base-model mechanics."""

from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from types import MappingProxyType

from pydantic import (
    BaseModel,
    ConfigDict,
)

from app.utils import logger

_MAX_TEXT_LENGTH = 512
_SHA256_LENGTH = 64

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | tuple["JsonValue", ...] | Mapping[str, "JsonValue"]


def _utc(value: datetime) -> datetime:
    """Validate that a timestamp is timezone-aware UTC.

    Args:
        value: Timestamp to validate.

    Returns:
        The validated timestamp.

    Raises:
        ValueError: If the timestamp is naive or not UTC.
    """
    logger.debug("Validating a Strategy UTC timestamp")
    offset = value.utcoffset()
    if value.tzinfo is None or offset is None:
        raise ValueError("timestamp must be timezone-aware UTC")
    if offset.total_seconds() != 0:
        raise ValueError("timestamp must use UTC")
    return value


def _text(value: str) -> str:
    """Validate a required bounded text value.

    Args:
        value: Text to validate.

    Returns:
        Stripped text.

    Raises:
        ValueError: If the text is blank or oversized.
    """
    logger.debug("Validating Strategy text")
    cleaned = value.strip()
    if not cleaned or len(cleaned) > _MAX_TEXT_LENGTH:
        raise ValueError("text must contain 1..512 characters")
    return cleaned


def _hash(value: str) -> str:
    """Validate one lowercase SHA-256 digest.

    Args:
        value: Digest to validate.

    Returns:
        The validated digest.

    Raises:
        ValueError: If the digest is malformed.
    """
    logger.debug("Validating a Strategy SHA-256 digest")
    if len(value) != _SHA256_LENGTH or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError("hash must be a lowercase 64-character SHA-256 digest")
    return value


def _finite_decimal(value: Decimal | None) -> Decimal | None:
    """Validate an optional finite decimal value.

    Args:
        value: Optional decimal value.

    Returns:
        The finite decimal or ``None``.

    Raises:
        ValueError: If the decimal is non-finite.
    """
    logger.debug("Validating a finite Strategy decimal")
    if value is not None and not value.is_finite():
        raise ValueError("decimal values must be finite")
    return value


def _freeze_json(value: object) -> JsonValue:
    """Recursively freeze JSON-compatible values.

    Args:
        value: Candidate JSON-compatible value.

    Returns:
        An immutable JSON-compatible value.

    Raises:
        ValueError: If an unsupported or non-finite value is supplied.
    """
    logger.debug("Freezing Strategy JSON material")
    if isinstance(value, Mapping):
        return MappingProxyType(
            {_text(str(key)): _freeze_json(item) for key, item in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item) for item in value)
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("JSON numbers must be finite")
        return value
    raise ValueError("value must be JSON-compatible")


def _thaw_json(value: JsonValue) -> JsonScalar | list[object] | dict[str, object]:
    """Convert frozen JSON material to ordinary JSON containers.

    Args:
        value: Frozen value.

    Returns:
        JSON-serializable material.
    """
    logger.debug("Serializing Strategy JSON material")
    if isinstance(value, Mapping):
        return {str(key): _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def _contains_executable_marker(value: JsonValue) -> bool:
    """Return whether JSON text contains an executable payload marker.

    Args:
        value: JSON-compatible value.

    Returns:
        Whether executable-looking content is present recursively.
    """
    logger.debug("Scanning Strategy JSON for executable markers")
    if isinstance(value, str):
        lowered = value.casefold()
        return any(
            marker in lowered
            for marker in ("import ", "exec(", "eval(", "__", "file://")
        )
    if isinstance(value, Mapping):
        return any(_contains_executable_marker(item) for item in value.values())
    if isinstance(value, tuple):
        return any(_contains_executable_marker(item) for item in value)
    return False


class _Contract(BaseModel):
    """Strict immutable base for Strategy contracts."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)
