from app.services.indicators import measure_trend_strength


def test_trend_strength_is_strategy_independent() -> None:
    result = measure_trend_strength(
        adx_value=30.0,
        positive_directional=25.0,
        negative_directional=10.0,
        fast_average=101.0,
        slow_average=100.0,
        strength_threshold=25.0,
    )
    assert result.data == {"direction": "UP", "strength": "STRONG", "adx": 30.0}


def test_trend_strength_covers_down_flat_and_invalid_states() -> None:
    down = measure_trend_strength(
        adx_value=10.0,
        positive_directional=5.0,
        negative_directional=10.0,
        fast_average=99.0,
        slow_average=100.0,
        strength_threshold=25.0,
    )
    flat = measure_trend_strength(
        adx_value=10.0,
        positive_directional=5.0,
        negative_directional=5.0,
        fast_average=100.0,
        slow_average=100.0,
        strength_threshold=25.0,
    )
    invalid = measure_trend_strength(
        adx_value=10.0,
        positive_directional=5.0,
        negative_directional=5.0,
        fast_average=100.0,
        slow_average=100.0,
        strength_threshold=-1.0,
    )
    assert down.data["direction"] == "DOWN"
    assert down.data["strength"] == "WEAK"
    assert flat.data["direction"] == "FLAT"
    assert invalid.status == "error"
