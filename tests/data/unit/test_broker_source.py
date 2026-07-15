"""Unit tests for the broker source adapter snapshot query."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services.brokers.contracts.models import (
    BrokerAccountInfo,
    BrokerBalance,
    BrokerOrder,
    BrokerPage,
    BrokerPermissions,
    BrokerPosition,
)
from app.services.data.contracts import AccountSnapshotRequest
from app.services.data.contracts.errors import DataError
from app.services.data.sources.broker import get_account_state_snapshot


def test_account_snapshot_fails_closed_when_incomplete() -> None:
    """Account reads fail closed when the injected adapter lacks evidence."""

    req = AccountSnapshotRequest(
        source_id="mt5",
        account_id="acc-1",
        max_age_seconds=10,
        request_id="req-9456bdfa12ea76959c94a3572f5d91c73d838622df0a8d9b4e815c276c6b7880",
    )

    adapter = MagicMock()
    missing = MagicMock(data=None, error=object())
    adapter.get_account_info = AsyncMock(return_value=missing)
    adapter.get_balances = AsyncMock(return_value=missing)
    adapter.get_positions = AsyncMock(return_value=missing)
    adapter.get_orders = AsyncMock(return_value=missing)
    adapter.get_permissions = AsyncMock(return_value=missing)
    adapter.is_connected = AsyncMock(return_value=missing)

    with pytest.raises(DataError) as captured:
        get_account_state_snapshot(req, adapter)
    assert captured.value.code == "SOURCE_UNAVAILABLE"


def test_account_snapshot_success() -> None:
    """Verify standard account state snapshot mapping from mock adapter."""
    # Mock Broker DTOs
    now = datetime.now(UTC)
    mock_info = BrokerAccountInfo(
        account_id="acc-1",
        retrieved_at=now,
        currency="USD",
        balance=Decimal(10000),
        equity=Decimal(10500),
        margin=Decimal(1000),
        free_margin=Decimal(9500),
        status="ACTIVE",
    )
    mock_balance = BrokerBalance(
        asset="USD",
        unit="CURRENCY",
        retrieved_at=now,
        total=Decimal(10000),
        available=Decimal(9000),
        locked=Decimal(1000),
    )
    mock_pos = BrokerPosition(
        position_id="pos-1",
        symbol="AAPL",
        side="LONG",
        quantity=Decimal(10),
        quantity_unit="SHARES",
        retrieved_at=now,
        state="OPEN",
        open_price=Decimal(150),
    )
    mock_order = BrokerOrder(
        order_id="ord-1",
        symbol="MSFT",
        side="BUY",
        order_type="LIMIT",
        state="NEW",
        quantity=Decimal(5),
        filled=Decimal(0),
        remaining=Decimal(5),
        quantity_unit="SHARES",
        retrieved_at=now,
        price=Decimal(250),
    )
    mock_perms = BrokerPermissions(
        observed_at=now,
        trade_write=True,
        market_data_read=True,
        account_read=True,
    )

    # Mock BrokerAdapter and its methods
    mock_adapter = MagicMock()
    mock_adapter.get_account_info = AsyncMock()
    mock_adapter.get_balances = AsyncMock()
    mock_adapter.get_positions = AsyncMock()
    mock_adapter.get_orders = AsyncMock()
    mock_adapter.get_permissions = AsyncMock()
    mock_adapter.is_connected = AsyncMock()

    def mock_res(data: object = None, error: object = None) -> object:
        m = MagicMock()
        m.data = data
        m.error = error
        return m

    mock_adapter.get_account_info.return_value = mock_res(data=mock_info)
    mock_adapter.get_balances.return_value = mock_res(data=(mock_balance,))
    mock_adapter.get_positions.return_value = mock_res(
        data=BrokerPage(items=(mock_pos,), limit=10)
    )
    mock_adapter.get_orders.return_value = mock_res(
        data=BrokerPage(items=(mock_order,), limit=10)
    )
    mock_adapter.get_permissions.return_value = mock_res(data=mock_perms)
    mock_adapter.is_connected.return_value = mock_res(data=True)

    req = AccountSnapshotRequest(
        source_id="yahoo",
        account_id="acc-1",
        max_age_seconds=30,
        request_id="req-24cf6ea68781eab00f0f09fa954ed083c6b0ea3e49c75928e09b174febb88a9e",
    )

    clock = MagicMock()
    clock.now.return_value = now
    snapshot = get_account_state_snapshot(req, mock_adapter, clock=clock)

    # Assertions
    assert snapshot.account_id == "acc-1"
    assert snapshot.currency == "USD"
    assert snapshot.equity == Decimal(10500)
    assert snapshot.margin_used == Decimal(1000)
    assert snapshot.margin_available == Decimal(9500)
    assert len(snapshot.balances) == 1
    assert snapshot.balances[0].asset == "USD"
    assert snapshot.balances[0].total == Decimal(10000)
    assert snapshot.balances[0].available == Decimal(9000)
    assert len(snapshot.positions) == 1
    assert snapshot.positions[0].position_id == "pos-1"
    assert snapshot.positions[0].side == "LONG"
    assert snapshot.positions[0].quantity == Decimal(10)
    assert snapshot.positions[0].entry_price == Decimal(150)
    assert len(snapshot.orders) == 1
    assert snapshot.orders[0].order_id == "ord-1"
    assert snapshot.orders[0].side == "BUY"
    assert snapshot.orders[0].quantity == Decimal(5)
    assert snapshot.orders[0].price == Decimal(250)
    assert snapshot.connected is True
    assert snapshot.trading_allowed is True
    assert all(call[0] != "connect" for call in mock_adapter.method_calls)
