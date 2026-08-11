"""Focused invariants for volatility expansion rate."""

from tests.indicators.formula_invariants import assert_formula_invariants


def test_volatility_expansion_rate_is_deterministic_and_causal() -> None:
    """Preserve historical volatility expansion under future extension."""
    assert_formula_invariants(
        "volatility_expansion_rate", {"atr_period": 3, "k": 2, "unit_seconds": 300.0}
    )
