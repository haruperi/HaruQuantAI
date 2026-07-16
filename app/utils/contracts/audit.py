"""Define the immutable audit-event contract and its bounded validators.

Audit payload validation is deliberately fail-closed: only bounded JSON-safe
values without protected credential keys can enter the shared contract.
"""

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
    {"password", "passwd", "privatekey", "clientsecret", "apikey", "authorization"}
)


def validate_non_empty(value: str, field_name: str) -> str:
    """Validate a required trimmed contract string.

    Args:
        value: Candidate string supplied by a contract producer.
        field_name: Stable field label used in validation errors.

    Returns:
        The unchanged validated string.

    Raises:
        ValueError: The string is empty or contains outer whitespace.
    """
    if not value or value != value.strip():
        message = f"{field_name} must be non-empty and trimmed"
        raise ValueError(message)
    return value


def validate_utc(value: datetime, field_name: str) -> datetime:
    """Validate an aware UTC datetime.

    Args:
        value: Candidate timestamp.
        field_name: Stable field label used in validation errors.

    Returns:
        The unchanged validated timestamp.

    Raises:
        ValueError: The timestamp is naive or has a non-UTC offset.
    """
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        message = f"{field_name} must be an aware UTC datetime"
        raise ValueError(message)
    return value


def validate_trace_id(value: str, prefix: str, field_name: str) -> str:
    """Validate a canonical UUID4 or stable-hash trace identifier.

    Args:
        value: Candidate prefixed trace identifier.
        prefix: Required identifier prefix without its separator.
        field_name: Stable field label used in validation errors.

    Returns:
        The unchanged validated identifier.

    Raises:
        ValueError: The value is empty, untrimmed, or non-canonical.
    """
    validate_non_empty(value, field_name)
    if re.fullmatch(rf"{re.escape(prefix)}-{_TRACE_SUFFIX}", value) is None:
        message = f"{field_name} has invalid canonical syntax"
        raise ValueError(message)
    return value


def _normalize_key(value: str) -> str:
    """Normalize a mapping key for credential-field comparison.

    Args:
        value: Source mapping key.

    Returns:
        A case-folded key without hyphens or underscores.
    """
    return value.casefold().replace("-", "").replace("_", "")


def _add_items(item_count: list[int], amount: int) -> None:
    """Add container items to the mutable traversal counter.

    Args:
        item_count: Single-element aggregate counter owned by one traversal.
        amount: Number of newly visited items.

    Raises:
        ValueError: The aggregate payload item limit is exceeded.
    """
    item_count[0] += amount
    if item_count[0] > _MAX_PAYLOAD_ITEMS:
        raise ValueError("payload exceeds maximum aggregate items")


def _freeze_json(value: object, *, depth: int, item_count: list[int]) -> JsonValue:
    """Validate and deeply freeze one JSON-safe value.

    Args:
        value: Candidate scalar or container value.
        depth: Current traversal depth, starting at zero.
        item_count: Shared single-element aggregate item counter.

    Returns:
        An immutable JSON-safe scalar, tuple, or mapping proxy.

    Raises:
        TypeError: A mapping key is not a string.
        ValueError: The value is unsafe, non-finite, protected, or over a
            configured payload bound.
    """
    if depth > _MAX_PAYLOAD_DEPTH:
        raise ValueError("payload exceeds maximum nesting depth")
    if value is None or isinstance(value, bool | int | str):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("payload contains a non-finite number")
        return value
    if isinstance(value, Mapping):
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
    if isinstance(value, list | tuple):
        _add_items(item_count, len(value))
        return tuple(
            _freeze_json(item, depth=depth + 1, item_count=item_count) for item in value
        )
    raise ValueError("payload contains a non-JSON-safe value")


