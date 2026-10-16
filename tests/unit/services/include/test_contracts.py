"""Unit tests for foundational trading data contracts and enums.

Description:
    Validates instantiation, default field states, methods, and strict absence of
    legacy alias shims across the canonical contracts and enums defined in
    app.services.include.

Purpose:
    FEAT-LIBS-CONTRACTS: Core data contract verification.
    FEAT-LIBS-ENUMS: Canonical trading enumerations verification.

Key Capabilities:
    - FR-CONTRACTS-INSTANTIATION: Verify data contract defaults and field integrity.
    - FR-CONTRACTS-ROUNDING: Verify SymbolInfo.round_to_tick_size precision handling.
    - FR-CONTRACTS-ZERO-SHIMS: Verify strict absence of deprecated transitional aliases.
"""

from __future__ import annotations

import pytest
from app.services.include import contracts, enums
from app.services.include.contracts import (
    BOOK_TYPE_DESCRIPTIONS,
    DEAL_ENTRY_DESCRIPTIONS,
    DEAL_TYPE_DESCRIPTIONS,
    MAX_POSITION,
    MAX_RECORDS,
    ORDER_FILLING_DESCRIPTIONS,
    ORDER_STATE_DESCRIPTIONS,
    ORDER_TIME_DESCRIPTIONS,
    ORDER_TYPE_DESCRIPTIONS,
    POSITION_TYPE_DESCRIPTIONS,
    READ_TIMEOUT,
    SYMBOL_CALC_MODE_DESCRIPTIONS,
    SYMBOL_SWAP_MODE_DESCRIPTIONS,
    SYMBOL_TRADE_EXECUTION_DESCRIPTIONS,
    SYMBOL_TRADE_MODE_DESCRIPTIONS,
    TIMEFRAME_SECONDS,
    AccountInfo,
    BookInfo,
    BridgeEvent,
    ChartDef,
    DataInfo,
    DealInfo,
    MarketBar,
    MarketTick,
    OrderInfo,
    PositionInfo,
    PropertyValue,
    Receipt,
    SymbolAliasRecord,
    SymbolInfo,
    TerminalInfo,
    TradeCheckResult,
    TradeRequest,
    TradeResult,
    TradingBackend,
)
from app.services.include.enums import (
    AccountTradeMode,
    BookType,
    DealEntry,
    DealType,
    MarginMode,
    OrderFilling,
    OrderState,
    OrderTime,
    OrderType,
    PositionType,
    ReceiptStatus,
    SymbolCalcMode,
    SymbolSwapMode,
    SymbolTradeExecution,
    SymbolTradeMode,
    Timeframe,
    TradeAction,
    TradeRetcode,
)


def test_symbol_info_defaults_and_fields() -> None:
    """Verify SymbolInfo default values and field assignment."""
    info = SymbolInfo(name="EURUSD", digits=5, point=0.00001)
    assert info.name == "EURUSD"
    assert info.digits == 5
    assert info.point == 0.00001
    assert info.trade_contract_size == 100_000.0
    assert info.trade_tick_size == 0.00001
    assert info.select is True
    assert info.visible is True


def test_symbol_info_round_to_tick_size() -> None:
    """Verify SymbolInfo.round_to_tick_size rounding behavior."""
    sym = SymbolInfo(name="EURUSD", digits=5, point=0.00001, trade_tick_size=0.00005)
    assert sym.round_to_tick_size(1.08542) == 1.08540
    assert sym.round_to_tick_size(1.08543) == 1.08545

    # Test fallback when trade_tick_size is 0
    sym_zero = SymbolInfo(name="TEST", digits=2, point=0.01, trade_tick_size=0.0)
    assert sym_zero.round_to_tick_size(10.556) == 10.56


def test_account_info_defaults() -> None:
    """Verify AccountInfo field defaults and initialization."""
    acc = AccountInfo(login=12345, balance=5000.0, equity=5200.0)
    assert acc.login == 12345
    assert acc.balance == 5000.0
    assert acc.equity == 5200.0
    assert acc.leverage == 100
    assert acc.currency == "USD"
    assert acc.trade_mode == AccountTradeMode.DEMO
    assert acc.margin_mode == MarginMode.RETAIL_HEDGING


def test_terminal_info_defaults() -> None:
    """Verify TerminalInfo field defaults and initialization."""
    term = TerminalInfo(connected=True, trade_allowed=True)
    assert term.connected is True
    assert term.trade_allowed is True
    assert term.name == "HaruQuantAI Simulator"
    assert term.community_account is False


