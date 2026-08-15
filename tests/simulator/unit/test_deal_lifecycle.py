"""Unit evidence for deterministic deal and transaction linkage."""

from datetime import UTC, datetime
from decimal import Decimal

from app.services.simulator.accounting.transactions import build_posting
from app.services.simulator.execution.lifecycle import build_lifecycle_deal


def test_deal_links_order_position_fees_and_transaction() -> None:
    """A lifecycle deal is stable and carries every required foreign key."""
    fields = {
        "order_id": "order-1",
        "position_id": "position-1",
        "side": "BUY",
        "quantity": Decimal(1),
        "price": Decimal("1.1"),
        "entry": "DEAL_ENTRY_IN",
        "reason": "EXPERT",
        "occurred_at": datetime(2026, 8, 17, tzinfo=UTC),
        "source_sequence": 4,
        "fee_evidence": {"commission": Decimal(-1)},
    }
    first = build_lifecycle_deal(**fields)  # type: ignore[arg-type]
    second = build_lifecycle_deal(**fields)  # type: ignore[arg-type]
    assert first == second
    assert first["order_id"] == "order-1"
    assert first["position_id"] == "position-1"
    assert first["entry"] == "DEAL_ENTRY_IN"
    posting = build_posting(
        economic_at=fields["occurred_at"],
        source_at=fields["occurred_at"],
        account_currency="USD",
        amount=Decimal(-1),
        kind="commission",
        source_sequence=4,
        evidence_reference=str(first["deal_id"]),
        causal_deal_id=str(first["deal_id"]),
        causal_order_id="order-1",
        causal_position_id="position-1",
    )
    assert posting.causal_deal_id == first["deal_id"]
