"""Unit tests for the final regime resolver."""

import pytest
from app.services.indicators import final_regime_resolver

from tests.indicators.helpers import build_dataset, unwrap_response


def _mixed_bars(count: int = 10) -> list[tuple[float, float, float, float, float]]:
    """Build mixed price bars for regime classification."""
    return [
        (10.0 + i * 0.1, 10.5 + i * 0.12, 9.5 + i * 0.08, 10.2 + i * 0.1, 100.0)
        for i in range(count)
    ]


_PARAMS = {
    "adx_period": 3,
    "adx_trend": 25.0,
    "adx_range": 20.0,
    "chop_period": 3,
    "chop_lower_threshold": 38.2,
    "chop_upper_threshold": 61.8,
    "donchian_period": 3,
    "atr_period": 3,
    "beta_atr": 1.5,
    "vol_reference_period": 5,
    "vol_period": 2,
    "amihud_window": 2,
    "p_vol_extreme": 0.8,
    "p_illiquidity_extreme": 0.8,
    "p_illiquidity_high": 0.7,
}


@pytest.fixture(autouse=True)
def _prewarm_resolver_caches() -> None:
    """Pre-warm calculation and pandas caches during setup phase."""
    data = build_dataset(_mixed_bars(10))
    final_regime_resolver(data, **_PARAMS)


def test_final_regime_resolver_calculates_regime_consensus() -> None:
    """final_regime_resolver combines trend, choppiness, hurst, breakout, and stress."""
    data = build_dataset(_mixed_bars(10))
    result = unwrap_response(final_regime_resolver(data, **_PARAMS))
    assert result.indicator_id == "final_regime_resolver"
    assert any("regime" in col for col in result.values.columns)
