"""Tests asserting live broker adapters return canonical domain contracts."""

from __future__ import annotations

import pytest
from app.core.data.contracts import (
    AccountInfo,
    MarketTick,
    OrderInfo,
    PositionInfo,
    TerminalInfo,
    TradeCheckResult,
    TradeRequest,
    TradeResult,
)
from app.core.enums import (
    OrderType,
    TradeAction,
    TradeRetcode,
)
from app.core.trading.connection.base import BridgeError
from app.workspace.trading.brokers.crypto import CryptoBrokerClient
from app.workspace.trading.brokers.ctrader import CTraderClient
from app.workspace.trading.brokers.metatrader import MetaTraderClient


def test_metatrader_contracts() -> None:
    client = MetaTraderClient(host="127.0.0.1", port=7777, auth_token="token123")
    assert client.connect() is True
    assert client.is_connected is True

    # Terminal & Account
    terminal = client.get_terminal_info()
    assert isinstance(terminal, TerminalInfo)
    assert terminal.connected is True

    account = client.get_account_info()
    assert isinstance(account, AccountInfo)
    assert account.balance == 100000.0

    # Ticks
    received_ticks: list[MarketTick] = []
    client.subscribe_ticks("EURUSD", received_ticks.append)
    tick = MarketTick(time_msc=1700000000000, bid=1.1000, ask=1.1002, last=1.1001)
    client.emit_tick("EURUSD", tick)
    assert len(received_ticks) == 1
    assert client.get_tick("EURUSD") == tick
    client.unsubscribe_ticks("EURUSD")

    # OrderCheck
    bad_check = client.order_check(TradeRequest(symbol="EURUSD", volume=0.0))
    assert isinstance(bad_check, TradeCheckResult)
    assert bad_check.retcode == int(TradeRetcode.INVALID_VOLUME)

    ok_check = client.order_check(TradeRequest(symbol="EURUSD", volume=1.0))
    assert ok_check.retcode == int(TradeRetcode.DONE)

    # OrderSend - not armed
    req_deal = TradeRequest(
        symbol="EURUSD",
        volume=1.0,
        action=TradeAction.DEAL,
        order_type=OrderType.BUY,
        price=1.1002,
    )
    with pytest.raises(BridgeError, match="not armed"):
        client.order_send(req_deal)

    # OrderSend - armed
    client.arm()
    res_deal = client.order_send(req_deal)
    assert isinstance(res_deal, TradeResult)
    assert res_deal.retcode == int(TradeRetcode.DONE)
    assert len(client.get_positions()) == 1
    assert isinstance(client.get_positions()[0], PositionInfo)

    # OrderSend - pending
    req_pending = TradeRequest(
        symbol="EURUSD",
        volume=0.5,
        action=TradeAction.PENDING,
        order_type=OrderType.BUY_LIMIT,
        price=1.0950,
    )
    res_pending = client.order_send(req_pending)
    assert isinstance(res_pending, TradeResult)
    assert len(client.get_orders()) == 1
    assert isinstance(client.get_orders()[0], OrderInfo)

    client.disconnect()
    assert client.is_connected is False


def test_ctrader_contracts() -> None:
    client = CTraderClient(account_id="891044", is_live=False)
    assert client.connect() is True
    assert client.is_connected is True

    terminal = client.get_terminal_info()
    assert isinstance(terminal, TerminalInfo)

    account = client.get_account_info()
    assert isinstance(account, AccountInfo)
    assert account.balance == 50000.0

    # Check
    bad_check = client.order_check(TradeRequest(symbol="GBPUSD", volume=-1.0))
    assert bad_check.retcode == int(TradeRetcode.INVALID_VOLUME)

    # Order not armed
    req = TradeRequest(
        symbol="GBPUSD",
        volume=0.2,
        action=TradeAction.DEAL,
        order_type=OrderType.BUY,
    )
    with pytest.raises(BridgeError, match="not armed"):
        client.order_send(req)

    client.arm()
    res = client.order_send(req)
    assert isinstance(res, TradeResult)
    assert res.retcode == int(TradeRetcode.DONE)
    assert len(client.get_positions()) == 1

    # Pending order
    req_pend = TradeRequest(
        symbol="GBPUSD",
        volume=0.5,
        action=TradeAction.PENDING,
        order_type=OrderType.SELL_LIMIT,
        price=1.31,
    )
    res_pend = client.order_send(req_pend)
    assert res_pend.retcode == int(TradeRetcode.DONE)
    assert len(client.get_orders()) == 1

    client.disconnect()
    assert client.is_connected is False


def test_crypto_contracts() -> None:
    client = CryptoBrokerClient(
        api_key="mock_key",
        api_secret="mock_secret",
        is_futures=True,
    )
    assert client.connect() is True

    # HMAC signature
    signed = client.sign_payload({"symbol": "BTCUSDT", "recvWindow": 5000})
    assert "signature=" in signed
    assert "timestamp=" in signed

    terminal = client.get_terminal_info()
    assert isinstance(terminal, TerminalInfo)

    account = client.get_account_info()
    assert isinstance(account, AccountInfo)
    assert account.currency == "USDT"

    # Not armed
    req = TradeRequest(
        symbol="BTCUSDT",
        volume=0.01,
        action=TradeAction.DEAL,
        order_type=OrderType.BUY,
        price=65000.0,
    )
    with pytest.raises(BridgeError, match="not armed"):
        client.order_send(req)

    # Armed
    client.arm()
    res = client.order_send(req)
    assert isinstance(res, TradeResult)
    assert res.retcode == int(TradeRetcode.DONE)
    assert len(client.get_positions()) == 1

    req_limit = TradeRequest(
        symbol="BTCUSDT",
        volume=0.02,
        action=TradeAction.PENDING,
        order_type=OrderType.BUY_LIMIT,
        price=60000.0,
    )
    res_limit = client.order_send(req_limit)
    assert res_limit.retcode == int(TradeRetcode.DONE)
    assert len(client.get_orders()) == 1

    client.disconnect()
    assert client.is_connected is False
