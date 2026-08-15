"""Integration evidence for netting and closure authority refresh."""

from decimal import Decimal

import pytest
from app.services.trading import (
    create_execution_position_store,
    get_execution_position,
    reconcile_execution_position_receipt,
)

from tests.trading.unit.state.test_execution_position_correlation import (
    _Adapter,
    _receipt,
)


@pytest.mark.anyio
async def test_fr_trd_101_many_orders_converge_to_one_net_position() -> None:
    """FR-TRD-101: multiple receipts converge on authority position identity."""
    store = create_execution_position_store()
    await reconcile_execution_position_receipt(
        _receipt("receipt-1", ("deal-1",)),
        store,
        _Adapter(),
        account_id="account-1",
        symbol="EURUSD",
    )
    second = await reconcile_execution_position_receipt(
        _receipt("receipt-2", ("deal-2", "deal-3")),
        store,
        _Adapter(),
        account_id="account-1",
        symbol="EURUSD",
    )
    assert second.position_id == "broker-position-1"
    assert get_execution_position(store, "broker-position-1") is second


@pytest.mark.anyio
async def test_fr_trd_102_full_close_uses_closed_authority_snapshot() -> None:
    """FR-TRD-102: full closure becomes FLAT only from authority evidence."""
    closed = await reconcile_execution_position_receipt(
        _receipt("receipt-close", ("deal-close",)),
        create_execution_position_store(),
        _Adapter("CLOSED"),
        account_id="account-1",
        symbol="EURUSD",
    )
    assert closed.state == "FLAT"
    assert closed.quantity == Decimal(0)


@pytest.mark.anyio
async def test_partial_close_and_reversal_follow_latest_authority() -> None:
    """Partial closure and reversal use current quantity and side, not receipt math."""
    store = create_execution_position_store()
    partial = await reconcile_execution_position_receipt(
        _receipt("receipt-partial", ("deal-partial",)),
        store,
        _Adapter(quantity=Decimal("0.4"), source_sequence=8),
        account_id="account-1",
        symbol="EURUSD",
    )
    reversed_position = await reconcile_execution_position_receipt(
        _receipt("receipt-reversal", ("deal-reversal",)),
        store,
        _Adapter(side="SHORT", quantity=Decimal("0.6"), source_sequence=9),
        account_id="account-1",
        symbol="EURUSD",
    )
    assert (partial.quantity, partial.side) == (Decimal("0.4"), "LONG")
    assert (reversed_position.quantity, reversed_position.side) == (
        Decimal("0.6"),
        "SHORT",
    )


@pytest.mark.anyio
async def test_hedging_receipts_retain_distinct_authority_identities() -> None:
    """Hedging-mode deals remain distinct when Brokers supplies distinct IDs."""
    store = create_execution_position_store()
    first = await reconcile_execution_position_receipt(
        _receipt("receipt-hedge-1", ("deal-hedge-1",)),
        store,
        _Adapter(position_id="broker-position-long", side="LONG"),
        account_id="account-1",
        symbol="EURUSD",
    )
    second = await reconcile_execution_position_receipt(
        _receipt("receipt-hedge-2", ("deal-hedge-2",)),
        store,
        _Adapter(position_id="broker-position-short", side="SHORT"),
        account_id="account-1",
        symbol="EURUSD",
    )
    assert {first.position_id, second.position_id} == {
        "broker-position-long",
        "broker-position-short",
    }
