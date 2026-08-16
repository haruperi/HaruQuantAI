"""Trading-compatible Simulation authority evidence for FR-SIM-223."""

from datetime import UTC, datetime
from decimal import Decimal

from app.services.simulator import build_lifecycle_deal
from app.services.trading import create_position_authority_event


def test_lifecycle_deal_is_self_sufficient_for_trading_authority() -> None:
    """One deal carries complete post-event position, account, time, and ledger proof."""
    instant = datetime(2026, 8, 17, tzinfo=UTC)
    response = build_lifecycle_deal(
        order_id="order-1",
        account_id="account-1",
        position_id="position-1",
        side="BUY",
        quantity=Decimal(1),
        price=Decimal("1.1"),
        entry="DEAL_ENTRY_IN",
        reason="EXPERT",
        occurred_at=instant,
        economic_at=instant,
        available_at=instant,
        source_sequence=4,
        fee_evidence={"commission": Decimal(-1)},
        authority_snapshot={
            "position": {
                "position_id": "position-1",
                "symbol": "EURUSD",
                "side": "LONG",
                "state": "OPEN",
                "quantity": Decimal(1),
                "source_sequence": 4,
            },
            "account": {"equity": Decimal(1000)},
        },
        ledger_reference="ledger-1",
    )
    assert response.data is not None
    deal = response.data
    event = create_position_authority_event(**deal["trading_authority_event"])
    assert event.deal_id == deal["deal_id"]
    assert deal["economic_at"] <= deal["available_at"]
    assert deal["authority_snapshot"]["position"]["position_id"] == "position-1"
    assert deal["ledger_reference"] == "ledger-1"
