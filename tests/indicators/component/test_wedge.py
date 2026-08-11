"""Component invariants for wedge evidence."""

from tests.indicators.formula_invariants import (
    assert_formula_invariants,
    oscillating_bars,
)


def test_wedge_is_deterministic_and_causal() -> None:
    """Keep fitted wedge history invariant when bars are appended."""
    assert_formula_invariants(
        "wedge",
        {
            "left": 1,
            "right": 1,
            "atr_period": 3,
            "lookback": 10,
            "min_touches": 2,
            "beta_atr": 0.0,
        },
        bars=oscillating_bars(),
    )
