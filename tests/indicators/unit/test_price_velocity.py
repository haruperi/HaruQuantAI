"""Focused invariants for price velocity."""

from tests.indicators.formula_invariants import assert_formula_invariants


def test_price_velocity_is_deterministic_and_causal() -> None:
    """Preserve historical velocity under future extension."""
    assert_formula_invariants("price_velocity", {"k": 2, "unit_seconds": 300.0})
