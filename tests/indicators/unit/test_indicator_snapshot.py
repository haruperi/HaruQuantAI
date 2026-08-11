from datetime import UTC, datetime

from app.services.indicators import (
    build_indicator_snapshot,
    parse_indicator_snapshot,
)
from app.services.indicators.snapshots.snapshot import evaluate_publication_state

NOW = datetime(2026, 1, 1, 12, tzinfo=UTC)


def test_indicator_snapshot_round_trip_and_rejects_lookahead() -> None:
    built = build_indicator_snapshot(
        indicator_id="atr",
        value=1.25,
        unit="price",
        state="AVAILABLE",
        observed_at=NOW,
        source_start=NOW.replace(hour=10),
        source_end=NOW.replace(hour=11),
        complete=True,
        confidence=1.0,
        data_health="HEALTHY",
        evidence_refs=("dataset-1",),
    )
    assert built.status == "success"
    parsed = parse_indicator_snapshot(built.data)
    assert parsed.status == "success"
    assert parsed.data == built.data

    invalid = build_indicator_snapshot(
        indicator_id="atr",
        value=1.25,
        unit="price",
        state="AVAILABLE",
        observed_at=NOW,
        source_start=NOW.replace(hour=10),
        source_end=NOW.replace(hour=13),
        complete=True,
        confidence=1.0,
        data_health="HEALTHY",
    )
    assert invalid.error.code == "IND_LOOKAHEAD_RISK"


def test_indicator_snapshot_rejects_invalid_transport_fields() -> None:
    base = {
        "schema": "indicators.indicator_snapshot.v1",
        "indicator_id": "atr",
        "value": 1.0,
        "unit": "price",
        "state": "AVAILABLE",
        "observed_at": "2026-01-01T12:00:00Z",
        "source_start": "2026-01-01T10:00:00Z",
        "source_end": "2026-01-01T11:00:00Z",
        "complete": True,
        "confidence": 1.0,
        "data_health": "HEALTHY",
        "evidence_refs": [],
    }
    cases = (
        dict(base, schema="unknown"),
        dict(base, indicator_id=""),
        dict(base, value=float("inf")),
        dict(base, confidence=2.0),
        dict(base, complete="yes"),
        dict(base, evidence_refs=[""]),
        dict(base, observed_at="not-a-timeZ"),
        dict(base, source_start="2026-01-01T10:00:00+01:00"),
    )
    for case in cases:
        assert parse_indicator_snapshot(case).status == "error"


def test_publication_state_uses_declared_fail_closed_priority() -> None:
    """Return every publication state from its ordered triggering condition."""
    names = (
        "any_source_after_as_of",
        "required_bar_not_closed",
        "required_source_stale",
        "timeframe_misaligned",
        "warmup_insufficient",
        "dependency_unavailable",
    )
    expected = (
        "INVALID_FUTURE_INPUT",
        "INCOMPLETE_INPUT",
        "STALE_INPUT",
        "MISALIGNED_INPUT",
        "WARMING_UP",
        "DEPENDENCY_UNAVAILABLE",
    )
    defaults = dict.fromkeys(names, False)
    for name, state in zip(names, expected, strict=True):
        response = evaluate_publication_state(**(defaults | {name: True}))
        assert response.data == state
    assert evaluate_publication_state(**defaults).data == "VALID"
