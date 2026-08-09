"""Versioned event-envelope transport with redaction and integrity evidence."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from datetime import UTC, datetime

from app.utils.errors.exceptions import ValidationError
from app.utils.security import redact_contract_mapping
from app.utils.serialization import canonical_digest, to_json_safe

_FIELDS = {
    "contract_version",
    "schema_id",
    "event_id",
    "source_id",
    "source_sequence",
    "correlation_id",
    "causation_id",
    "deduplication_key",
    "integrity_hash",
    "emitted_at",
    "payload",
}


def build_event_envelope(
    *,
    event_id: str,
    source_id: str,
    source_sequence: int,
    correlation_id: str,
    causation_id: str | None,
    deduplication_key: str,
    emitted_at: datetime,
    payload: Mapping[str, object],
) -> dict[str, object]:
    """Build and hash a redacted EventEnvelope v1 mapping.

    Args:
        event_id: Event identifier.
        source_id: Producer identifier.
        source_sequence: Monotonic source sequence.
        correlation_id: Correlation identifier.
        causation_id: Optional causation identifier.
        deduplication_key: Caller-derived duplicate key.
        emitted_at: Aware UTC emission instant.
        payload: Opaque domain payload.

    Returns:
        EventEnvelope v1 mapping.

    Raises:
        ValidationError: If evidence is invalid.
    """
    if (
        not all((event_id, source_id, correlation_id, deduplication_key))
        or isinstance(source_sequence, bool)
        or source_sequence < 0
        or emitted_at.tzinfo is None
        or emitted_at.utcoffset() != UTC.utcoffset(emitted_at)
    ):
        raise ValidationError("EVENT_ENVELOPE_INVALID")
    envelope: dict[str, object] = {
        "contract_version": "v1",
        "schema_id": "utils.event_envelope.v1",
        "event_id": event_id,
        "source_id": source_id,
        "source_sequence": source_sequence,
        "correlation_id": correlation_id,
        "causation_id": causation_id,
        "deduplication_key": deduplication_key,
        "emitted_at": emitted_at.isoformat().replace("+00:00", "Z"),
        "payload": redact_contract_mapping(payload),
    }
    envelope["integrity_hash"] = canonical_digest(envelope)
    return envelope


def parse_event_envelope(value: Mapping[str, object]) -> dict[str, object]:
    """Validate an EventEnvelope v1 mapping and integrity hash.

    Args:
        value: Candidate mapping.

    Returns:
        Validated detached envelope.

    Raises:
        ValidationError: If version, shape, or hash is invalid.
    """
    if (
        set(value) != _FIELDS
        or value.get("contract_version") != "v1"
        or value.get("schema_id") != "utils.event_envelope.v1"
    ):
        raise ValidationError("EVENT_ENVELOPE_VERSION_INCOMPATIBLE")
    expected_hash = value.get("integrity_hash")
    unhashed = {key: value[key] for key in value if key != "integrity_hash"}
    if (
        not isinstance(expected_hash, str)
        or canonical_digest(unhashed) != expected_hash
    ):
        raise ValidationError("EVENT_ENVELOPE_INTEGRITY_INVALID")
    emitted, payload = value.get("emitted_at"), value.get("payload")
    source_sequence = value.get("source_sequence")
    if (
        not isinstance(emitted, str)
        or not isinstance(payload, Mapping)
        or not isinstance(source_sequence, int)
        or isinstance(source_sequence, bool)
    ):
        raise ValidationError("EVENT_ENVELOPE_INVALID")
    rebuilt = build_event_envelope(
        event_id=str(value["event_id"]),
        source_id=str(value["source_id"]),
        source_sequence=source_sequence,
        correlation_id=str(value["correlation_id"]),
        causation_id=None
        if value["causation_id"] is None
        else str(value["causation_id"]),
        deduplication_key=str(value["deduplication_key"]),
        emitted_at=datetime.fromisoformat(emitted),
        payload=payload,
    )
    safe: object = to_json_safe(rebuilt)
    if not isinstance(safe, dict):
        raise ValidationError("EVENT_ENVELOPE_INVALID")
    return dict(safe)


def is_duplicate_event(
    value: Mapping[str, object], observed_keys: Collection[str]
) -> bool:
    """Return whether a validated event key was already observed.

    Args:
        value: EventEnvelope mapping.
        observed_keys: Caller-owned observed key set.

    Returns:
        Whether the event is a duplicate.
    """
    return str(parse_event_envelope(value)["deduplication_key"]) in observed_keys


def find_sequence_gap(
    value: Mapping[str, object], *, expected_sequence: int
) -> dict[str, int] | None:
    """Report a gap without buffering or reordering the event.

    Args:
        value: EventEnvelope mapping.
        expected_sequence: Expected successor sequence.

    Returns:
        Gap details or None.

    Raises:
        ValidationError: If sequence evidence is malformed.
    """
    raw_actual = parse_event_envelope(value)["source_sequence"]
    if not isinstance(raw_actual, int) or isinstance(raw_actual, bool):
        raise ValidationError("EVENT_ENVELOPE_INVALID")
    actual = raw_actual
    if actual <= expected_sequence:
        return None
    return {
        "expected_sequence": expected_sequence,
        "actual_sequence": actual,
        "missing_count": actual - expected_sequence,
    }
