"""Unit tests for the Donchian breakout regime classifier."""

from app.services.indicators import donchian_breakout_regime

from tests.indicators.helpers import assert_error, build_dataset, unwrap_response


def _range_bars(count: int = 40) -> list[tuple[float, float, float, float, float]]:
    """Build a ranging bar series."""
    return [(10.0, 10.5, 9.5, 10.0 + (i % 3) * 0.1, 100.0) for i in range(count)]


def test_donchian_breakout_regime_calculates_classification() -> None:
    """donchian_breakout_regime produces regime and breakout values."""
    data = build_dataset(_range_bars(40))
    result = unwrap_response(
        donchian_breakout_regime(data, period=20, atr_period=14, beta_atr=1.5)
    )
    assert result.indicator_id == "donchian_breakout_regime"
    assert any("breakout" in col for col in result.values.columns)


def test_donchian_breakout_regime_rejects_invalid_period() -> None:
    """Period less than 2 is rejected fail-fast."""
    data = build_dataset(_range_bars(20))
    assert_error(
        donchian_breakout_regime(data, period=1, atr_period=14, beta_atr=1.5),
        "IND_INVALID_PARAMETER",
    )
