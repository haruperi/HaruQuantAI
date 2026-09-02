"""Unit tests for MetaTrader 5 client module."""

from __future__ import annotations

from unittest.mock import MagicMock

import app.services.brokers.metatrader._account_info as acc_mod
import app.services.brokers.metatrader._order_info as order_mod
import app.services.brokers.metatrader._positions_info as pos_mod
import app.services.brokers.metatrader._symbol_info as sym_mod
import app.services.brokers.metatrader._terminal_info as term_mod
import app.services.brokers.metatrader._trade as trade_mod
import pytest
from app.services.brokers.metatrader.client import (
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

    for mod in (term_mod, acc_mod, sym_mod, order_mod, pos_mod, trade_mod):
        monkeypatch.setattr(mod.mt5, "initialize", lambda **kw: True)
        monkeypatch.setattr(mod.mt5, "terminal_info", lambda: mock_terminal)
        monkeypatch.setattr(mod.mt5, "version", lambda: (500, 6140, "2026-08-21"))
        monkeypatch.setattr(mod.mt5, "account_info", lambda: mock_acc)
        monkeypatch.setattr(mod.mt5, "symbols_get", lambda: (sym,))
        monkeypatch.setattr(mod.mt5, "symbol_info", lambda s: mock_info)
        monkeypatch.setattr(mod.mt5, "symbol_info_tick", lambda s: mock_tick)
        monkeypatch.setattr(mod.mt5, "symbol_select", lambda s, e: True)
        monkeypatch.setattr(mod.mt5, "orders_get", lambda **kw: (mock_order,))
        monkeypatch.setattr(mod.mt5, "positions_get", lambda **kw: (mock_pos,))
        monkeypatch.setattr(mod.mt5, "order_send", lambda req: mock_trade_res)


def test_service_class_and_fr_report() -> None:
    """Verify MetaTraderService class implements required capability protocol."""
    service = MetaTraderService()
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

    report = fr_brk_metatrader()
    assert report["platform"] == "mt5"
    assert report["symbols"] == 1

    assert service.disconnect() is True
