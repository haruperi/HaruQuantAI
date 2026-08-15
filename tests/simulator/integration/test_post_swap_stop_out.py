"""Integration evidence for post-swap stop-out ordering and conservation."""

from decimal import Decimal

from app.services.simulator.accounting.stop_out import (
    get_margin_state,
    plan_stop_out_liquidation,
)


def test_swap_is_applied_before_target_evidenced_stop_out() -> None:
    """Post-swap equity triggers the evidenced liquidation sequence."""
    balance = Decimal(100)
    swap = Decimal(-60)
    assert (
        get_margin_state(
            equity=balance + swap,
            used_margin=Decimal(100),
            margin_call_level=Decimal(80),
            stop_out_level=Decimal(50),
            mode="PERCENT",
        )
        == "STOP_OUT"
    )
    positions = (
        {"position_id": "p1", "profit": Decimal(-10), "opened_at": "2026-01-01"},
        {"position_id": "p2", "profit": Decimal(-20), "opened_at": "2026-01-02"},
    )
    assert plan_stop_out_liquidation(
        positions,
        ordering="WORST_LOSS_FIRST",
        target_evidence_reference="mt5-demo-fixture",
    ) == ("p2", "p1")
