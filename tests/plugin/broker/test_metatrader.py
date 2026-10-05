"""Unit tests for MetaTraderBroker plugin with mocked MetaTrader5 API."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from app.plugin.broker import (
    MetaTraderBroker,
    OrderAction,
    OrderType,
    TradeRequest,
)


@pytest.fixture
def mock_mt5():
    """Mock MetaTrader5 library functions."""
    with patch("app.plugin.broker.metatrader.mt5") as mock:
        mock.initialize.return_value = True
        mock.login.return_value = True
        mock.shutdown.return_value = True
        mock.last_error.return_value = (1, "Success")

        # Terminal info mock
        term_mock = MagicMock()
        term_mock.community_account = True
        term_mock.connected = True
        term_mock.name = "MetaTrader 5"
        term_mock.build = 4000
        mock.terminal_info.return_value = term_mock
        mock.version.return_value = (500, 4000, "2024-01-01")

        # Account info mock
        acc_mock = MagicMock()
        acc_mock.login = 61605506
        acc_mock.balance = 50000.0
        acc_mock.equity = 50000.0
        acc_mock.currency = "USD"
        acc_mock.leverage = 100
        mock.account_info.return_value = acc_mock

        # Symbol info mock
        sym_mock = MagicMock()
        sym_mock.name = "EURUSD"
        sym_mock.visible = True
        sym_mock.select = True
        sym_mock.digits = 5
        sym_mock.point = 0.00001
        sym_mock.bid = 1.08500
        sym_mock.ask = 1.08510
        mock.symbol_info.return_value = sym_mock
        mock.symbols_total.return_value = 100
        mock.symbols_get.return_value = [sym_mock]
        mock.symbol_select.return_value = True

        # Tick mock
        tick_mock = MagicMock()
        tick_mock.time = 1700000000
        tick_mock.bid = 1.08500
        tick_mock.ask = 1.08510
        tick_mock.last = 1.08505
        tick_mock.volume = 10
        mock.symbol_info_tick.return_value = tick_mock

        # Margin & Profit mocks
        mock.order_calc_margin.return_value = 20.0
        mock.order_calc_profit.return_value = 50.0

        # Order Check mock
        check_mock = MagicMock()
        check_mock.retcode = 0
        check_mock.balance = 50000.0
        check_mock.equity = 50000.0
        check_mock.profit = 0.0
        check_mock.margin = 20.0
        check_mock.margin_free = 49980.0
        mock.order_check.return_value = check_mock

        # Order Send mock
        res_mock = MagicMock()
        res_mock.retcode = 10009  # TRADE_RETCODE_DONE
        res_mock.deal = 9999
        res_mock.order = 8888
        res_mock.volume = 0.01
        res_mock.price = 1.08510
        res_mock.bid = 1.08500
        res_mock.ask = 1.08510
        res_mock.comment = "Done"
        mock.order_send.return_value = res_mock
        mock.TRADE_RETCODE_DONE = 10009

        # Positions & Orders mocks
        pos_mock = MagicMock()
        pos_mock.ticket = 8888
        pos_mock.symbol = "EURUSD"
        pos_mock.type = 0
        pos_mock.volume = 0.01
        pos_mock.price_open = 1.08510
        mock.positions_get.return_value = [pos_mock]
        mock.positions_total.return_value = 1
        mock.orders_get.return_value = []
        mock.orders_total.return_value = 0
        mock.history_orders_get.return_value = []
        mock.history_orders_total.return_value = 0
        mock.history_deals_get.return_value = []
        mock.history_deals_total.return_value = 0

        yield mock


def test_mt5_connect_and_disconnect(mock_mt5) -> None:
    """Verify MT5 connection lifecycle."""
    broker = MetaTraderBroker()
    res = broker.connect()
    assert res.is_success is True

    conn = broker.is_connected()
    assert conn.data is True

    disc = broker.disconnect()
    assert disc.is_success is True


def test_mt5_account_and_terminal_info(mock_mt5) -> None:
    """Verify MT5 account and terminal properties retrieval."""
    broker = MetaTraderBroker()

    acc = broker.get_account_info()
    assert acc.is_success is True
    assert acc.data.login == 61605506
    assert acc.data.balance == 50000.0

    term = broker.get_terminal_info()
    assert term.is_success is True
    assert term.data.name == "MetaTrader 5"


def test_mt5_symbol_operations(mock_mt5) -> None:
    """Verify MT5 symbol queries and ticks."""
    broker = MetaTraderBroker()

    sym_info = broker.get_symbol_info("EURUSD")
    assert sym_info.is_success is True
    assert sym_info.data.name == "EURUSD"

    syms = broker.get_symbols()
    assert syms.is_success is True
    assert len(syms.data) == 1

    tick = broker.get_symbol_tick("EURUSD")
    assert tick.is_success is True
    assert tick.data.bid == 1.08500

    enable = broker.enable_symbol("EURUSD", enable=True)
    assert enable.is_success is True


def test_mt5_calculations_and_order_check(mock_mt5) -> None:
    """Verify margin, profit, and order check calls."""
    broker = MetaTraderBroker()

    margin = broker.calculate_margin(
        action=OrderType.BUY, symbol="EURUSD", volume=0.01, price=1.08510
    )
    assert margin.is_success is True
    assert margin.data == 20.0

    profit = broker.calculate_profit(
        action=OrderType.BUY,
        symbol="EURUSD",
        volume=0.01,
        price_open=1.0850,
        price_close=1.0860,
    )
    assert profit.is_success is True
    assert profit.data == 50.0

    chk = broker.check_order(
        TradeRequest(
            action=OrderAction.DEAL, symbol="EURUSD", volume=0.01, type=OrderType.BUY
        )
    )
    assert chk.is_success is True
    assert chk.data.retcode == 0


def test_mt5_trade_and_positions(mock_mt5) -> None:
    """Verify MT5 trade execution and position inspection."""
    broker = MetaTraderBroker()

    trade_res = broker.trade(
        TradeRequest(
            action=OrderAction.DEAL, symbol="EURUSD", volume=0.01, type=OrderType.BUY
        )
    )
    assert trade_res.is_success is True
    assert trade_res.data.order == 8888
    assert trade_res.data.deal == 9999

    pos = broker.get_position_info(symbol="EURUSD")
    assert pos.is_success is True
    assert len(pos.data) == 1
    assert pos.data[0].ticket == 8888


def test_mt5_asdict_mapping(mock_mt5) -> None:
    """Verify that MT5 objects with _asdict() are mapped with all fields."""

    class FakeMT5Info:
        def __init__(self, data: dict[str, object]) -> None:
            self._data = data
            for k, v in data.items():
                setattr(self, k, v)

        def _asdict(self) -> dict[str, object]:
            return dict(self._data)

    mock_mt5.terminal_info.return_value = FakeMT5Info(
        {
            "community_account": True,
            "connected": True,
            "name": "MetaTrader 5",
            "build": 4150,
            "ping_last": 1234,
            "language": "English",
        }
    )
    mock_mt5.account_info.return_value = FakeMT5Info(
        {
            "login": 99999,
            "trade_mode": 1,
            "balance": 25000.0,
            "margin_so_call": 60.0,
            "margin_so_so": 40.0,
        }
    )
    mock_mt5.symbol_info.return_value = FakeMT5Info(
        {
            "name": "GBPUSD",
            "digits": 5,
            "volume_real": 50.5,
            "isin": "GB1234567890",
        }
    )

    broker = MetaTraderBroker()
    term = broker.get_terminal_info()
    assert term.is_success is True
    assert term.data.build == 4150
    assert term.data.ping_last == 1234
    assert term.data.language == "English"

    acc = broker.get_account_info()
    assert acc.is_success is True
    assert acc.data.login == 99999
    assert acc.data.trade_mode == 1
    assert acc.data.margin_so_call == 60.0
    assert acc.data.margin_so_so == 40.0

    sym = broker.get_symbol_info("GBPUSD")
    assert sym.is_success is True
    assert sym.data.name == "GBPUSD"
    assert sym.data.volume_real == 50.5
    assert sym.data.isin == "GB1234567890"
