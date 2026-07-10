"""Unit tests for trading read-only info facades."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from app.services.trading.info import (
    AccountInfo,
    DealInfo,
    HistoryOrderInfo,
    OrderInfo,
    PositionInfo,
    SymbolInfo,
    TerminalInfo,
)


class BrokerFixture:
    """Read-only broker module fixture."""

    def __init__(self) -> None:
        """Initialize broker fixture calls and payloads."""
        self.calls: list[tuple[str, dict[str, object]]] = []
        self.account = SimpleNamespace(
            login=123,
            server="Demo",
            leverage=100,
            limit_orders=10,
            trade_allowed=True,
            trade_expert=False,
            margin_mode="Hedging",
            balance=1000.0,
            credit=0.0,
            profit=1.5,
            equity=1001.5,
            margin=10.0,
            margin_free=991.5,
            margin_level=1000.0,
            name="Trader",
            currency="USD",
            company="Broker",
        )
        self.symbol = SimpleNamespace(
            name="EURUSD",
            digits=5,
            point=0.00001,
            trade_tick_size=0.00001,
            trade_mode=1,
            trade_contract_size=100000.0,
            volume_min=0.01,
            volume_max=100.0,
            volume_step=0.01,
            swap_mode=0,
            swap_long=-1.0,
            swap_short=0.5,
            bid=1.1,
            ask=1.1002,
            last=1.1001,
            spread=2,
            description="Euro",
            path="Forex",
        )
        self.ticket_record = SimpleNamespace(
            ticket=42,
            order=41,
            time=100,
            time_msc=100000,
            time_setup=90,
            type=0,
            magic=7,
            position_id=44,
            volume=0.1,
            volume_initial=0.1,
            volume_current=0.1,
            price=1.1,
            price_open=1.1,
            price_current=1.1002,
            sl=1.0,
            tp=1.2,
            symbol="EURUSD",
            comment="token=abcdefabcdefabcdefabcdefabcdef12",
            profit=2.0,
            swap=0.0,
            commission=-0.1,
            entry=0,
        )
        self.terminal = SimpleNamespace(
            language="English",
            company="Broker",
            name="Terminal",
            path="C:/terminal",
            data_path="C:/data",
            commondata_path="C:/common",
            build=1234,
            connected=True,
            trade_allowed=True,
            dlls_allowed=False,
            ping_last=12,
        )

    def get_account_info(self) -> object:
        """Return account info."""
        self.calls.append(("get_account_info", {}))
        return self.account

    def get_symbol_info(self, symbol: str) -> object:
        """Return symbol info."""
        self.calls.append(("get_symbol_info", {"symbol": symbol}))
        return self.symbol

    def get_position_info(self, **kwargs: object) -> list[object]:
        """Return position info."""
        self.calls.append(("get_position_info", kwargs))
        return [self.ticket_record]

    def get_order_info(self, **kwargs: object) -> list[object]:
        """Return order info."""
        self.calls.append(("get_order_info", kwargs))
        return [self.ticket_record]

    def get_history_order_info(self, **kwargs: object) -> list[object]:
        """Return history order info."""
        self.calls.append(("get_history_order_info", kwargs))
        return [self.ticket_record]

    def get_history_deal_info(self, **kwargs: object) -> list[object]:
        """Return deal info."""
        self.calls.append(("get_history_deal_info", kwargs))
        return [self.ticket_record]

    def get_terminal_info(self) -> object:
        """Return terminal info."""
        self.calls.append(("get_terminal_info", {}))
        return self.terminal


@pytest.fixture
def broker(monkeypatch: pytest.MonkeyPatch) -> BrokerFixture:
    """Patch the active broker resolver."""
    fixture = BrokerFixture()
    monkeypatch.setattr(
        "app.services.trading.info._common.get_broker_module",
        lambda: fixture,
    )
    return fixture


def test_account_terminal_and_symbol_facades_are_read_only(
    broker: BrokerFixture,
) -> None:
    """Account, terminal, and symbol wrappers expose read-only values."""
    account = AccountInfo()
    terminal = TerminalInfo()
    symbol = SymbolInfo("EURUSD")

    assert account.balance() == 1000.0
    assert account.leverage() == 100
    assert terminal.connected() is True
    assert terminal.ping_last() == 12
    assert symbol.refresh() is True
    assert symbol.select(True) is True
    assert symbol.volume_min() == 0.01
    assert symbol.tick_size() == 0.00001
    assert all(call[0] != "get_mt5_client" for call in broker.calls)


def test_ticket_facades_select_and_redact_payloads(broker: BrokerFixture) -> None:
    """Ticket wrappers expose MQL5-style accessors and redacted payloads."""
    position = PositionInfo()
    order = OrderInfo(42)
    history = HistoryOrderInfo(42)
    deal = DealInfo(42)

    assert position.select("EURUSD") is True
    assert position.ticket() == 42
    assert order.volume_initial() == 0.1
    assert history.state_description() == "Started"
    assert deal.order() == 41
    assert "abcdef" not in str(deal.payload())


def test_mql5_surface_accessors_cover_facade_methods(  # noqa: PLR0915
    broker: BrokerFixture,
) -> None:
    """MQL5-compatible accessors return safe primitive values."""
    account = AccountInfo()
    terminal = TerminalInfo()
    symbol = SymbolInfo("EURUSD")
    position = PositionInfo()
    order = OrderInfo(42)
    history = HistoryOrderInfo(42)
    deal = DealInfo(42)
    position.select_by_ticket(42)

    assert account.login() == 123
    assert account.trade_mode_description() == "Demo"
    assert account.limit_orders() == 10
    assert account.trade_allowed() is True
    assert account.trade_expert() is False
    assert account.margin_so_mode() == 0
    assert account.margin_mode() == 0
    assert account.margin_mode_description() == "Hedging"
    assert account.credit() == 0.0
    assert account.profit() == 1.5
    assert account.equity() == 1001.5
    assert account.free_margin() == 991.5
    assert account.free_margin_mode() == 0
    assert account.margin_level() == 1000.0
    assert account.margin_so_level() == 50.0
    assert account.name() == "Trader"
    assert account.server() == "Demo"
    assert account.currency() == "USD"
    assert account.company() == "Broker"
    assert account.info_integer(4) == 1
    assert account.info_double(3) == 1001.5
    assert account.info_string(2) == "USD"
    assert "login" in account.payload()

    assert terminal.language() == "English"
    assert terminal.company() == "Broker"
    assert terminal.name() == "Terminal"
    assert terminal.path() == "C:/terminal"
    assert terminal.data_path() == "C:/data"
    assert terminal.common_data_path() == "C:/common"
    assert terminal.build() == 1234
    assert terminal.trade_allowed() is True
    assert terminal.dlls_allowed() is False
    assert terminal.info_integer(4) == 12
    assert terminal.info_string(5) == "C:/common"
    assert "connected" in terminal.payload()

    assert symbol.name("GBPUSD") is True
    assert symbol.name() == "GBPUSD"
    assert symbol.refresh_rates() is True
    assert symbol.is_synchronized() is True
    assert symbol.digits() == 5
    assert symbol.point() == 0.00001
    assert symbol.trade_mode() == 1
    assert symbol.trade_mode_description() == "Full Access"
    assert symbol.contract_size() == 100000.0
    assert symbol.volume_max() == 100.0
    assert symbol.volume_step() == 0.01
    assert symbol.swap_mode() == 0
    assert symbol.swap_long() == -1.0
    assert symbol.swap_short() == 0.5
    assert symbol.bid() == 1.1
    assert symbol.ask() == 1.1002
    assert symbol.last() == 1.1001
    assert symbol.spread() == 2
    assert symbol.info_integer(3) == 2
    assert symbol.info_double(10) == 1.1001
    assert symbol.info_string(1) == "Euro"
    assert "volume_min" in symbol.payload()

    assert position.time_update() == 0
    assert position.time_update_msc() == 0
    assert position.identifier() == 42
    assert position.price_open() == 1.1
    assert position.stop_loss() == 1.0
    assert position.take_profit() == 1.2
    assert position.price_current() == 1.1002
    assert position.swap() == 0.0
    assert position.profit() == 2.0
    assert position.info_double(6) == 2.0

    assert order.time_setup() == 90
    assert order.time_setup_msc() == 0
    assert order.time_expiration() == 0
    assert order.time_done() == 0
    assert order.time_done_msc() == 0
    assert order.type_time() == 0
    assert order.type_time_description() == "GTC"
    assert order.type_filling() == 0
    assert order.type_filling_description() == "FOK"
    assert order.state() == 0
    assert order.position_by_id() == 0
    assert order.volume_current() == 0.1
    assert order.price_open() == 1.1
    assert order.stop_loss() == 1.0
    assert order.take_profit() == 1.2
    assert order.price_current() == 1.1002
    assert order.price_stop_limit() == 0.0
    assert order.info_double(5) == 1.1002

    assert history.select(42) is True
    assert deal.entry_description() == "Entry In"
    assert deal.commission() == -0.1
    assert deal.swap() == 0.0
    assert deal.profit() == 2.0


def test_facades_return_safe_defaults_when_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Facades return neutral values when broker data is unavailable."""
    empty = Mock()
    empty.get_account_info.return_value = None
    empty.get_terminal_info.return_value = None
    empty.get_symbol_info.return_value = None
    empty.get_order_info.return_value = []
    monkeypatch.setattr(
        "app.services.trading.info._common.get_broker_module",
        lambda: empty,
    )

    assert AccountInfo().balance() == 0.0
    assert TerminalInfo().connected() is False
    assert SymbolInfo("EURUSD").refresh() is False
    assert OrderInfo().select(1) is False
