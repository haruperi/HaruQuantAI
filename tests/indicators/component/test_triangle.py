"""Component invariants for triangle evidence."""

from tests.indicators.formula_invariants import (
    assert_formula_invariants,
    oscillating_bars,
)


def _converging_bars() -> list[tuple[float, float, float, float, float]]:
    """Return bars whose alternating extrema converge over time."""
    closes = [100.0 + ((-1.0) ** index) * (8.0 - index * 0.15) for index in range(40)]
    return [(close - 0.2, close + 0.8, close - 0.8, close, 1_000.0) for close in closes]


def test_triangle_is_deterministic_and_causal() -> None:
    """Keep fitted triangle history invariant when bars are appended."""
    assert_formula_invariants(
        "triangle",
        {
            "left": 1,
            "right": 1,
            "atr_period": 3,
            "lookback": 10,
            "min_touches": 2,
            "slope_flat": 0.1,
            "beta_atr": 0.0,
        },
        bars=oscillating_bars(),
    )


def test_triangle_recognizes_converging_boundaries() -> None:
    """Exercise the fitted converging-boundary classification branch."""
    assert_formula_invariants(
        "triangle",
        {
            "left": 1,
            "right": 1,
            "atr_period": 3,
            "lookback": 20,
            "min_touches": 2,
            "slope_flat": 0.1,
            "beta_atr": 0.0,
        },
        bars=_converging_bars(),
    )
