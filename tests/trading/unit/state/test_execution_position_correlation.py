"""Unit evidence for receipt-to-authority execution-position correlation."""

# ruff: noqa: INP001 - repository test layout intentionally has no package marker.

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest
from app.services.brokers import build_broker_value
from app.services.trading import (
    create_execution_position_store,
    create_execution_receipt,
    reconcile_execution_position_receipt,
    restore_execution_position_store,
    serialize_execution_position_store,
)

NOW = datetime(2026, 8, 15, tzinfo=UTC)


class _Adapter:
    """Offline Broker authority fixture."""

    def __init__(
        self,
        position_state: str = "OPEN",
        *,
        side: str = "LONG",
        quantity: Decimal | None = None,
        source_sequence: int | None = 7,
        position_symbol: str = "EURUSD",
        position_id: str = "broker-position-1",
        deal_available: bool = True,
    ) -> None:
        """Initialize deterministic deal and position responses."""
        self.position_state = position_state
        self.side = side
        self.quantity = quantity
        self.source_sequence = source_sequence
        self.position_symbol = position_symbol
        self.position_id = position_id
        self.deal_available = deal_available
        self.deal_calls: list[str] = []

    async def get_deal(self, deal_id: str) -> object:
        """Return one captured deal."""
        self.deal_calls.append(deal_id)
        if not self.deal_available:
            return SimpleNamespace(status="error", data=None)
        return SimpleNamespace(
            status="success",
            data=build_broker_value(
                "deal",
                deal_id=deal_id,
                symbol="EURUSD",
                side="BUY",
                quantity=Decimal(1),
                quantity_unit="lot",
                price=Decimal("1.10"),
                partial=False,
                retrieved_at=NOW,
                position_id=self.position_id,
            ),
        )

    async def get_position(self, position_id: str) -> object:
        """Return one captured authority position."""
        return SimpleNamespace(
            status="success",
            data=build_broker_value(
                "position",
                position_id=position_id,
                symbol=self.position_symbol,
                side=self.side,
                quantity=(
                    self.quantity
                    if self.quantity is not None
                    else Decimal(1)
                    if self.position_state == "OPEN"
                    else Decimal(0)
                ),
                quantity_unit="lot",
                retrieved_at=NOW,
                state=self.position_state,
                open_price=Decimal("1.10") if self.position_state == "OPEN" else None,
                source_sequence=self.source_sequence,
            ),
        )


def _receipt(
    receipt_id: str = "receipt-1", deals: tuple[str, ...] = ("deal-1",)
) -> object:
    """Build one durable Trading receipt."""
    return create_execution_receipt(
        receipt_id=receipt_id,
        intent_id="intent-1",
        client_order_id="client-1",
        route="live",
        authority="mt5",
        provider_order_id="order-1",
        provider_deal_ids=deals,
        status="filled",
        requested_quantity=Decimal(1),
        filled_quantity=Decimal(1),
        average_price=Decimal("1.10"),
        authority_timestamp=NOW,
        received_at=NOW,
        response_classification="accepted",
        retry_safe=False,
        reconciliation_required=True,
        request_id="req-11111111-1111-4111-8111-111111111111",
        correlation_id="cor-11111111-1111-4111-8111-111111111111",
    )


@pytest.mark.anyio
async def test_fr_trd_085_086_correlates_deal_then_position_authority() -> None:
    """FR-TRD-085/086: receipt refresh follows deal-to-position authority."""
    state = await reconcile_execution_position_receipt(
        _receipt(),
        create_execution_position_store(),
        _Adapter(),
        account_id="account-1",
        symbol="EURUSD",
    )
    assert state.broker_position_id == "broker-position-1"
    assert state.state == "OPEN"


@pytest.mark.anyio
async def test_fr_trd_103_duplicate_and_restart_do_not_repeat_lookup() -> None:
    """FR-TRD-103: durable receipt watermark survives exact restore."""
    adapter = _Adapter()
    store = create_execution_position_store()
    await reconcile_execution_position_receipt(
        _receipt(), store, adapter, account_id="account-1", symbol="EURUSD"
    )
    restored = restore_execution_position_store(
        serialize_execution_position_store(store)
    )
    duplicate = await reconcile_execution_position_receipt(
        _receipt(), restored, adapter, account_id="account-1", symbol="EURUSD"
    )
    assert duplicate.source_sequence == 7
    assert adapter.deal_calls == ["deal-1"]
