"""Component invariants for Donchian breakout regimes."""

from tests.indicators.formula_invariants import assert_formula_invariants


def test_donchian_breakout_regime_is_deterministic_and_causal() -> None:
    """Preserve historical breakout regimes under future extension."""
    assert_formula_invariants(
        "donchian_breakout_regime", {"period": 3, "atr_period": 3, "beta_atr": 0.0}
    )
