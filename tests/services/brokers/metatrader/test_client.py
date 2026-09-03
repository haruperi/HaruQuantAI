"""Unit tests for MetaTrader 5 client module with direct functions and StandardResponse."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import app.services.brokers.metatrader.client as client_mod
import pytest
from app.contracts.broker.models import (
    BrokerAccountInfo,
    BrokerSymbolInfo,
    BrokerTerminalInfo,
)
from app.contracts.common.response import StandardResponse
from app.services.brokers.metatrader.client import (
    MT5_TERMINAL_ERROR_DESCRIPTIONS,
    MT5_TRADE_RETCODE_DESCRIPTIONS,
    MT5Client,
    MT5TerminalError,
    MT5TradeRetcode,
    get_credentials,
    get_mt5_error_description,
    get_mt5_retcode_description,
)


def _setup_market_mocks(mock_mt5: MagicMock) -> None:
    """Configure market and data mock responses on mt5 mock."""
    sym = MagicMock()
    sym.name = "EURUSD"
    mock_info = MagicMock()
    mock_info._asdict.return_value = {"name": "EURUSD", "digits": 5, "spread": 12}
    mock_tick = MagicMock()
    mock_tick.bid = 1.08500
    mock_tick.ask = 1.08512
    mock_tick.time = 1788375000.0
    mock_tick._asdict.return_value = {"bid": 1.08500, "ask": 1.08512}

    mock_mt5.symbols_get.return_value = (sym,)
    mock_mt5.symbol_info.return_value = mock_info
    mock_mt5.symbol_info_tick.return_value = mock_tick
    mock_mt5.symbols_total.return_value = 142
    mock_mt5.symbol_select.return_value = True
    mock_book_item = MagicMock()
    mock_book_item._asdict.return_value = {"type": 1, "price": 1.0851, "volume": 10}
    mock_mt5.market_book_add.return_value = True
    mock_mt5.market_book_get.return_value = (mock_book_item,)
    mock_mt5.market_book_release.return_value = True

    mock_rate = {
        "time": 1788375000,
        "open": 1.08,
        "high": 1.09,
        "low": 1.07,
        "close": 1.085,
        "tick_volume": 120,
    }
    mock_mt5.copy_rates_from_pos.return_value = [mock_rate]
    mock_mt5.copy_rates_range.return_value = [mock_rate]
    mock_mt5.copy_rates_from.return_value = [mock_rate]

    mock_tick_item = {"time": 1788375000, "bid": 1.085, "ask": 1.0851}
    mock_mt5.copy_ticks_from.return_value = [mock_tick_item]
    mock_mt5.copy_ticks_range.return_value = [mock_tick_item]


def _setup_trade_mocks(mock_mt5: MagicMock) -> None:
    """Configure trade, order, and position mock responses on mt5 mock."""
    mock_order = MagicMock()
    mock_order.ticket = 101
    mock_order._asdict.return_value = {"ticket": 101, "symbol": "EURUSD", "type": 2}
    mock_deal = MagicMock()
    mock_deal.ticket = 201
    mock_deal._asdict.return_value = {"ticket": 201, "symbol": "EURUSD", "profit": 25.0}
    mock_pos = MagicMock()
    mock_pos.ticket = 901
    mock_pos._asdict.return_value = {"ticket": 901, "symbol": "EURUSD", "profit": 150.0}

    mock_mt5.orders_get.return_value = (mock_order,)
    mock_mt5.history_orders_get.return_value = (mock_order,)
    mock_mt5.history_deals_get.return_value = (mock_deal,)
    mock_mt5.positions_get.return_value = (mock_pos,)
    mock_mt5.orders_total.return_value = 5
    mock_mt5.positions_total.return_value = 3
    mock_mt5.history_orders_total.return_value = 42
    mock_mt5.history_deals_total.return_value = 88
    mock_mt5.order_calc_margin.return_value = 108.50
    mock_mt5.order_calc_profit.return_value = 50.00

    mock_check_res = MagicMock()
    mock_check_res.retcode = 0
    mock_check_res.comment = "Done"
    mock_check_res._asdict.return_value = {
        "retcode": 0,
        "balance": 50000,
        "margin": 100,
    }
    mock_mt5.order_check.return_value = mock_check_res


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

    mock_trade_res = MagicMock()
    mock_trade_res.retcode = 10009
    mock_trade_res.order = 100501
    mock_trade_res.comment = "Done"
    mock_trade_res._asdict.return_value = {
        "retcode": 10009,
        "order": 100501,
        "comment": "Done",
    }

    mock_mt5 = MagicMock()
    mock_mt5.initialize.return_value = True
    mock_mt5.terminal_info.return_value = mock_terminal
    mock_mt5.version.return_value = (500, 6140, "2026-08-21")
    mock_mt5.account_info.return_value = mock_acc
    mock_mt5.order_send.return_value = mock_trade_res
    mock_mt5.last_error.return_value = (0, "Success")

    _setup_market_mocks(mock_mt5)
    _setup_trade_mocks(mock_mt5)

    monkeypatch.setattr(client_mod, "mt5", mock_mt5)


@pytest.fixture
def client() -> MT5Client:
    """Return a fresh MT5Client instance."""
    return MT5Client()


def test_connection_lifecycle(client: MT5Client) -> None:
    """Verify connect, disconnect, and is_connected methods on MT5Client."""
    conn_res = client.connect(login=61563411, server="DemoServer")
    assert isinstance(conn_res, StandardResponse)
    assert conn_res.status == "connected"
    assert conn_res.data["connected"] is True
    assert conn_res.data["login"] == 61563411
    assert client.is_connected() is True

    disc_res = client.disconnect()
    assert disc_res.status == "success"
    assert disc_res.data["connected"] is False


def test_get_terminal_info(client: MT5Client) -> None:
    """Verify get_terminal_info returns StandardResponse with BrokerTerminalInfo."""
    resp = client.get_terminal_info()
    assert isinstance(resp, StandardResponse)
    assert resp.status == "success"
    assert isinstance(resp.data, BrokerTerminalInfo)
    assert resp.data.build == 6140
    assert resp.data["build"] == 6140
    assert "build" in resp.data
    # Test dictionary-like access
    assert resp["status"] == "success"
    assert resp.get("status") == "success"
    dict_repr = resp.to_dict()
    assert dict_repr["status"] == "success"


def test_get_account_info(client: MT5Client) -> None:
    """Verify get_account_info returns StandardResponse with BrokerAccountInfo."""
    resp = client.get_account_info()
    assert isinstance(resp, StandardResponse)
    assert resp.status == "success"
    assert isinstance(resp.data, BrokerAccountInfo)
    assert resp.data.login == 61563411
    assert resp.data["login"] == 61563411
    assert resp.data.balance == 53375.40
    assert resp.data["balance"] == 53375.40


def test_get_symbol_info(client: MT5Client) -> None:
    """Verify get_symbol_info returns StandardResponse with BrokerSymbolInfo."""
    resp = client.get_symbol_info("EURUSD")
    assert isinstance(resp, StandardResponse)
    assert resp.status == "success"
    assert isinstance(resp.data, BrokerSymbolInfo)
    assert resp.data.name == "EURUSD"
    assert resp.data["name"] == "EURUSD"
    assert resp.data.spread == 12
    assert resp.data["spread"] == 12


def test_get_position_info(client: MT5Client) -> None:
    """Verify get_position_info queries all positions and specific ticket."""
    resp_all = client.get_position_info()
    assert isinstance(resp_all, StandardResponse)
    assert resp_all.status == "success"
    assert len(resp_all.data) == 1
    assert resp_all.data[0]["ticket"] == 901

    resp_ticket = client.get_position_info(ticket=901)
    assert isinstance(resp_ticket, StandardResponse)
    assert resp_ticket.status == "success"
    assert resp_ticket.data["ticket"] == 901


def test_get_order_info(client: MT5Client) -> None:
    """Verify get_order_info queries active orders and specific ticket."""
    resp_all = client.get_order_info()
    assert isinstance(resp_all, StandardResponse)
    assert resp_all.status == "success"
    assert len(resp_all.data) == 1
    assert resp_all.data[0]["ticket"] == 101

    resp_ticket = client.get_order_info(ticket=101)
    assert isinstance(resp_ticket, StandardResponse)
    assert resp_ticket.status == "success"
    assert resp_ticket.data["ticket"] == 101


def test_get_history_order_info(client: MT5Client) -> None:
    """Verify get_history_order_info queries history orders."""
    resp_hist = client.get_history_order_info(date_from=0, date_to=1788375000)
    assert isinstance(resp_hist, StandardResponse)
    assert resp_hist.status == "success"
    assert len(resp_hist.data) == 1
    assert resp_hist.data[0]["ticket"] == 101

    resp_ticket = client.get_history_order_info(ticket=101)
    assert isinstance(resp_ticket, StandardResponse)
    assert resp_ticket.status == "success"
    assert resp_ticket.data["ticket"] == 101


def test_get_history_deal_info(client: MT5Client) -> None:
    """Verify get_history_deal_info queries history deals."""
    resp_deals = client.get_history_deal_info(date_from=0, date_to=1788375000)
    assert isinstance(resp_deals, StandardResponse)
    assert resp_deals.status == "success"
    assert len(resp_deals.data) == 1
    assert resp_deals.data[0]["ticket"] == 201

    resp_ticket = client.get_history_deal_info(ticket=201)
    assert isinstance(resp_ticket, StandardResponse)
    assert resp_ticket.status == "success"
    assert resp_ticket.data["ticket"] == 201


def test_trade_execution(client: MT5Client) -> None:
    """Verify trade execution returns StandardResponse."""
    req = {"symbol": "EURUSD", "volume": 0.1, "type": 0}
    resp = client.trade(req)
    assert isinstance(resp, StandardResponse)
    assert resp.status == "success"
    assert resp.data["retcode"] == 10009
    assert resp.data["order"] == 100501


def test_error_handling(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify failure cases return StandardResponse with status='error'."""
    mock_failing_mt5 = MagicMock()
    mock_failing_mt5.initialize.return_value = False
    mock_failing_mt5.terminal_info.return_value = None
    mock_failing_mt5.account_info.return_value = None
    mock_failing_mt5.symbol_info.return_value = None
    mock_failing_mt5.positions_get.return_value = None
    mock_failing_mt5.orders_get.return_value = None
    mock_failing_mt5.history_orders_get.return_value = None
    mock_failing_mt5.history_deals_get.return_value = None
    mock_failing_mt5.order_send.return_value = None
    mock_failing_mt5.last_error.return_value = (-10004, "No IPC connection")

    client = MT5Client(mt5_module=mock_failing_mt5)

    conn_res = client.connect()
    assert conn_res.status == "error"
    assert conn_res.error["code"] == -10004

    term_res = client.get_terminal_info()
    assert term_res.status == "error"
    assert term_res.error["code"] == -10004

    acc_res = client.get_account_info()
    assert acc_res.status == "error"
    assert acc_res.error["code"] == -10004

    sym_res = client.get_symbol_info("EURUSD")
    assert sym_res.status == "error"

    pos_res = client.get_position_info()
    assert pos_res.status == "error"

    ord_res = client.get_order_info()
    assert ord_res.status == "error"

    hist_ord_res = client.get_history_order_info()
    assert hist_ord_res.status == "error"

    hist_deal_res = client.get_history_deal_info()
    assert hist_deal_res.status == "error"

    trade_res = client.trade({"symbol": "EURUSD"})
    assert trade_res.status == "error"


