"""Component invariants for Amihud illiquidity."""

from tests.indicators.formula_invariants import assert_formula_invariants


def test_amihud_illiquidity_is_deterministic_and_causal() -> None:
    """Preserve historical illiquidity under future extension."""
    assert_formula_invariants("amihud_illiquidity", {"window": 3})
