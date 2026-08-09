from datetime import UTC, datetime, timedelta

from app.services.indicators import build_indicator_snapshot, parse_indicator_snapshot


def test_indicator_snapshot_v1_producer_consumer_compatibility() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    produced = build_indicator_snapshot(
        indicator_id="atr",
        value=1.0,
        unit="price",
        state="AVAILABLE",
        observed_at=now,
        source_start=now - timedelta(hours=2),
        source_end=now - timedelta(hours=1),
        complete=True,
        confidence=1.0,
        data_health="HEALTHY",
    )
    consumed = parse_indicator_snapshot(produced.data)
    assert consumed.data == produced.data