def test_capability_protocol(client: MT5Client) -> None:
    """Verify MT5Client class implements capability protocol."""
    conn_res = client.connect()
    assert conn_res.status == "connected"
    assert client.is_connected() is True

    acc = client.get_account_info()
    assert acc.data["login"] == 61563411

    sym_info = client.get_symbol_info("EURUSD")
    assert sym_info.data["name"] == "EURUSD"

    orders_resp = client.get_order_info()
    assert orders_resp.status == "success"
    assert len(orders_resp.data) == 1

    positions_resp = client.get_position_info()
    assert positions_resp.status == "success"
    assert len(positions_resp.data) == 1

    trade_res = client.trade({"symbol": "EURUSD", "volume": 0.1})
    assert trade_res.data["retcode"] == 10009

    disc_res = client.disconnect()
    assert disc_res.status == "success"


def test_client_instance_isolation() -> None:
    """Verify that multiple MT5Client instances maintain independent state."""
    mock_mt5_a = MagicMock()
    mock_mt5_b = MagicMock()
    mock_mt5_a.initialize.return_value = True
    mock_mt5_b.initialize.return_value = True

    client_a = MT5Client(mt5_module=mock_mt5_a)
    client_b = MT5Client(mt5_module=mock_mt5_b)

    client_a.connect(login=11111)
    assert client_a.state["login"] == 11111
    assert client_b.state["login"] is None
    assert client_b.is_connected() is False


