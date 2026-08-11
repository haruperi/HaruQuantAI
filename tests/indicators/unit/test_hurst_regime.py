"""Focused invariants for Hurst regimes."""

from tests.indicators.formula_invariants import assert_formula_invariants


def test_hurst_regime_is_deterministic_and_causal() -> None:
    """Preserve historical Hurst regimes under future extension."""
    assert_formula_invariants(
        "hurst_regime",
        {
            "window": 16,
            "min_scale": 2,
            "max_scale": 8,
            "scale_count": 3,
            "lower_threshold": 0.45,
            "upper_threshold": 0.55,
        },
    )