def test_position_info_defaults() -> None:
    """Verify PositionInfo field defaults and initialization."""
    pos = PositionInfo(
        ticket=1001,
        identifier=1001,
        symbol="EURUSD",
        position_type=int(PositionType.BUY),
        volume=1.0,
        price_open=1.08500,
    )
    assert pos.ticket == 1001
    assert pos.identifier == 1001
    assert pos.symbol == "EURUSD"
    assert pos.volume == 1.0
    assert pos.sl == 0.0
    assert pos.tp == 0.0
    assert pos.position_type == int(PositionType.BUY)


def test_order_info_defaults() -> None:
    """Verify OrderInfo field defaults and initialization."""
    order = OrderInfo(
        ticket=2001,
        symbol="EURUSD",
        order_type=int(OrderType.BUY_LIMIT),
        volume_initial=1.0,
        volume_current=1.0,
        price_open=1.08000,
    )
    assert order.ticket == 2001
    assert order.symbol == "EURUSD"
    assert order.order_type == int(OrderType.BUY_LIMIT)
    assert order.state == int(OrderState.STARTED)


def test_deal_info_defaults() -> None:
    """Verify DealInfo field defaults and initialization."""
    deal = DealInfo(
        ticket=3001,
        order=2001,
        position_id=1001,
        symbol="EURUSD",
        deal_type=int(DealType.BUY),
        entry=int(DealEntry.IN),
        volume=1.0,
        price=1.08500,
    )
    assert deal.ticket == 3001
    assert deal.order == 2001
    assert deal.position_id == 1001
    assert deal.symbol == "EURUSD"
    assert deal.deal_type == int(DealType.BUY)


def test_book_info_defaults() -> None:
    """Verify BookInfo initialization."""
    book = BookInfo(
        type=BookType.BOOK_TYPE_BUY, price=1.08550, volume=10, volume_real=10.0
    )
    assert book.type == BookType.BOOK_TYPE_BUY
    assert book.price == 1.08550
    assert book.volume == 10
    assert book.volume_real == 10.0


def test_trade_contracts() -> None:
    """Verify TradeRequest, TradeResult, TradeCheckResult."""
    req = TradeRequest(action=TradeAction.DEAL, symbol="EURUSD", volume=0.1)
    assert req.action == TradeAction.DEAL
    assert req.symbol == "EURUSD"
    assert req.volume == 0.1

    res = TradeResult(retcode=int(TradeRetcode.DONE), deal=101, order=202)
    assert res.retcode == int(TradeRetcode.DONE)
    assert res.deal == 101
    assert res.order == 202

    check = TradeCheckResult(retcode=int(TradeRetcode.DONE), margin=100.0)
    assert check.retcode == int(TradeRetcode.DONE)
    assert check.margin == 100.0


def test_constants() -> None:
    """Verify boundary constants defined in contracts."""
    assert MAX_RECORDS == 1000
    assert MAX_POSITION == 2**31 - 1
    assert READ_TIMEOUT == 60.0


def test_market_bar_methods() -> None:
    """Verify MarketBar calculations and predicates."""
    bar = MarketBar(
        time=1000,
        open=100.0,
        high=110.0,
        low=95.0,
        close=108.0,
        tick_volume=50,
        spread=2,
        real_volume=100,
    )
    assert bar.is_bullish() is True
    assert bar.is_bearish() is False
    assert bar.is_doji() is False
    assert bar.range() == 15.0
    assert bar.body() == 8.0
    assert bar.volume() == 100.0

    bearish = MarketBar(
        time=1000, open=105.0, high=110.0, low=95.0, close=98.0, tick_volume=20
    )
    assert bearish.is_bullish() is False
    assert bearish.is_bearish() is True
    assert bearish.body() == 7.0
    assert bearish.volume() == 20.0

    doji = MarketBar(time=1000, open=100.0, high=105.0, low=95.0, close=100.0)
    assert doji.is_doji() is True
    assert doji.body() == 0.0


def test_market_tick_methods() -> None:
    """Verify MarketTick calculations."""
    tick = MarketTick(
        time_msc=1000000,
        bid=100.0,
        ask=100.5,
        last=100.25,
        volume=10,
        flags=6,
        volume_real=10.5,
    )
    assert tick.spread() == 0.5
    assert tick.mid() == 100.25


