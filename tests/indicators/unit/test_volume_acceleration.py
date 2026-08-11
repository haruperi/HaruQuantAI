"""Focused invariants for volume acceleration."""

from tests.indicators.formula_invariants import assert_formula_invariants


def test_volume_acceleration_is_deterministic_and_causal() -> None:
    """Preserve historical volume acceleration under future extension."""
    assert_formula_invariants(
        "volume_acceleration", {"window": 3, "k": 2, "unit_seconds": 300.0}
    )
