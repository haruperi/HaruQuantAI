"""Netting and hedging margin tests."""

from decimal import Decimal

from app.services.simulator import (
    calculate_planned_margin,
    calculate_total_margin,
    unwrap_simulation_response,
)

from tests.simulator.unit.calculations.test_profit import NOW, revision


def margin(function: object, **overrides: object) -> Decimal:
    """Return one unwrapped margin result."""
    fields: dict[str, object] = {
        "position_mode": "NETTING",
        "existing_long": Decimal(1),
        "existing_short": Decimal(0),
        "planned_side": "SELL",
        "planned_volume": Decimal("0.25"),
        "as_of": NOW,
        "fx_evidence": None,
    }
    fields.update(overrides)
    return unwrap_simulation_response(
        function(revision(), **fields),  # type: ignore[operator]
        operation="test.margin",
    )


def test_netting_margin_accounts_for_existing_exposure() -> None:
    """Opposing planned volume reduces total and incremental margin."""
    assert margin(calculate_total_margin) == Decimal("750.00")
    assert margin(calculate_planned_margin) == Decimal("0.00")


def test_hedging_margin_uses_explicit_hedged_rate() -> None:
    """Hedged overlap uses the specification rate and uncovered base margin."""
    assert margin(
        calculate_total_margin,
        position_mode="HEDGING",
        planned_volume=Decimal("0.5"),
    ) == Decimal("750.00")
