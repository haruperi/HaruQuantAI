"""Unit tests for core trading connection and execution contracts."""

from __future__ import annotations

import pytest
from app.core.enums import (
    AccountTradeMode,
    DealEntry,
    DealType,
    MarginMode,
    OrderFilling,
    OrderState,
    OrderTime,
    OrderType,
    PositionType,
    ReceiptStatus,
    StopoutMode,
    TradeAction,
)
from app.core.trading.connection.contracts import (
    DEAL_ENTRY_DESCRIPTIONS,
    DEAL_TYPE_DESCRIPTIONS,
    ORDER_FILLING_DESCRIPTIONS,
    ORDER_STATE_DESCRIPTIONS,
    ORDER_TIME_DESCRIPTIONS,
    ORDER_TYPE_DESCRIPTIONS,
    POSITION_TYPE_DESCRIPTIONS,
    READ_TIMEOUT,
    AccountInfo,
    BridgeError,
    BridgeEvent,
    DealInfo,
    OrderInfo,
    PositionInfo,
    PropertyValue,
    Receipt,
    TerminalInfo,
    TradeCheckResult,
    TradeRequest,
    TradeResult,
    TradingBackend,
)


def test_trading_connection_exports() -> None:
    """Verify that all core trading connection contracts are exposed."""
    assert READ_TIMEOUT == 60.0
    assert BridgeError is not None
    assert PropertyValue is not None
    assert Receipt is not None
    assert BridgeEvent is not None
    assert TradingBackend is not None
    assert AccountInfo is not None
    assert TerminalInfo is not None
    assert PositionInfo is not None
    assert OrderInfo is not None
    assert DealInfo is not None
    assert TradeRequest is not None
    assert TradeResult is not None
    assert TradeCheckResult is not None


def test_enum_descriptions() -> None:
    """Verify description dictionary mappings for orders, positions, and deals."""
    assert ORDER_TYPE_DESCRIPTIONS[OrderType.BUY] == "Buy"
    assert ORDER_TYPE_DESCRIPTIONS[OrderType.SELL] == "Sell"
    assert POSITION_TYPE_DESCRIPTIONS[PositionType.BUY] == "Buy"
    assert ORDER_STATE_DESCRIPTIONS[OrderState.PLACED] == "Placed"
    assert DEAL_TYPE_DESCRIPTIONS[DealType.BUY] == "Buy"
    assert DEAL_ENTRY_DESCRIPTIONS[DealEntry.IN] == "In"
    assert ORDER_FILLING_DESCRIPTIONS[OrderFilling.FOK] == "Fill or Kill"
    assert ORDER_TIME_DESCRIPTIONS[OrderTime.GTC] == "Good Till Cancelled"


def test_bridge_error() -> None:
    """Verify BridgeError exception attributes and message formatting."""
    err = BridgeError(
        "Connection lost", code="ERR_DISCONNECTED", command_id="cmd-123", uncertain=True
    )
    assert str(err) == "Connection lost"
    assert err.code == "ERR_DISCONNECTED"
    assert err.command_id == "cmd-123"
    assert err.uncertain is True


def test_receipt_immutability_and_slots() -> None:
    """Verify Receipt frozen slotted dataclass behavior."""
    receipt = Receipt(
        command_id="cmd-1",
        object_id="acc-1",
        class_name="Account",
        method_name="AccountInfo",
        status=ReceiptStatus.CREATED,
        created_at=1000.0,
    )
    assert receipt.command_id == "cmd-1"
    assert receipt.status == ReceiptStatus.CREATED
    with pytest.raises(AttributeError):
        receipt.status = ReceiptStatus.RESOLVED  # type: ignore[misc]


def test_property_value_and_bridge_event() -> None:
    """Verify PropertyValue and BridgeEvent behavior."""
    pv = PropertyValue(ok=True, value=123.45)
    assert pv.ok is True
    assert pv.value == 123.45

    event = BridgeEvent(event_type="tick", payload={"symbol": "EURUSD", "bid": 1.1000})
    assert event.event_type == "tick"
    assert event.payload["symbol"] == "EURUSD"


def test_account_and_terminal_defaults() -> None:
    """Verify AccountInfo and TerminalInfo default construction and mutability."""
    account = AccountInfo()
    assert account.balance == 10_000.0
    assert account.trade_mode == AccountTradeMode.DEMO
    assert account.margin_mode == MarginMode.RETAIL_HEDGING
    assert account.stopout_mode == StopoutMode.PERCENT

    terminal = TerminalInfo()
    assert terminal.connected is True
    assert terminal.name == "HaruQuantAI Simulator"
    assert terminal.build == 0


def test_order_position_deal_structures() -> None:
    """Verify PositionInfo, OrderInfo, and DealInfo contracts."""
    pos = PositionInfo(ticket=1001, symbol="EURUSD", volume=1.5, price_open=1.0850)
    assert pos.ticket == 1001
    assert pos.symbol == "EURUSD"
    assert pos.volume == 1.5
    assert pos.price_open == 1.0850

    order = OrderInfo(
        ticket=2001, symbol="EURUSD", volume_initial=1.0, price_open=1.0800
    )
    assert order.ticket == 2001
    assert order.order_type == 0

    deal = DealInfo(ticket=3001, order=2001, volume=1.0, price=1.0800)
    assert deal.ticket == 3001
    assert deal.order == 2001


def test_trade_request_and_results() -> None:
    """Verify TradeRequest, TradeResult, and TradeCheckResult contracts."""
    req = TradeRequest(
        action=TradeAction.DEAL,
        symbol="EURUSD",
        volume=0.5,
        price=1.0850,
        order_type=OrderType.BUY,
        type_filling=OrderFilling.IOC,
        type_time=OrderTime.DAY,
    )
    assert req.symbol == "EURUSD"
    assert req.volume == 0.5
    assert req.order_type == OrderType.BUY

    res = TradeResult(retcode=10009, deal=5001, order=6001, comment="Done")
    assert res.retcode == 10009
    assert res.deal == 5001

    check = TradeCheckResult(retcode=0, balance=10_000.0, margin_free=9500.0)
    assert check.retcode == 0
    assert check.margin_free == 9500.0


class _DummyBackend:
    async def start(self) -> None:
        pass

    async def wait_connected(self, timeout: float | None = None) -> None:  # noqa: ASYNC109
        pass

    async def close(self) -> None:
        pass

    def arm(self) -> None:
        pass

    def disarm(self) -> None:
        pass

    def last_command_id(self) -> str | None:
        return None

    def receipt(self, command_id: str) -> Receipt | None:
        return None

    async def next_event(self, timeout: float | None = None) -> BridgeEvent:  # noqa: ASYNC109
        return BridgeEvent("test", {})

    async def await_request_event(
        self,
        request_id: int,
        timeout: float | None = None,  # noqa: ASYNC109
    ) -> BridgeEvent:
        return BridgeEvent("test", {})

    async def call(
        self,
        *,
        object_id: str,
        class_name: str,
        method_name: str,
        args: list[object],
        requires_arm: bool = False,
        timeout: float | None = None,  # noqa: ASYNC109
    ) -> object:
        return None


def test_trading_backend_protocol() -> None:
    """Verify TradingBackend runtime checkability."""
    assert isinstance(_DummyBackend(), TradingBackend)
