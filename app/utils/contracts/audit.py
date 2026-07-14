"""Shared immutable audit-event contract and contract-field validation."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping
from datetime import datetime, timedelta
from types import MappingProxyType
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

type JsonValue = (
    None | bool | int | float | str | tuple[JsonValue, ...] | Mapping[str, JsonValue]
)

_UUID4_SUFFIX = (
    r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}"
)
_TRACE_SUFFIX = rf"(?:{_UUID4_SUFFIX}|[0-9a-f]{{64}})"
_MAX_PAYLOAD_BYTES = 65_536
_MAX_PAYLOAD_DEPTH = 16
_MAX_PAYLOAD_ITEMS = 1_000
_PROTECTED_KEYS = frozenset(
    {
        "password",
        "passwd",
        "privatekey",
        "clientsecret",
        "apikey",
        "authorization",
    }
)


def validate_non_empty(value: str, field_name: str) -> str:
    """Validate a required contract string.

    Args:
        value: Candidate value.
        field_name: Field name used in the validation message.

    Returns:
        The unchanged validated value.

    Raises:
        ValueError: If the value is empty or has surrounding whitespace.
    """
    if not value or value != value.strip():
        message = f"{field_name} must be non-empty and trimmed"
        raise ValueError(message)
    return value


def validate_utc(value: datetime, field_name: str) -> datetime:
    """Validate an aware UTC datetime.

    Args:
        value: Candidate datetime.
        field_name: Field name used in the validation message.

    Returns:
        The unchanged validated datetime.

    Raises:
        ValueError: If the datetime is naive or not UTC.
    """
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        message = f"{field_name} must be an aware UTC datetime"
        raise ValueError(message)
    return value


def validate_trace_id(value: str, prefix: str, field_name: str) -> str:
    """Validate a canonical trace identifier.

    Args:
        value: Candidate identifier.
        prefix: Required identifier prefix.
        field_name: Field name used in the validation message.

    Returns:
        The unchanged validated identifier.

    Raises:
        ValueError: If the identifier is malformed.
    """
    validate_non_empty(value, field_name)
    if re.fullmatch(rf"{re.escape(prefix)}-{_TRACE_SUFFIX}", value) is None:
        message = f"{field_name} has invalid canonical syntax"
        raise ValueError(message)
    return value


def _normalize_key(value: str) -> str:
    return value.casefold().replace("-", "").replace("_", "")


def _freeze_json(
    value: object,
    *,
    depth: int,
    item_count: list[int],
) -> JsonValue:
    if depth > _MAX_PAYLOAD_DEPTH:
        raise ValueError("payload exceeds maximum nesting depth")
    if value is None or isinstance(value, bool | int | str):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("payload contains a non-finite number")
        return value
    if isinstance(value, Mapping):
        return _freeze_mapping(value, depth=depth, item_count=item_count)
    if isinstance(value, list | tuple):
        return _freeze_sequence(value, depth=depth, item_count=item_count)
    raise ValueError("payload contains a non-JSON-safe value")


def _add_items(item_count: list[int], amount: int) -> None:
    item_count[0] += amount
    if item_count[0] > _MAX_PAYLOAD_ITEMS:
        raise ValueError("payload exceeds maximum aggregate items")


def _freeze_mapping(
    value: Mapping[object, object],
    *,
    depth: int,
    item_count: list[int],
) -> Mapping[str, JsonValue]:
    _add_items(item_count, len(value))
    frozen: dict[str, JsonValue] = {}
    for key, nested in value.items():
        if not isinstance(key, str):
            raise TypeError("payload mapping keys must be strings")
        validate_non_empty(key, "payload key")
        if _normalize_key(key) in _PROTECTED_KEYS:
            raise ValueError("payload contains a protected credential key")
        frozen[key] = _freeze_json(
            nested,
            depth=depth + 1,
            item_count=item_count,
        )
    return MappingProxyType(frozen)


def _freeze_sequence(
    value: list[object] | tuple[object, ...],
    *,
    depth: int,
    item_count: list[int],
) -> tuple[JsonValue, ...]:
    _add_items(item_count, len(value))
    return tuple(
        _freeze_json(item, depth=depth + 1, item_count=item_count) for item in value
    )


def _thaw_json(value: JsonValue) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw_json(nested) for key, nested in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


class AuditEvent(BaseModel):
    """Immutable, bounded, redacted audit-event envelope version 1."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        frozen=True,
    )

    contract_version: Literal["v1"]
    schema_id: Literal["utils.audit_event.v1"]
    event_id: str
    timestamp: datetime
    domain: str
    action: str
    principal_id: str | None = None
    request_id: str
    correlation_id: str
    causation_id: str | None = None
    payload: Mapping[str, JsonValue]

    @field_validator("event_id")
    @classmethod
    def _validate_event_id(cls, value: str) -> str:
        return validate_trace_id(value, "evt", "event_id")

    @field_validator("request_id")
    @classmethod
    def _validate_request_id(cls, value: str) -> str:
        return validate_trace_id(value, "req", "request_id")

    @field_validator("correlation_id")
    @classmethod
    def _validate_correlation_id(cls, value: str) -> str:
        return validate_trace_id(value, "cor", "correlation_id")

    @field_validator("causation_id")
    @classmethod
    def _validate_causation_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_trace_id(value, "cau", "causation_id")

    @field_validator("timestamp")
    @classmethod
    def _validate_timestamp(cls, value: datetime) -> datetime:
        return validate_utc(value, "timestamp")

    @field_validator("domain", "action", "principal_id")
    @classmethod
    def _validate_identity_fields(cls, value: str | None, info: object) -> str | None:
        if value is None:
            return None
        field_name = getattr(info, "field_name", "contract field")
        return validate_non_empty(value, str(field_name))

    @field_validator("payload", mode="before")
    @classmethod
    def _validate_payload(cls, value: object) -> Mapping[str, JsonValue]:
        if not isinstance(value, Mapping):
            raise TypeError("payload must be a mapping")
        frozen = _freeze_json(value, depth=0, item_count=[0])
        if not isinstance(frozen, Mapping):
            raise TypeError("payload must be a mapping")
        encoded = json.dumps(
            _thaw_json(frozen),
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        if len(encoded) > _MAX_PAYLOAD_BYTES:
            raise ValueError("payload exceeds maximum canonical JSON size")
        return frozen

    @field_validator("payload")
    @classmethod
    def _freeze_validated_payload(
        cls,
        value: Mapping[str, JsonValue],
    ) -> Mapping[str, JsonValue]:
        frozen = _freeze_json(value, depth=0, item_count=[0])
        if not isinstance(frozen, Mapping):
            raise TypeError("payload must be a mapping")
        return frozen
