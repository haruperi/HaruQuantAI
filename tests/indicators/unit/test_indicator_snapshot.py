from datetime import UTC, datetime

from app.services.indicators import build_indicator_snapshot, parse_indicator_snapshot

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