def test_chart_def_operations() -> None:
    """Verify ChartDef methods, hashes, and round-trip serialization."""
    c1 = ChartDef("EURUSD", Timeframe.PERIOD_M1, history_from=100, history_to=500)
    assert c1.timeframe == "M1"
    assert c1.timeframe_seconds() == 60
    assert c1.is_symbol_recognized() is True

    c2 = ChartDef("EURUSD", "M5", history_from=100, history_to=500)
    assert c1.is_smaller_than(c2) is True
    assert c2.can_be_computed_from(c1) is True

    cloned = c1.clone(history_to=600)
    assert cloned.history_to == 600
    assert cloned.symbol == "EURUSD"

    payload = c1.to_dict()
    restored = ChartDef.from_dict(payload)
    assert restored.symbol == c1.symbol
    assert restored.timeframe == c1.timeframe
    assert restored.get_charts_hash() == c1.get_charts_hash()


def test_data_info_operations() -> None:
    """Verify DataInfo sync, clone, conversion to ChartDef, and serialization."""
    info = DataInfo(
        id=1,
        symbol="EURUSD",
        timeframe="M5",
        bars=200,
        category="Forex",
        date_from=100,
        date_to=500,
    )
    assert info.rows == 200
    assert info.total_records == 200
    assert info.instrument == "Forex"
    assert info.data_type == "Forex"

    chart = info.to_chart_def()
    assert chart.symbol == "EURUSD"
    assert chart.timeframe == "M5"
    assert chart.history_from == 100
    assert chart.history_to == 500

    d = info.to_dict()
    restored = DataInfo.from_dict(d)
    assert restored == info

    from_row_info = DataInfo.from_row(
        {"id": 2, "symbol": "GBPUSD", "timeframe": "H1", "bars": 50, "source": "test"}
    )
    assert from_row_info.symbol == "GBPUSD"
    assert from_row_info.rows == 50


def test_symbol_info_reconciled_serialization() -> None:
    """Verify SymbolInfo extended metadata fields and serialization."""
    sym = SymbolInfo(
        id=10,
        name="EURUSD",
        connection="BrokerA",
        default_spread=1.2,
        default_slippage=0.5,
        commissions="3.0",
        alias="EUR/USD",
        country="EU",
        sector="Currencies",
    )
    assert sym.symbol == "EURUSD"
    assert sym.name == "EURUSD"

    data = sym.to_dict()
    assert data["symbol"] == "EURUSD"
    assert data["connection"] == "BrokerA"
    assert data["default_spread"] == 1.2

    from_d = SymbolInfo.from_dict(data)
    assert from_d.name == "EURUSD"
    assert from_d.connection == "BrokerA"
    assert from_d.default_spread == 1.2

    from_row = SymbolInfo.from_row(
        {"id": 11, "symbol": "USDJPY", "digits": 3, "point": 0.001}
    )
    assert from_row.symbol == "USDJPY"
    assert from_row.name == "USDJPY"
    assert from_row.digits == 3


def test_symbol_alias_record() -> None:
    """Verify SymbolAliasRecord serialization."""
    rec = SymbolAliasRecord(
        alias="EURUSD.raw", symbol="EURUSD", description="Raw spread"
    )
    assert rec.to_dict() == {
        "alias": "EURUSD.raw",
        "symbol": "EURUSD",
        "description": "Raw spread",
    }


def test_bridge_contracts() -> None:
    """Verify PropertyValue, Receipt, and BridgeEvent dataclasses."""
    pv = PropertyValue(ok=True, value=123)
    assert pv.ok is True
    assert pv.value == 123
    assert pv.error is None

    rcpt = Receipt(
        command_id="cmd-1",
        object_id="obj-1",
        class_name="Trading",
        method_name="buy",
        status=ReceiptStatus.RESOLVED,
        created_at=1000.0,
    )
    assert rcpt.command_id == "cmd-1"
    assert rcpt.status == ReceiptStatus.RESOLVED

    ev = BridgeEvent(event_type="on_quote", payload={"bid": 1.105})
    assert ev.event_type == "on_quote"
    assert ev.payload["bid"] == 1.105


