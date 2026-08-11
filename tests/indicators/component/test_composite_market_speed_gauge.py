"""Component invariants for the composite market-speed gauge."""

from tests.indicators.formula_invariants import (
    assert_formula_invariants,
    oscillating_bars,
)


def test_composite_market_speed_gauge_is_deterministic_and_causal() -> None:
    """Preserve historical composite speed under future extension."""
    assert_formula_invariants(
        "composite_market_speed_gauge",
        {
            "k": 2,
            "unit_seconds": 300.0,
            "volume_window": 3,
            "atr_period": 3,
            "z_window": 3,
            "z_max": 3.0,
            "weight_price_velocity": 0.25,
            "weight_momentum_acceleration": 0.25,
            "weight_volume_acceleration": 0.25,
            "weight_volatility_expansion": 0.25,
        },
        bars=oscillating_bars()[:12],
    )
