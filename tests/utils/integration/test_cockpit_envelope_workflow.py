"""End-to-end Utils-owned cockpit-envelope workflow proof."""

from datetime import UTC, datetime

from app.utils import (
    build_event_envelope,
    build_exact_unit,
    build_profile_ref,
    is_duplicate_event,
    parse_event_envelope,
)


def test_redacted_unit_envelope_round_trips_and_deduplicates() -> None:
    """References, exact units, redaction, hashing, and duplicate checks compose."""
    profile = build_profile_ref(
        profile_kind="risk", profile_id="prf-1", version="1", content_hash="a" * 64
    )
    amount = build_exact_unit("100", kind="MONEY", currency="USD")
    envelope = build_event_envelope(
        event_id="evt-1",
        source_id="sim",
        source_sequence=1,
        correlation_id="cor-1",
        causation_id=None,
        deduplication_key="intent-1",
        emitted_at=datetime(2026, 1, 1, tzinfo=UTC),
        payload={"profile": profile, "amount": amount, "api_key": "synthetic-secret"},
    )  # pragma: allowlist secret
    assert parse_event_envelope(envelope)["payload"]["api_key"] == "[REDACTED]"  # type: ignore[index]
    assert is_duplicate_event(envelope, {"intent-1"})