def test_self_contained_credential_loading(tmp_path: Any) -> None:
    """Verify MT5Client automatically loads credentials from SQLite database."""
    from app.services.brokers.metatrader._persistence import save_mt5_credentials
    from app.services.brokers.metatrader.config import MetaTraderConfig

    db_file = tmp_path / "test_creds.db"
    save_mt5_credentials(
        login=88776655,
        password="secret_db_password",  # pragma: allowlist secret
        server="Pepperstone-Live",
        terminal_path="C:/MT5/terminal64.exe",
        db_path=db_file,
    )

    # Calling MT5Client with database_path in config loads credentials automatically
    cfg = MetaTraderConfig(database_path=db_file)
    client = MT5Client(config=cfg)

    assert client.config.login == 88776655
    assert client.config.password == "secret_db_password"  # pragma: allowlist secret
    assert client.config.server == "Pepperstone-Live"
    assert client.config.terminal_path == "C:/MT5/terminal64.exe"

    # Verify standalone helper get_credentials works
    creds = get_credentials(db_file)
    assert creds["login"] == 88776655
    assert creds["server"] == "Pepperstone-Live"


def test_mt5_error_codes_and_descriptions() -> None:
    """Verify that MT5 terminal error codes and trade retcodes are defined and documented."""
    assert MT5TerminalError.INTERNAL_FAIL_CONNECT == -10004
    assert MT5TradeRetcode.DONE == 10009
    assert MT5TradeRetcode.NO_MONEY == 10019

    assert -10004 in MT5_TERMINAL_ERROR_DESCRIPTIONS
    assert "terminal may not be running" in MT5_TERMINAL_ERROR_DESCRIPTIONS[-10004]

    assert 10009 in MT5_TRADE_RETCODE_DESCRIPTIONS
    assert get_mt5_retcode_description(10009) == "Request completed successfully"
    assert get_mt5_retcode_description(10019) == "Insufficient funds to execute trade"
    assert (
        get_mt5_error_description(-10004)
        == "Failed to connect to MetaTrader 5 terminal (terminal may not be running)"
    )


