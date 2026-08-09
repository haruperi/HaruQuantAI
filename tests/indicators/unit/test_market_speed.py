from app.services.indicators import measure_market_speed


def test_market_speed_uses_all_explicit_components() -> None:
    result = measure_market_speed(
        {
            "momentum": 2.0,
            "realized_volatility": 2.0,
            "range_expansion": 2.0,
            "volume_acceleration": 2.0,
            "order_flow_velocity": 2.0,
        },
        thresholds=(0.5, 1.5, 3.0),
    )
    assert result.data["state"] == "FAST"
    assert result.data["score"] == 2.0


def test_market_speed_rejects_incomplete_and_invalid_evidence() -> None:
    assert measure_market_speed({}, thresholds=(0.5, 1.5, 3.0)).status == "error"
    invalid = {
        "momentum": -1.0,
        "realized_volatility": 1.0,
        "range_expansion": 1.0,
        "volume_acceleration": 1.0,
        "order_flow_velocity": 1.0,
    }
    assert measure_market_speed(invalid, thresholds=(0.5, 1.5, 3.0)).status == "error"
    valid = dict(invalid, momentum=1.0)
    assert measure_market_speed(valid, thresholds=(1.0, 1.0, 3.0)).status == "error"
    assert (
        measure_market_speed(valid, thresholds=(1.5, 2.0, 3.0)).data["state"] == "SLOW"
    )
    assert (
        measure_market_speed(valid, thresholds=(0.2, 0.5, 0.8)).data["state"]
        == "EXTREME"
    )
