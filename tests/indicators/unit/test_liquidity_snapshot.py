from datetime import UTC, datetime

from app.services.indicators import build_liquidity_snapshot, parse_liquidity_snapshot


def test_liquidity_snapshot_round_trip_preserves_unknown_probability() -> None:
    result = build_liquidity_snapshot(
        observed_at=datetime(2026, 1, 1, tzinfo=UTC),
        spread=0.2,
        executable_depth=100.0,
        imbalance=0.1,
        volume=250.0,
        fill_probability=None,
        regime="NORMAL",
        complete=False,
    )
    parsed = parse_liquidity_snapshot(result.data)
    assert parsed.data["fill_probability"] is None
    assert parsed.data["complete"] is False


def test_liquidity_snapshot_rejects_invalid_transport_fields() -> None:
    base = {
        "schema": "indicators.liquidity_snapshot.v1",
        "observed_at": "2026-01-01T00:00:00Z",
        "spread": 0.1,
        "executable_depth": 1.0,
        "imbalance": 0.0,
        "volume": 1.0,
        "fill_probability": None,
        "regime": "NORMAL",
        "complete": True,
    }
    cases = (
        dict(base, schema="unknown"),
        dict(base, observed_at="invalidZ"),
        dict(base, spread=float("nan")),
        dict(base, volume=-1.0),
        dict(base, imbalance=2.0),
        dict(base, fill_probability=2.0),
        dict(base, regime=""),
        dict(base, complete="yes"),
    )
    for case in cases:
        assert parse_liquidity_snapshot(case).status == "error"
