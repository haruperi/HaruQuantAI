"""Authoritative owner-event translation into public stream envelopes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, is_dataclass

from pydantic import BaseModel

from app.services.api.contracts import StreamEvent
from app.utils import get_logger, is_sensitive_key, to_json_safe, utc_now

logger = get_logger(__name__)

_MAX_STREAM_DEPTH = 8


class StreamValidationError(ValueError):
    """Bounded invalid owner-event failure."""


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    """Normalize a supported object into a mapping.

    Returns:
        Detached mapping of public fields.

    Raises:
        StreamValidationError: If the value has no supported public shape.
    """
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    message = f"{label} must be a mapping or typed contract"
    raise StreamValidationError(message)


def _assert_secret_free(value: object, *, depth: int = 0) -> None:
    """Reject secret-bearing keys recursively before stream publication.

    Raises:
        StreamValidationError: If content is too deep or secret-bearing.
    """
    if depth > _MAX_STREAM_DEPTH:
        raise StreamValidationError("stream payload exceeds nesting limit")
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str) or is_sensitive_key(key):
                raise StreamValidationError("stream payload contains a forbidden key")
            _assert_secret_free(item, depth=depth + 1)
    elif isinstance(value, list | tuple):
        for item in value:
            _assert_secret_free(item, depth=depth + 1)


def build_stream_event(event: object, trace: object) -> StreamEvent:
    """Translate one validated owner event into a redacted ordered envelope.

    Args:
        event: Authoritative owner event or detached mapping.
        trace: Request/trace mapping containing route and identifiers.

    Returns:
        Immutable public ``StreamEvent``.

    Raises:
        StreamValidationError: If event or trace evidence is malformed or unsafe.
    """
    logger.info("Building one ordered API stream event")
    owner = _mapping(event, label="event")
    trace_values = _mapping(trace, label="trace")
    _assert_secret_free(owner)
    try:
        sequence = int(str(owner["sequence"]))
        request_id = str(trace_values["request_id"])
        route = str(trace_values["route"])
        trace_id_value = trace_values.get("trace_id")
        event_type = str(owner.get("event_type", "payload"))
        timestamp = owner.get("timestamp", utc_now())
    except (KeyError, TypeError, ValueError) as error:
        raise StreamValidationError("stream evidence is incomplete") from error
    reserved = {"sequence", "event_type", "timestamp", "error", "cursor"}
    payload = {key: value for key, value in owner.items() if key not in reserved}
    try:
        safe_payload = to_json_safe(payload)
    except (TypeError, ValueError) as error:
        raise StreamValidationError("stream payload cannot be serialized") from error
    if not isinstance(safe_payload, Mapping):
        raise StreamValidationError("stream payload must serialize as a mapping")
    return StreamEvent.model_validate(
        {
            "sequence": sequence,
            "request_id": request_id,
            "trace_id": str(trace_id_value) if trace_id_value is not None else None,
            "route": route,
            "event_type": event_type,
            "timestamp": timestamp,
            "payload": safe_payload if event_type == "payload" else None,
            "error": (str(owner["error"]) if owner.get("error") is not None else None),
            "cursor": (
                str(owner["cursor"]) if owner.get("cursor") is not None else None
            ),
        }
    )


__all__ = ("StreamValidationError", "build_stream_event")
