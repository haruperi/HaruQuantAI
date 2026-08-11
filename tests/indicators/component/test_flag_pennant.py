"""Component invariants for flag/pennant evidence."""

from tests.indicators.formula_invariants import (
    assert_formula_invariants,
    oscillating_bars,
)


def test_flag_pennant_is_deterministic_and_causal() -> None:
    """Preserve historical flag evidence under future extension."""
    assert_formula_invariants(
        "flag_pennant",
        {
            "atr_period": 3,
            "impulse_lookback": 3,
            "consolidation_bars": 3,
            "impulse_min_atr": 0.1,
            "retrace_max": 1.0,
            "beta_atr": 0.0,
        },
        bars=oscillating_bars(),
    )
