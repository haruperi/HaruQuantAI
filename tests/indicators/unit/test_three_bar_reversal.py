"""Focused invariants for three-bar reversal evidence."""

from tests.indicators.formula_invariants import (
    assert_formula_invariants,
    oscillating_bars,
)


def test_three_bar_reversal_is_deterministic_and_causal() -> None:
    """Preserve historical reversal evidence under future extension."""
    assert_formula_invariants(
        "three_bar_reversal",
        {"atr_period": 3, "body_min_atr": 0.1, "confirm_fraction": 0.5},
        bars=oscillating_bars(),
    )
