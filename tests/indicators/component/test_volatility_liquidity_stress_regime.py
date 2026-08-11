"""Component invariants for volatility/liquidity stress regimes."""

from tests.indicators.formula_invariants import assert_formula_invariants


def test_stress_regime_is_deterministic_and_causal() -> None:
    """Preserve historical stress regimes under future extension."""
    assert_formula_invariants(
        "volatility_liquidity_stress_regime",
        {
            "vol_reference_period": 5,
            "vol_period": 3,
            "amihud_window": 3,
            "p_vol_extreme": 0.8,
            "p_illiquidity_extreme": 0.8,
            "p_illiquidity_high": 0.6,
        },
    )
