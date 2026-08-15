"""Unit evidence for internal protection and OCO semantics."""

from decimal import Decimal

from app.services.simulator.execution.lifecycle import build_protection_projection


def test_protection_is_not_an_ordinary_pending_order() -> None:
    """Winning SL/TP evidence cancels its sibling without exposing an order."""
    protection = build_protection_projection(
        position_id="position-1",
        stop_loss=Decimal("1.09"),
        take_profit=Decimal("1.12"),
        triggered_reason="STOP_LOSS",
    )
    assert protection["exposed_as_pending_order"] is False
    assert protection["oco_cancelled_reason"] == "TAKE_PROFIT"
