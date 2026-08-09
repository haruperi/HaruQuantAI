"""Ordered, deduplicated broker EventEnvelope normalization (``TC-IMP-BRK-11``).

The Trading Cockpit Phase 0 reconciliation requires converting adapter
callbacks and polls into ordered, deduplicated ``EventEnvelope`` records. The
``EventEnvelope`` contract (schema ``utils.event_envelope.v1``) is owned by
Utils and consumed here through its public ``build_event_envelope``,
``is_duplicate_event``, and ``find_sequence_gap`` functions.

This module is a pure consumer: it does not buffer, reorder, or discard events.
It derives the envelope metadata from broker evidence, delegates duplicate and
gap detection to Utils, and returns a normalized envelope plus ordering
evidence so the caller can decide how to handle a gap or duplicate.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from datetime import datetime

from app.utils import (
    build_event_envelope,
    find_sequence_gap,
    is_duplicate_event,
)


def normalize_broker_event_envelope(
    *,
    source_id: str,
    source_sequence: int,
    event_id: str,
    correlation_id: str,
    causation_id: str | None,
    emitted_at: datetime,
    event_type: str,
    broker: str,
    payload: Mapping[str, object],
) -> dict[str, object]:
    """Normalize one broker event into a redacted EventEnvelope v1 mapping.

    Args:
        source_id: Producer identifier (broker + subscription).
        source_sequence: Monotonic producer sequence.
        event_id: Stable event identifier.
        correlation_id: Correlation identifier.
        causation_id: Optional causation identifier.
        emitted_at: Aware UTC emission instant.
        event_type: Broker event type label.
        broker: Owning broker identifier.
        payload: Opaque broker event payload.

    Returns:
        EventEnvelope v1 mapping carrying the broker payload.
    """
    envelope = build_event_envelope(
        event_id=event_id,
        source_id=source_id,
        source_sequence=source_sequence,
        correlation_id=correlation_id,
        causation_id=causation_id,
        deduplication_key=f"{broker}:{event_type}:{event_id}",
        emitted_at=emitted_at,
        payload={
            "event_type": event_type,
            "broker": broker,
            "data": dict(payload),
        },
    )
    return envelope


def classify_broker_event(
    *,
    envelope: Mapping[str, object],
    observed_keys: Collection[str],
    expected_sequence: int,
) -> dict[str, object]:
    """Classify one broker event envelope for duplicates and ordering gaps.

    The classifier delegates duplicate and gap detection to Utils. It never
    buffers, reorders, or discards the envelope; it returns the verdict so the
    caller can apply its own delivery policy.

    Args:
        envelope: EventEnvelope mapping produced by normalization.
        observed_keys: Caller-owned observed deduplication-key set.
        expected_sequence: Expected successor sequence.

    Returns:
        Classification mapping with ``is_duplicate`` and ``gap`` evidence.
    """
    is_duplicate = is_duplicate_event(envelope, observed_keys)
    gap = find_sequence_gap(envelope, expected_sequence=expected_sequence)
    return {
        "is_duplicate": is_duplicate,
        "gap": gap,
    }


__all__ = [
    "classify_broker_event",
    "normalize_broker_event_envelope",
]
