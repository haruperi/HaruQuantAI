"""Unit tests for MetaTrader 5 client module."""

from __future__ import annotations

from unittest.mock import MagicMock

import app.services.brokers.metatrader.client as client_mod
import pytest
from app.services.brokers.metatrader.client import (
    MetaTraderClient,
    MetaTraderService,
    fr_brk_metatrader,
)


@pytest.fixture(autouse=True)
def _setup_mt5_mocks(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up standard MT5 mock behavior for client tests."""
    mock_terminal = MagicMock()
    mock_terminal.connected = True
    mock_terminal.ping_last = 15000
    mock_terminal._asdict.return_value = {"connected": True, "build": 6140}

    mock_acc = MagicMock()
    mock_acc._asdict.return_value = {
        "login": 61563411,
        "balance": 53375.40,
        "currency": "USD",
        "trade_allowed": True,
        "trade_expert": True,
    }

    sym = MagicMock()
    sym.name = "EURUSD"

    mock_info = MagicMock()
    mock_info._asdict.return_value = {"name": "EURUSD", "digits": 5, "spread": 12}

    mock_tick = MagicMock()
    mock_tick.bid = 1.08500
    mock_tick.ask = 1.08512
    mock_tick.time = 1788375000.0

    mock_order = MagicMock()
    mock_order.ticket = 101
    mock_order._asdict.return_value = {"ticket": 101, "symbol": "EURUSD", "type": 2}

    mock_pos = MagicMock()
    mock_pos.ticket = 901
    mock_pos._asdict.return_value = {"ticket": 901, "symbol": "EURUSD", "profit": 150.0}

    mock_trade_res = MagicMock()
    mock_trade_res.retcode = 10009
    mock_trade_res.order = 100501
    mock_trade_res._asdict.return_value = {"retcode": 10009, "order": 100501}

    mock_mt5 = MagicMock()
    mock_mt5.initialize.return_value = True
    mock_mt5.terminal_info.return_value = mock_terminal
    mock_mt5.version.return_value = (500, 6140, "2026-08-21")
    mock_mt5.account_info.return_value = mock_acc
    mock_mt5.symbols_get.return_value = (sym,)
    mock_mt5.symbol_info.return_value = mock_info
    mock_mt5.symbol_info_tick.return_value = mock_tick
    mock_mt5.symbol_select.return_value = True
    mock_mt5.orders_get.return_value = (mock_order,)
    mock_mt5.positions_get.return_value = (mock_pos,)
    mock_mt5.order_send.return_value = mock_trade_res

    monkeypatch.setattr(client_mod, "mt5", mock_mt5)
    default_client = MetaTraderClient(mt5_module=mock_mt5)
    client_mod.set_default_client(default_client)


def test_service_class_and_fr_report() -> None:
    """Verify MetaTraderService class implements required capability protocol."""
    service = MetaTraderService(client=client_mod.get_default_client())
    conn_res = service.connect()
    assert conn_res["status"] == "connected"
    assert service.is_connected() is True

    acc = service.get_account_info()
    assert acc["login"] == 61563411

    sym_info = service.get_symbol_info("EURUSD")
    assert sym_info["name"] == "EURUSD"

    quote = service.get_quote("EURUSD")
    assert quote["bid"] == 1.08500

    orders = service.get_orders()
    assert len(orders) == 1

    positions = service.get_positions()
    assert len(positions) == 1

    trade = service.place_order({"symbol": "EURUSD", "volume": 0.1})
    assert trade["retcode"] == 10009

    report = fr_brk_metatrader(client=client_mod.get_default_client())
    assert report["platform"] == "mt5"
    assert report["symbols"] == 1

    assert service.disconnect() is True


def test_client_instance_isolation() -> None:
    """Verify that multiple MetaTraderClient instances maintain independent state."""
    mock_mt5_a = MagicMock()
    mock_mt5_b = MagicMock()
    mock_mt5_a.initialize.return_value = True
    mock_mt5_b.initialize.return_value = True

    client_a = MetaTraderClient(mt5_module=mock_mt5_a)
    client_b = MetaTraderClient(mt5_module=mock_mt5_b)

    client_a.connect(login=11111)
    assert client_a.state["login"] == 11111
    assert client_b.state["login"] is None
    assert client_b.is_connected() is False
