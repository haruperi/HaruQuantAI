"""Component invariants for double-top and double-bottom evidence."""

from tests.indicators.formula_invariants import (
    assert_formula_invariants,
    oscillating_bars,
)


def test_double_top_bottom_is_deterministic_and_causal() -> None:
    """Preserve confirmed swing evidence when future bars are appended."""
    assert_formula_invariants(
        "double_top_bottom",
        {
            "left": 1,
            "right": 1,
            "atr_period": 3,
            "tau_price": 0.2,
            "d_min_atr": 0.1,
            "beta_atr": 0.0,
            "m_confirm": 5,
        },
        bars=oscillating_bars(),
    )
