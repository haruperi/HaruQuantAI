from datetime import UTC, datetime

from app.services.indicators import (
    build_chart_pattern_evidence,
    build_liquidity_snapshot,
    measure_market_speed,
    parse_liquidity_snapshot,
)


def test_cockpit_measurements_remain_advisory_and_json_safe() -> None:
    speed = measure_market_speed(
        {
            "momentum": 1.0,
            "realized_volatility": 1.0,
            "range_expansion": 1.0,
            "volume_acceleration": 1.0,
            "order_flow_velocity": 1.0,
        },
        thresholds=(0.5, 1.5, 2.5),
    )
    liquidity = build_liquidity_snapshot(
        observed_at=datetime(2026, 1, 1, tzinfo=UTC),
        spread=0.1,
        executable_depth=100.0,
        imbalance=0.0,
        volume=100.0,
        fill_probability=None,
        regime="NORMAL",
        complete=False,
    )
    patterns = build_chart_pattern_evidence(
        {"doji": 1}, observed_at=datetime(2026, 1, 1, tzinfo=UTC)
    )
    assert speed.data["state"] == "NORMAL"
    assert parse_liquidity_snapshot(liquidity.data).data == liquidity.data
    assert patterns.data["authorizes_trade"] is False
