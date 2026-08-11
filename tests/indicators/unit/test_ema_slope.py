"""Unit tests for the EMA slope indicator."""

from app.services.indicators import ema_slope

from tests.indicators.helpers import assert_error, build_dataset, unwrap_response


def _slope_bars(count: int = 40) -> list[tuple[float, float, float, float, float]]:
    """Build price bars with upward trend for slope calculation."""
    return [(10.0 + i, 11.0 + i, 9.5 + i, 10.5 + i, 100.0) for i in range(count)]


def test_ema_slope_calculates_slope_values() -> None:
    """ema_slope calculates EMA and slope degrees/rate."""
    data = build_dataset(_slope_bars(40))
    result = unwrap_response(ema_slope(data, period=10, lag=1, atr_period=14))
    assert result.indicator_id == "ema_slope"
    assert any("slope" in col for col in result.values.columns)


def test_ema_slope_rejects_invalid_period() -> None:
    """Period less than 2 is rejected fail-fast."""
    data = build_dataset(_slope_bars(20))
    assert_error(
        ema_slope(data, period=1, lag=1, atr_period=14), "IND_INVALID_PARAMETER"
    )
