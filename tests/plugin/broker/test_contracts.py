"""Unit tests for broker plugin contracts, models, and base broker behavior.

Verifies:
- Standard response envelope (StandardResponse) with broker extensions
- Core enumerations and capabilities bitmask
- Dataclass models (SymbolInfo, Bar, Tick, etc.)
- BaseBroker default capability enforcement
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.plugin.broker.contracts import (
    AccountInfo,
    Bar,
    BaseBroker,
    BookItem,
    BrokerCapability,
    DealInfo,
    OrderAction,
    OrderCheckResult,
    OrderInfo,
    OrderType,
    PositionInfo,
    StandardError,
    StandardResponse,
    SymbolInfo,
    TerminalInfo,
    Tick,
    TimeFrame,
    TradeRequest,
    TradeResult,
)


def test_broker_standard_response_success_and_failure() -> None:
    """Verify StandardResponse creation with broker extensions and error payload."""
    ok_resp: StandardResponse[dict[str, int]] = StandardResponse.success(
        data={"key": 123},
        message="All good",
        extensions={"broker": "MockBroker", "raw": {"raw_id": 99}},
    )
    assert ok_resp.is_success is True
    assert bool(ok_resp) is True
    assert ok_resp.data == {"key": 123}
    assert ok_resp.unwrap() == {"key": 123}
    assert ok_resp.message == "All good"
    assert ok_resp.metadata.extensions["broker"] == "MockBroker"
    assert ok_resp.metadata.extensions["raw"] == {"raw_id": 99}
    assert ok_resp.error is None

    err = StandardError(code="ERR_404", message="Failed operation")
    fail_resp: StandardResponse[Any] = StandardResponse.failure(
        message="Failed operation",
        error=err,
        extensions={"broker": "MockBroker"},
    )
    assert fail_resp.is_success is False
    assert bool(fail_resp) is False
    assert fail_resp.data is None
    assert fail_resp.message == "Failed operation"
    assert fail_resp.error is not None
    assert fail_resp.error.code == "ERR_404"
    assert fail_resp.metadata.extensions["broker"] == "MockBroker"


def test_timeframe_enum_values() -> None:
    """Verify timeframe representation and string conversions."""
    assert TimeFrame.M1.value == "M1"
    assert TimeFrame.H1.value == "H1"
    assert TimeFrame.D1.value == "D1"
    assert TimeFrame.W1.value == "W1"


def test_dataclasses_instantiation() -> None:
    """Verify standard dataclass instantiations."""
    now = datetime.now(UTC)

    # Bar
    bar = Bar(time=now, open=1.0, high=1.2, low=0.9, close=1.1, tick_volume=100)
    assert bar.open == 1.0
    assert bar.close == 1.1

    # Tick
    tick = Tick(time=now, bid=1.1, ask=1.1001, last=1.1)
    assert tick.bid == 1.1

    # SymbolInfo
    sym = SymbolInfo(name="EURUSD", digits=5, point=0.00001, currency_base="EUR")
    assert sym.name == "EURUSD"
    assert sym.digits == 5

    # AccountInfo
    acc = AccountInfo(login=12345, balance=10000.0, equity=10050.0, currency="USD")
    assert acc.login == 12345
    assert acc.balance == 10000.0

    # TerminalInfo
    term = TerminalInfo(name="TestTerminal", connected=True)
    assert term.connected is True

    # BookItem
    book = BookItem(type="BUY", price=1.105, volume=10.0)
    assert book.price == 1.105

    # PositionInfo
    pos = PositionInfo(
        ticket=1001, symbol="EURUSD", type=OrderType.BUY, volume=0.5, price_open=1.1
    )
    assert pos.ticket == 1001

    # OrderInfo
    order = OrderInfo(
        ticket=2001, symbol="EURUSD", type=OrderType.BUY_LIMIT, volume_initial=1.0
    )
    assert order.ticket == 2001

    # DealInfo
    deal = DealInfo(
        ticket=3001,
        order=2001,
        symbol="EURUSD",
        type=OrderType.BUY,
        volume=1.0,
        price=1.1,
    )
    assert deal.ticket == 3001

    # TradeRequest & TradeResult
    req = TradeRequest(
        action=OrderAction.DEAL, symbol="EURUSD", volume=0.01, type=OrderType.BUY
    )
    assert req.symbol == "EURUSD"
    res = TradeResult(retcode=0, deal=3001, order=2001, volume=0.01, price=1.1)
    assert res.retcode == 0

    # OrderCheckResult
    chk = OrderCheckResult(
        retcode=0, balance=10000.0, equity=10000.0, margin=100.0, margin_free=9900.0
    )
    assert chk.margin == 100.0


def test_expanded_mt5_contract_fields() -> None:
    """Verify expanded fields on TerminalInfo, AccountInfo, and SymbolInfo."""
    term = TerminalInfo(
        community_account=True,
        community_connection=True,
        connected=True,
        dlls_allowed=False,
        trade_allowed=True,
        tradeapi_disabled=False,
        email_enabled=True,
        ftp_enabled=False,
        notifications_enabled=True,
        mqid=True,
        build=2366,
        maxbars=5000,
        codepage=1251,
        ping_last=77850,
        community_balance=707.10,
        retransmission=0.0,
        company="MetaQuotes Software Corp.",
        name="MetaTrader 5",
        language="Russian",
        path=r"E:\ProgramFiles\MetaTrader 5",
        data_path=r"E:\ProgramFiles\MetaTrader 5",
        commondata_path=r"C:\Users\Rosh\AppData\Roaming\MetaQuotes\Terminal\Common",
    )
    assert term.build == 2366
    assert term.ping_last == 77850
    assert term.community_balance == 707.10
    assert term.language == "Russian"

    acc = AccountInfo(
        login=25115284,
        trade_mode=0,
        leverage=100,
        limit_orders=200,
        margin_so_mode=0,
        trade_allowed=True,
        trade_expert=True,
        margin_mode=2,
        currency_digits=2,
        fifo_close=False,
        balance=99511.4,
        credit=0.0,
        profit=41.82,
        equity=99553.22,
        margin=102.4,
        margin_free=99450.82,
        margin_level=97220.0,
        margin_so_call=50.0,
        margin_so_so=30.0,
        margin_initial=0.0,
        margin_maintenance=0.0,
        assets=0.0,
        liabilities=0.0,
        commission_blocked=0.0,
        name="MetaQuotes Demo",
        server="MetaQuotes-Demo",
        currency="USD",
        company="MetaQuotes Software Corp.",
    )
    assert acc.trade_mode == 0
    assert acc.margin_mode == 2
    assert acc.margin_so_call == 50.0
    assert acc.margin_so_so == 30.0

    sym = SymbolInfo(
        name="EURUSD",
        custom=False,
        chart_mode=0,
        select=True,
        visible=True,
        session_deals=100,
        session_buy_orders=50,
        session_sell_orders=50,
        volume_real=123.45,
        price_change=-0.0015,
        price_volatility=0.05,
        price_theoretical=1.085,
        price_greeks_delta=0.5,
        margin_initial=1000.0,
        swap_mode=1,
        isin="US1234567890",
    )
    assert sym.name == "EURUSD"
    assert sym.custom is False
    assert sym.session_deals == 100
    assert sym.volume_real == 123.45
    assert sym.price_change == -0.0015
    assert sym.price_greeks_delta == 0.5
    assert sym.isin == "US1234567890"


def test_base_broker_unsupported_operations() -> None:
    """Verify BaseBroker default methods return standardized capability rejections."""
    broker = BaseBroker(name="EmptyBroker", capabilities=BrokerCapability.NONE)

    assert not broker.has_capability(BrokerCapability.TRADE)
    assert not broker.has_capability(BrokerCapability.MARKET_DATA)

    # Capability rejection tests
    res_trade = broker.trade(TradeRequest(symbol="EURUSD", volume=1.0))
    assert res_trade.is_success is False
    assert not res_trade
    assert "EmptyBroker doesn't have trading capabilities" in res_trade.message

    res_margin = broker.calculate_margin(
        action=OrderType.BUY, symbol="EURUSD", volume=1.0, price=1.0
    )
    assert res_margin.is_success is False
    assert not res_margin
    assert (
        "EmptyBroker doesn't have margin calculation capabilities" in res_margin.message
    )

    res_profit = broker.calculate_profit(
        action=OrderType.BUY,
        symbol="EURUSD",
        volume=1.0,
        price_open=1.0,
        price_close=1.1,
    )
    assert res_profit.is_success is False
    assert not res_profit
    assert (
        "EmptyBroker doesn't have profit calculation capabilities" in res_profit.message
    )

    res_check = broker.check_order(TradeRequest(symbol="EURUSD", volume=1.0))
    assert res_check.is_success is False
    assert not res_check
    assert "EmptyBroker doesn't have trading capabilities" in res_check.message

    res_bars = broker.get_bars(symbol="EURUSD")
    assert res_bars.is_success is False
    assert not res_bars
    assert "EmptyBroker doesn't have market data capabilities" in res_bars.message

    res_pos = broker.get_position_info()
    assert res_pos.is_success is False
    assert not res_pos
    assert "EmptyBroker doesn't have position capabilities" in res_pos.message

    res_orders = broker.get_order_info()
    assert res_orders.is_success is False
    assert not res_orders
    assert "EmptyBroker doesn't have orders capabilities" in res_orders.message

    res_history_deals = broker.get_history_deal_info()
    assert res_history_deals.is_success is False
    assert not res_history_deals
    assert "EmptyBroker doesn't have history capabilities" in res_history_deals.message