def test_symbols_and_market_depth(client: MT5Client) -> None:
    """Verify get_num_of_symbols, get_symbols, enable_symbol, get_symbol_tick, and DOM functions."""
    num_sym = client.get_num_of_symbols()
    assert num_sym.status == "success"
    assert num_sym.data == 142

    syms = client.get_symbols()
    assert syms.status == "success"
    assert len(syms.data) == 1
    assert isinstance(syms.data[0], BrokerSymbolInfo)
    assert syms.data[0].name == "EURUSD"
    assert syms.data[0]["name"] == "EURUSD"

    syms_grp = client.get_symbols(group="*USD*")
    assert syms_grp.status == "success"

    sel_res = client.enable_symbol("EURUSD", enable=True)
    assert sel_res.status == "success"
    assert sel_res.data is True

    desel_res = client.enable_symbol("EURUSD", enable=False)
    assert desel_res.status == "success"
    assert desel_res.data is True

    tick_res = client.get_symbol_tick("EURUSD")
    assert tick_res.status == "success"
    assert tick_res.data["bid"] == 1.08500

    dom_sub = client.subscribe_market_depth("EURUSD")
    assert dom_sub.status == "success"
    assert dom_sub.data is True

    dom_get = client.get_market_depth("EURUSD")
    assert dom_get.status == "success"
    assert len(dom_get.data) == 1
    assert dom_get.data[0]["price"] == 1.0851

    dom_unsub = client.unsubscribe_market_depth("EURUSD")
    assert dom_unsub.status == "success"
    assert dom_unsub.data is True


