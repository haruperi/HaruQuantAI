"""Focused invariants for choppiness regimes."""

from tests.indicators.formula_invariants import assert_formula_invariants


def test_choppiness_regime_is_deterministic_and_causal() -> None:
    """Preserve historical choppiness regimes under future extension."""
    assert_formula_invariants(
        "choppiness_regime",
        {"period": 3, "lower_threshold": 38.2, "upper_threshold": 61.8},
    )
