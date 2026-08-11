"""Component invariants for final regime resolution."""

from tests.indicators.formula_invariants import (
    assert_formula_invariants,
    oscillating_bars,
)


def test_final_regime_resolver_is_deterministic_and_causal() -> None:
    """Resolve component states without changing historical output."""
    assert_formula_invariants(
        "final_regime_resolver",
        {
            "adx_period": 3,
            "adx_trend": 25.0,
            "adx_range": 20.0,
            "chop_period": 3,
            "chop_lower_threshold": 38.2,
            "chop_upper_threshold": 61.8,
            "donchian_period": 3,
            "atr_period": 3,
            "beta_atr": 0.0,
            "vol_reference_period": 5,
            "vol_period": 3,
            "amihud_window": 3,
            "p_vol_extreme": 0.8,
            "p_illiquidity_extreme": 0.8,
            "p_illiquidity_high": 0.6,
        },
        bars=oscillating_bars()[:12],
    )
