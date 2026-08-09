"""Unit tests for EventEnvelope v1."""

from datetime import UTC, datetime

import pytest
from app.utils import build_event_envelope, parse_event_envelope
from app.utils.errors.exceptions import ValidationError


def test_integrity_hash_is_stable_and_tamper_evident() -> None:
    value = build_event_envelope(
        event_id="evt-1",
        source_id="sim",
        source_sequence=1,
        correlation_id="cor-1",
        causation_id=None,
        deduplication_key="key-1",
        emitted_at=datetime(2026, 1, 1, tzinfo=UTC),
        payload={"api_key": "secret", "value": 1},
    )  # pragma: allowlist secret
    assert parse_event_envelope(value) == value
    value["source_sequence"] = 2
    with pytest.raises(ValidationError):
        parse_event_envelope(value)