class _MockBackend:
    """Mock implementation satisfying TradingBackend protocol."""

    async def start(self) -> None: ...
    async def wait_connected(self, timeout: float | None = None) -> None: ...  # noqa: ASYNC109 -- backend deadline capability
    async def close(self) -> None: ...
    def arm(self) -> None: ...
    def disarm(self) -> None: ...
    def last_command_id(self) -> str | None:
        return None

    def receipt(self, command_id: str) -> Receipt | None:
        return None

    async def next_event(self, timeout: float | None = None) -> BridgeEvent:  # noqa: ASYNC109 -- backend deadline capability
        return BridgeEvent(event_type="", payload={})

    async def await_request_event(
        self,
        request_id: int,
        timeout: float | None = None,  # noqa: ASYNC109 -- backend deadline capability
    ) -> BridgeEvent:
        return BridgeEvent(event_type="", payload={})

    async def call(
        self,
        *,
        object_id: str,
        class_name: str,
        method_name: str,
        args: list[object],
        requires_arm: bool = False,
        timeout: float | None = None,  # noqa: ASYNC109 -- backend deadline capability
    ) -> object:
        return None


def test_trading_backend_protocol() -> None:
    """Verify TradingBackend runtime checkable protocol."""
    assert isinstance(_MockBackend(), TradingBackend)


def test_description_mappings_and_timeframe_seconds() -> None:
    """Verify description dictionaries and timeframe duration mapping in contracts."""
    assert ORDER_TYPE_DESCRIPTIONS[OrderType.BUY] == "Buy"
    assert ORDER_FILLING_DESCRIPTIONS[OrderFilling.FOK] == "Fill or Kill"
    assert ORDER_TIME_DESCRIPTIONS[OrderTime.GTC] == "Good Till Cancelled"
    assert BOOK_TYPE_DESCRIPTIONS[BookType.BOOK_TYPE_SELL] == "Sell"
    assert POSITION_TYPE_DESCRIPTIONS[PositionType.BUY] == "Buy"
    assert ORDER_STATE_DESCRIPTIONS[OrderState.FILLED] == "Filled"
    assert DEAL_TYPE_DESCRIPTIONS[DealType.BUY] == "Buy"
    assert DEAL_ENTRY_DESCRIPTIONS[DealEntry.IN] == "In"
    assert SYMBOL_TRADE_MODE_DESCRIPTIONS[SymbolTradeMode.FULL] == "Full"
    assert SYMBOL_TRADE_EXECUTION_DESCRIPTIONS[SymbolTradeExecution.MARKET] == "Market"
    assert SYMBOL_SWAP_MODE_DESCRIPTIONS[SymbolSwapMode.POINTS] == "Points"
    assert SYMBOL_CALC_MODE_DESCRIPTIONS[SymbolCalcMode.FOREX] == "Forex"

    assert TIMEFRAME_SECONDS[Timeframe.PERIOD_M1] == 60
    assert TIMEFRAME_SECONDS[Timeframe.PERIOD_H1] == 3600
    assert Timeframe.PERIOD_CURRENT not in TIMEFRAME_SECONDS


def test_enums_module_strictly_only_enums() -> None:
    """Verify that app.services.include.enums contains strictly Enum subclasses."""
    from enum import Enum

    for name in enums.__all__:
        attr = getattr(enums, name)
        assert isinstance(attr, type) and issubclass(attr, Enum), (
            f"Non-enum found in enums.__all__: {name} ({attr})"
        )


def test_no_app_services_libs_module() -> None:
    """Verify that legacy app.services.libs package is completely removed without shims."""
    import importlib

    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("app.services.libs")
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("app.services.libs.contracts")
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("app.services.libs.enums")


def test_zero_shims_and_aliases_invariant() -> None:
    """Verify strict absence of legacy compatibility shims and aliases."""
    legacy_shims = [
        "MqlBookInfo",
        "SymbolSpec",
        "HistoryOrderSnapshot",
        "SymbolSnapshot",
        "AccountSnapshot",
        "TerminalSnapshot",
        "PositionSnapshot",
        "OrderSnapshot",
        "DealSnapshot",
        "InstrumentInfo",
        "InstrumentAliasRecord",
        "SWAP_MODE_DESCRIPTIONS",
    ]
    for shim in legacy_shims:
        assert not hasattr(contracts, shim), (
            f"Forbidden shim found in contracts: {shim}"
        )
        assert not hasattr(enums, shim), f"Forbidden shim found in enums: {shim}"

    # Invariant: SymbolInfo and DataInfo have zero self-identity adapter shims
    assert not hasattr(SymbolInfo, "to_symbol_info")
    assert not hasattr(DataInfo, "to_data_info")

    # Invariant: Timeframe has zero shorthand aliases
    shorthands = ["M1", "M5", "H1", "H4", "D1", "W1", "MN1"]
    for sh in shorthands:
        assert sh not in Timeframe.__members__, (
            f"Forbidden shorthand alias on Timeframe: {sh}"
        )
