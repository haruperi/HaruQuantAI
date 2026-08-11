"""Focused invariants for market-event arrival rate."""

from tests.indicators.formula_invariants import assert_formula_invariants


def test_market_event_arrival_rate_is_deterministic_and_causal() -> None:
    """Preserve historical event-rate output under future extension."""
    assert_formula_invariants("market_event_arrival_rate", {"window_seconds": 900.0})
