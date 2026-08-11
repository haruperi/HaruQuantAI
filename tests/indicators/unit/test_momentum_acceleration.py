"""Focused invariants for momentum acceleration."""

from tests.indicators.formula_invariants import assert_formula_invariants


def test_momentum_acceleration_is_deterministic_and_causal() -> None:
    """Preserve historical acceleration under future extension."""
    assert_formula_invariants("momentum_acceleration", {"k": 2, "unit_seconds": 300.0})
