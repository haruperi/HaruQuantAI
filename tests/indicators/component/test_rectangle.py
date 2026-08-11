"""Component invariants for rectangle evidence."""

from tests.indicators.formula_invariants import (
    assert_formula_invariants,
    oscillating_bars,
)


def test_rectangle_is_deterministic_and_causal() -> None:
    """Keep fitted rectangle history invariant when bars are appended."""
    assert_formula_invariants(
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
        bars=oscillating_bars(),
    )
