"""Unit tests for volatility/liquidity stress regime classifier."""

from app.services.indicators import volatility_liquidity_stress_regime

from tests.indicators.helpers import build_dataset, unwrap_response


def _stress_bars(count: int = 50) -> list[tuple[float, float, float, float, float]]:
    """Build volatile/illiquid bars."""
    return [
        (10.0, 15.0 + (i % 5), 5.0 - (i % 3), 11.0, 50.0 + i * 10) for i in range(count)
    ]


def test_volatility_liquidity_stress_regime_calculates_stress() -> None:
    """volatility_liquidity_stress_regime outputs stress level and regime."""
    data = build_dataset(_stress_bars(50))
    result = unwrap_response(
        volatility_liquidity_stress_regime(
            data,
            vol_reference_period=30,
            vol_period=10,
            amihud_window=10,
            p_vol_extreme=0.8,
            p_illiquidity_extreme=0.8,
            p_illiquidity_high=0.7,
        )
    )
    assert result.indicator_id == "volatility_liquidity_stress_regime"
    assert any("stress" in col for col in result.values.columns)