def test_bars_and_ticks(client: MT5Client) -> None:
    """Verify get_bars, get_historical_bars alias, and get_ticks with switching arguments."""
    from app.services.brokers.metatrader.client import resolve_timeframe

    assert resolve_timeframe("1m") == 1
    assert resolve_timeframe("H1") == 16385
    assert resolve_timeframe("1d") == 16408

    # get_bars with range
    bars_range = client.get_bars("EURUSD", timeframe="1h", date_from=1000, date_to=2000)
    assert bars_range.status == "success"
    assert len(bars_range.data) == 1
    assert bars_range.data["Close"].iloc[0] == 1.085
    assert bars_range.data.index.name == "DateTime"
    assert list(bars_range.data.columns) == [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "Spread",
    ]

    # get_bars with start_pos and count
    bars_pos = client.get_bars("EURUSD", timeframe="1m", start_pos=0, count=50)
    assert bars_pos.status == "success"
    assert len(bars_pos.data) == 1

    # get_bars with date_from and count
    bars_from = client.get_bars("EURUSD", timeframe="15m", date_from=1000, count=20)
    assert bars_from.status == "success"

    # get_bars default count
    bars_default = client.get_bars("EURUSD")
    assert bars_default.status == "success"

    # get_historical_bars alias
    bars_alias = client.get_historical_bars("EURUSD", count=10)
    assert bars_alias.status == "success"

    # get_ticks range
    ticks_range = client.get_ticks("EURUSD", date_from=1000, date_to=2000)
    assert ticks_range.status == "success"
    assert len(ticks_range.data) == 1
    assert ticks_range.data.index.name == "DateTime"
    assert list(ticks_range.data.columns) == ["Bid", "Ask", "Volume"]

    # get_ticks from start
    ticks_from = client.get_ticks("EURUSD", count=50)
    assert ticks_from.status == "success"


def test_order_position_history_and_totals(client: MT5Client) -> None:
    """Verify counts and group filtering for orders, positions, and history."""
    assert client.get_num_orders().data == 5
    assert client.get_num_positions().data == 3
    assert client.get_num_history_orders().data == 42
    assert client.get_num_history_orders(date_from=100, date_to=200).data == 42
    assert client.get_num_history_deals().data == 88
    assert client.get_num_history_deals(date_from=100, date_to=200).data == 88

    # Filter with group
    pos_grp = client.get_position_info(group="*USD*")
    assert pos_grp.status == "success"

    ord_grp = client.get_order_info(group="*USD*")
    assert ord_grp.status == "success"

    hist_ord_grp = client.get_history_order_info(group="*USD*")
    assert hist_ord_grp.status == "success"

    hist_deal_grp = client.get_history_deal_info(group="*USD*")
    assert hist_deal_grp.status == "success"

    # Filter with symbol
    hist_ord_sym = client.get_history_order_info(
        symbol="EURUSD", date_from=0, date_to=2000
    )
    assert hist_ord_sym.status == "success"

    hist_deal_sym = client.get_history_deal_info(
        symbol="EURUSD", date_from=0, date_to=2000
    )
    assert hist_deal_sym.status == "success"


def test_margin_profit_and_order_check(client: MT5Client) -> None:
    """Verify calculate_margin, calculate_profit, and check_order."""
    margin_res = client.calculate_margin(0, "EURUSD", 1.0, 1.0850)
    assert margin_res.status == "success"
    assert margin_res.data == 108.50

    profit_res = client.calculate_profit(0, "EURUSD", 1.0, 1.0800, 1.0850)
    assert profit_res.status == "success"
    assert profit_res.data == 50.00

    check_res = client.check_order({"symbol": "EURUSD", "volume": 0.1, "type": 0})
    assert check_res.status == "success"
    assert check_res.data["retcode"] == 0
