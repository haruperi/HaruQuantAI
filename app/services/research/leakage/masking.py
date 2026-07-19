"""Recursive masking for Research artifacts and warnings."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from app.utils import is_sensitive_key, logger
from app.utils.errors import SecurityError

type JSONValue = (
    None | bool | int | float | str | list["JSONValue"] | Mapping[str, "JSONValue"]
)

_FORBIDDEN_TOKENS = ("forward", "future", "target", "account", "broker")
_MASK = "[REDACTED]"


def _sensitive(key: str, extra: frozenset[str]) -> bool:
    """Determine whether one key must be masked.

    Args:
        key: Candidate mapping key.
        extra: Caller-supplied denylist.

    Returns:
        Whether the key is sensitive or research-only.
    """
    logger.debug("Classifying Research artifact key")
    lowered = key.casefold()
    return (
        is_sensitive_key(key)
        or lowered in {item.casefold() for item in extra}
        or any(token in lowered for token in _FORBIDDEN_TOKENS)
    )


def _mask(value: JSONValue, extra: frozenset[str]) -> JSONValue:
    """Recursively mask one JSON-compatible value.

    Args:
        value: JSON-compatible value.
        extra: Caller-supplied denylist.

    Returns:
        New masked value.

    Raises:
        SecurityError: If an unsupported structure is supplied.
    """
    logger.debug("Recursively masking Research artifact value")
    if isinstance(value, Mapping):
        return {
            str(key): _MASK if _sensitive(str(key), extra) else _mask(item, extra)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_mask(item, extra) for item in value]
    if isinstance(value, tuple) or (
        isinstance(value, Sequence) and not isinstance(value, str)
    ):
        raise SecurityError("RES_SENSITIVE_OUTPUT_REJECTED", "UNSUPPORTED_SEQUENCE")
    if value is None or isinstance(value, bool | int | float | str):
        return value
    raise SecurityError("RES_SENSITIVE_OUTPUT_REJECTED", "NON_JSON_VALUE")


def mask_research_artifact(
    artifact: JSONValue, *, extra_sensitive_keys: frozenset[str] = frozenset()
) -> JSONValue:
    """Return a recursively masked copy without mutating the input.

    Args:
        artifact: JSON-compatible Research artifact.
        extra_sensitive_keys: Additional case-insensitive keys to mask.

    Returns:
        New masked JSON-compatible value.

    Raises:
        SecurityError: If the artifact contains unsupported values.
    """
    logger.info("Masking sensitive Research artifact fields")
    return _mask(artifact, extra_sensitive_keys)


__all__ = ("mask_research_artifact",)