def _thaw_json(value: JsonValue) -> object:
    """Convert a frozen payload to containers accepted by ``json.dumps``.

    Args:
        value: Frozen JSON-safe value.

    Returns:
        An equivalent scalar, list, or mutable mapping used only for encoding.
    """
    if isinstance(value, Mapping):
        return {key: _thaw_json(nested) for key, nested in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


class AuditEvent(BaseModel):
    """Represent an immutable, bounded audit-event envelope.

    Producers must redact payloads before construction. The contract performs
    an additional fail-closed protected-key check but does not originate or
    persist audit events.

    Attributes:
        contract_version: Fixed contract version, always ``"v1"``.
        schema_id: Fixed schema identity, always
            ``"utils.audit_event.v1"``.
        event_id: Canonical event identifier.
        timestamp: Aware UTC event timestamp.
        domain: Non-empty producing domain name.
        action: Non-empty audited action name.
        principal_id: Optional authenticated principal identifier.
        request_id: Canonical request trace identifier.
        correlation_id: Canonical correlation trace identifier.
        causation_id: Optional canonical causation trace identifier.
        payload: Deeply immutable, bounded JSON-safe event evidence.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid", frozen=True)

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
        """Validate and return the event identifier.

        Args:
            value: Candidate event identifier.

        Returns:
            The validated identifier.

        Raises:
            ValueError: The identifier is not canonical.
        """
        return validate_trace_id(value, "evt", "event_id")

    @field_validator("request_id")
    @classmethod
    def _validate_request_id(cls, value: str) -> str:
        """Validate and return the request identifier.

        Args:
            value: Candidate request identifier.

        Returns:
            The validated identifier.

        Raises:
            ValueError: The identifier is not canonical.
        """
        return validate_trace_id(value, "req", "request_id")

    @field_validator("correlation_id")
    @classmethod
    def _validate_correlation_id(cls, value: str) -> str:
        """Validate and return the correlation identifier.

        Args:
            value: Candidate correlation identifier.

        Returns:
            The validated identifier.

        Raises:
            ValueError: The identifier is not canonical.
        """
        return validate_trace_id(value, "cor", "correlation_id")

    @field_validator("causation_id")
    @classmethod
    def _validate_causation_id(cls, value: str | None) -> str | None:
        """Validate an optional causation identifier.

        Args:
            value: Candidate causation identifier or ``None``.

        Returns:
            ``None`` or the validated identifier.

        Raises:
            ValueError: A supplied identifier is not canonical.
        """
        return (
            None if value is None else validate_trace_id(value, "cau", "causation_id")
        )

    @field_validator("timestamp")
    @classmethod
    def _validate_timestamp(cls, value: datetime) -> datetime:
        """Validate and return the event timestamp.

        Args:
            value: Candidate event timestamp.

        Returns:
            The same aware UTC timestamp.

        Raises:
            ValueError: The timestamp is naive or not UTC.
        """
        return validate_utc(value, "timestamp")

    @field_validator("domain", "action", "principal_id")
    @classmethod
    def _validate_identity_fields(cls, value: str | None, info: object) -> str | None:
        """Validate an optional identity-related string field.

        Args:
            value: Candidate value or ``None``.
            info: Pydantic validation metadata containing the field name.

        Returns:
            ``None`` or the unchanged validated value.

        Raises:
            ValueError: A supplied value is empty or untrimmed.
        """
        if value is None:
            return None
        return validate_non_empty(value, str(getattr(info, "field_name", "field")))

    @field_validator("payload", mode="before")
    @classmethod
    def _validate_payload(cls, value: object) -> Mapping[str, JsonValue]:
        """Validate, bound, and freeze a producer payload before parsing.

        Args:
            value: Candidate audit payload.

        Returns:
            A deeply immutable JSON-safe mapping.

        Raises:
            TypeError: The payload is not a string-keyed mapping.
            ValueError: The payload is unsafe, protected, or exceeds a bound.
        """
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
        """Restore deep immutability after Pydantic container validation.

        Args:
            value: Pydantic-validated payload mapping.

        Returns:
            A deeply immutable mapping proxy.

        Raises:
            TypeError: Validation unexpectedly produced a non-mapping value.
            ValueError: Revalidation detects an unsafe or oversized value.
        """
        frozen = _freeze_json(value, depth=0, item_count=[0])
        if not isinstance(frozen, Mapping):
            raise TypeError("payload must be a mapping")
        return frozen
