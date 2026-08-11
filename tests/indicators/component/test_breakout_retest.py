"""Component invariants for breakout/retest evidence."""

from tests.indicators.formula_invariants import (
    assert_formula_invariants,
    oscillating_bars,
)


def test_breakout_retest_is_deterministic_and_causal() -> None:
    """Keep breakout/retest history invariant when bars are appended."""
    assert_formula_invariants(
        "breakout_retest",
        {
            "left": 1,
            "right": 1,
            "atr_period": 3,
            "beta_atr": 0.0,
            "tau_price": 1.0,
            "m": 5,
        },
        bars=oscillating_bars(),
    )
