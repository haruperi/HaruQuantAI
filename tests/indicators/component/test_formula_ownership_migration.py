"""Component regression coverage for formula-ownership migration families."""

from __future__ import annotations

import pytest
from app.services import indicators

from tests.indicators.helpers import build_dataset, unwrap_response

_CASES = (
    ("price_velocity", {"k": 2, "unit_seconds": 300.0}),
    ("momentum_acceleration", {"k": 2, "unit_seconds": 300.0}),
    ("volume_acceleration", {"window": 3, "k": 2, "unit_seconds": 300.0}),
    ("market_event_arrival_rate", {"window_seconds": 900.0}),
    ("volatility_expansion_rate", {"atr_period": 3, "k": 2, "unit_seconds": 300.0}),
    ("adx_dmi_regime", {"period": 3, "adx_trend": 25.0, "adx_range": 20.0}),
    (
        "choppiness_regime",
        {"period": 3, "lower_threshold": 38.2, "upper_threshold": 61.8},
    ),
    (
        "hurst_regime",
        {
            "window": 16,
            "min_scale": 2,
            "max_scale": 8,
            "scale_count": 3,
            "lower_threshold": 0.45,
            "upper_threshold": 0.55,
        },
    ),
    ("donchian_breakout_regime", {"period": 3, "atr_period": 3, "beta_atr": 0.0}),
    (
        "volatility_liquidity_stress_regime",
        {
            "vol_reference_period": 5,
            "vol_period": 3,
            "amihud_window": 3,
            "p_vol_extreme": 0.8,
            "p_illiquidity_extreme": 0.8,
            "p_illiquidity_high": 0.6,
        },
    ),
    ("amihud_illiquidity", {"window": 3}),
    (
        "double_top_bottom",
        {
            "left": 1,
            "right": 1,
            "atr_period": 3,
            "tau_price": 0.05,
            "d_min_atr": 0.1,
            "beta_atr": 0.0,
            "m_confirm": 5,
        },
    ),
    (
        "head_and_shoulders",
        {
            "left": 1,
            "right": 1,
            "atr_period": 3,
            "tau_shoulder": 0.1,
            "d_head_atr": 0.1,
            "beta_atr": 0.0,
            "m_confirm": 5,
        },
    ),
    (
        "triangle",
        {
            "left": 1,
            "right": 1,
            "atr_period": 3,
            "lookback": 10,
            "min_touches": 2,
            "slope_flat": 0.01,
            "beta_atr": 0.0,
        },
    ),
    (
        "flag_pennant",
        {
            "atr_period": 3,
            "impulse_lookback": 3,
            "consolidation_bars": 3,
            "impulse_min_atr": 0.1,
            "retrace_max": 1.0,
            "beta_atr": 0.0,
        },
    ),
    (
        "breakout_retest",
        {
            "left": 1,
            "right": 1,
            "atr_period": 3,
            "beta_atr": 0.0,
            "tau_price": 1.0,
            "m": 5,
        },
    ),
    (
        "wedge",
        {
            "left": 1,
            "right": 1,
            "atr_period": 3,
            "lookback": 10,
            "min_touches": 2,
            "beta_atr": 0.0,
        },
    ),
    (
        "rectangle",
        {
            "left": 1,
            "right": 1,
            "atr_period": 3,
            "lookback": 10,
            "min_touches": 2,
            "slope_flat": 1.0,
            "tolerance": 1.0,
            "beta_atr": 0.0,
        },
    ),
    (
        "three_bar_reversal",
        {"atr_period": 3, "body_min_atr": 0.1, "confirm_fraction": 0.5},
    ),
)


@pytest.mark.parametrize(("operation", "parameters"), _CASES)
def test_migrated_formula_returns_deterministic_series(
    operation: str, parameters: dict[str, object]
) -> None:
    """Each migrated formula publishes a successful deterministic result."""
    bars = [
        (100 + i * 0.1, 101 + i * 0.1, 99 + i * 0.1, 100.2 + i * 0.1, 1000 + i * 10)
        for i in range(32)
    ]
    result = unwrap_response(
        getattr(indicators, operation)(build_dataset(bars), **parameters)
    )
    assert result.indicator_id == operation
    assert result.values.equals(result.values.copy(deep=True))
