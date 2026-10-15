"""Unit tests for canonical trading library contracts, proxies, and facade.

Description:
    Validates functionality, boundary conditions, serialization, type safety,
    property aliases, proxy dispatch, and error handling for all trading contracts,
    snapshots, enums, proxy classes (Trade, AccountInfo, SymbolInfo, TerminalInfo,
    PositionInfo, OrderInfo, HistoryOrderInfo, DealInfo), and the master Trading facade
    in app.services.trading.

Purpose:
    FEAT-TRADING-CONTRACTS-TESTS: Test suite for consolidated trading library.

Key Capabilities:
    - FR-TRADING-CONTRACTS-MODELS: Verify trading dataclasses, snapshots, and enums.
    - FR-TRADING-COMPOSITION: Verify Trading facade and child proxy composition.
    - FR-TRADING-MUTATION: Verify order execution, checks, and payload serialization.
    - FR-TRADING-STATE-QUERIES: Verify account, symbol, terminal, position, order queries.

Python API Usage:
    ```bash
    uv run pytest tests/unit/services/test_trading.py --no-cov
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_trading.py --no-cov
    ```
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from app.services.trading import (
    BOOK_TYPE_DESCRIPTIONS,
    ORDER_FILLING_DESCRIPTIONS,
    ORDER_TIME_DESCRIPTIONS,
    ORDER_TYPE_DESCRIPTIONS,
    AccountInfo,
    AccountSnapshot,
    AccountTradeMode,
    BaseTradingClass,
    BookInfo,
    BookType,
    BridgeEvent,
    DealInfo,
    DealSnapshot,
    HistoryOrderInfo,
    HistoryOrderSnapshot,
    MarginMode,
    MqlBookInfo,
    OrderFilling,
    OrderInfo,
    OrderSnapshot,
    OrderTime,
    OrderType,
    PositionInfo,
    PositionSnapshot,
    PropertyValue,
    Receipt,
    ReceiptStatus,
    StopoutMode,
    SymbolInfo,
    SymbolSnapshot,
    TerminalInfo,
    TerminalSnapshot,
    Trade,
    TradeAction,
    TradeCheckResult,
    TradeRequest,
    TradeResolution,
    TradeResult,
    TradeRetcode,
    Trading,
    TradingBackend,
    _build_trade_check_result,
    _build_trade_request,
    _build_trade_result,
    _serialize_dict_request,
    _serialize_request,
)


class MockTradingBackend:
    """Mock TradingBackend implementation capturing calls for verification."""

    def __init__(self) -> None:
        self.started = False
        self.closed = False
        self.armed = False
        self.connected_waited = False
        self.calls: list[dict[str, Any]] = []
        self.call_responses: dict[tuple[str, str], Any] = {}
        self.default_response: Any = None
        self._last_cmd_id: str | None = "cmd-12345"
        self._receipts: dict[str, Receipt] = {}
        self._events: list[BridgeEvent] = []

    async def start(self) -> None:
        self.started = True

    async def close(self) -> None:
        self.closed = True

    async def wait_connected(self, timeout: float | None = None) -> None:  # noqa: ASYNC109
        self.connected_waited = True

    def arm(self) -> None:
        self.armed = True

    def disarm(self) -> None:
        self.armed = False

    def is_armed(self) -> bool:
        return bool(self.armed)

    def is_started(self) -> bool:
        return bool(self.started)

    def is_closed(self) -> bool:
        return bool(self.closed)

    def last_command_id(self) -> str | None:
        return self._last_cmd_id

    def receipt(self, command_id: str) -> Receipt | None:
        return self._receipts.get(command_id)

    async def next_event(self, timeout: float | None = None) -> BridgeEvent:  # noqa: ASYNC109
        if self._events:
            return self._events.pop(0)
        return BridgeEvent(event_type="test", payload={})

    async def await_request_event(
        self,
        request_id: int,
        timeout: float | None = None,  # noqa: ASYNC109
    ) -> BridgeEvent:
        return BridgeEvent(
            event_type="request_correlated",
            payload={"request_id": request_id},
            request_id=request_id,
        )

    async def call(
        self,
        *,
        object_id: str,
        class_name: str,
        method_name: str,
        args: list[Any],
        requires_arm: bool = False,
        timeout: float | None = None,  # noqa: ASYNC109
    ) -> Any:
        call_entry = {
            "object_id": object_id,
            "class_name": class_name,
            "method_name": method_name,
            "args": args,
            "requires_arm": requires_arm,
        }
        self.calls.append(call_entry)
        key = (class_name, method_name)
        if key in self.call_responses:
            resp = self.call_responses[key]
            if isinstance(resp, Exception):
                raise resp
            return resp
        return self.default_response


# ============================================================================
# Enums and Description Maps
# ============================================================================


def test_trading_enums_values() -> None:
    """Verify enumerations define expected integer and string representations."""
    assert ReceiptStatus.CREATED.value == "created"
    assert ReceiptStatus.SENT.value == "sent"
    assert ReceiptStatus.ACKNOWLEDGED.value == "acknowledged"
    assert ReceiptStatus.RESOLVED.value == "resolved"
    assert ReceiptStatus.REJECTED.value == "rejected"
    assert ReceiptStatus.UNCERTAIN.value == "uncertain"

    assert TradeResolution.DISPATCHED.value == "dispatched"
    assert TradeResolution.PLACED.value == "placed"
    assert TradeResolution.FILLED.value == "filled"
    assert TradeResolution.PARTIALLY_FILLED.value == "partially_filled"
    assert TradeResolution.REJECTED.value == "rejected"
    assert TradeResolution.CANCELLED.value == "cancelled"
    assert TradeResolution.EXPIRED.value == "expired"
    assert TradeResolution.NOT_FOUND.value == "not_found"
    assert TradeResolution.UNCERTAIN.value == "uncertain"

    assert AccountTradeMode.DEMO.value == 0
    assert AccountTradeMode.CONTEST.value == 1
    assert AccountTradeMode.REAL.value == 2

    assert StopoutMode.PERCENT.value == 0
    assert StopoutMode.MONEY.value == 1

    assert MarginMode.RETAIL_NETTING.value == 0
    assert MarginMode.EXCHANGE.value == 1
    assert MarginMode.RETAIL_HEDGING.value == 2

    assert OrderType.BUY.value == 0
    assert OrderType.SELL.value == 1
    assert OrderType.BUY_LIMIT.value == 2
    assert OrderType.SELL_LIMIT.value == 3
    assert OrderType.BUY_STOP.value == 4
    assert OrderType.SELL_STOP.value == 5
    assert OrderType.CLOSE_BY.value == 8

    assert OrderFilling.FOK.value == 0
    assert OrderFilling.IOC.value == 1
    assert OrderFilling.RETURN.value == 2
    assert OrderFilling.BOC.value == 3

    assert OrderTime.GTC.value == 0
    assert OrderTime.DAY.value == 1
    assert OrderTime.SPECIFIED.value == 2
    assert OrderTime.SPECIFIED_DAY.value == 3

    assert TradeAction.DEAL.value == 1
    assert TradeAction.PENDING.value == 5
    assert TradeAction.SLTP.value == 6
    assert TradeAction.MODIFY.value == 7
    assert TradeAction.REMOVE.value == 8

    assert TradeRetcode.DONE.value == 10009
    assert TradeRetcode.ERROR.value == 10011
    assert TradeRetcode.NO_MONEY.value == 10019

    assert BookType.BOOK_TYPE_SELL.value == 1
    assert BookType.BOOK_TYPE_BUY.value == 2


def test_trading_backend_protocol() -> None:
    """Verify TradingBackend protocol exports and runtime conformance."""
    backend = MockTradingBackend()
    assert isinstance(backend, TradingBackend)


def test_trading_description_mappings() -> None:
    """Verify description dictionaries contain human-readable string descriptions."""
    for ot in OrderType:
        assert ot in ORDER_TYPE_DESCRIPTIONS
        assert isinstance(ORDER_TYPE_DESCRIPTIONS[ot], str)

    for of in OrderFilling:
        assert of in ORDER_FILLING_DESCRIPTIONS
        assert isinstance(ORDER_FILLING_DESCRIPTIONS[of], str)

    for otm in OrderTime:
        assert otm in ORDER_TIME_DESCRIPTIONS
        assert isinstance(ORDER_TIME_DESCRIPTIONS[otm], str)

    for bt in BookType:
        assert bt in BOOK_TYPE_DESCRIPTIONS
        assert isinstance(BOOK_TYPE_DESCRIPTIONS[bt], str)


# ============================================================================
# Dataclasses and Property Aliases
# ============================================================================


def test_property_value_and_receipt() -> None:
    """Verify PropertyValue and Receipt dataclasses."""
    pv = PropertyValue(ok=True, value="test_val")
    assert pv.ok is True
    assert pv.value == "test_val"
    assert pv.error is None

    rcpt = Receipt(
        command_id="cmd-1",
        object_id="obj-1",
        class_name="Trade",
        method_name="OrderSend",
        status=ReceiptStatus.RESOLVED,
        created_at=100.0,
        sent_at=100.1,
        resolved_at=100.5,
    )
    assert rcpt.command_id == "cmd-1"
    assert rcpt.status == ReceiptStatus.RESOLVED


def test_bridge_event() -> None:
    """Verify BridgeEvent dataclass."""
    ev = BridgeEvent(
        event_type="on_tick",
        payload={"symbol": "EURUSD", "bid": 1.05},
        command_id="c-1",
        request_id=42,
    )
    assert ev.event_type == "on_tick"
    assert ev.payload["bid"] == 1.05
    assert ev.request_id == 42


def test_book_info_properties() -> None:
    """Verify BookInfo and MqlBookInfo properties and dictionary serialization."""
    assert MqlBookInfo is BookInfo

    entry = BookInfo(
        type=BookType.BOOK_TYPE_BUY,
        price=1.0500,
        volume=10,
        volume_real=10.0,
    )
    assert entry.type_description == "Buy"
    d = entry._asdict()
    assert d["type"] == int(BookType.BOOK_TYPE_BUY)
    assert d["price"] == 1.0500
    assert d["volume"] == 10
    assert d["volume_real"] == 10.0

    # Fallback for unknown type
    unknown_entry = BookInfo(
        type=999,  # type: ignore[arg-type]
        price=1.0,
        volume=1,
        volume_real=1.0,
    )
    assert unknown_entry.type_description == "Unknown"


def test_account_snapshot_defaults() -> None:
    """Verify AccountSnapshot default attributes."""
    acc = AccountSnapshot(balance=25_000.0, equity=25_500.0)
    assert acc.balance == 25_000.0
    assert acc.equity == 25_500.0
    assert acc.trade_mode == AccountTradeMode.DEMO
    assert acc.margin_mode == MarginMode.RETAIL_HEDGING
    assert acc.currency == "USD"


def test_terminal_snapshot_defaults() -> None:
    """Verify TerminalSnapshot default attributes."""
    term = TerminalSnapshot(build=4500, connected=True)
    assert term.build == 4500
    assert term.connected is True
    assert term.max_bars == 100_000


def test_symbol_snapshot_aliases() -> None:
    """Verify SymbolSnapshot property aliases match underlying fields."""
    sym = SymbolSnapshot(
        volume_min=0.01,
        volume_max=50.0,
        volume_step=0.01,
        volume_limit=100.0,
        trade_tick_size=0.00001,
        trade_tick_value=1.0,
        trade_contract_size=100_000.0,
        trade_stops_level=5,
        trade_freeze_level=2,
    )
    assert sym.lots_min == 0.01
    assert sym.lots_max == 50.0
    assert sym.lots_step == 0.01
    assert sym.lots_limit == 100.0
    assert sym.tick_size == 0.00001
    assert sym.tick_value == 1.0
    assert sym.contract_size == 100_000.0
    assert sym.stops_level == 5
    assert sym.freeze_level == 2


def test_position_snapshot_aliases() -> None:
    """Verify PositionSnapshot property aliases."""
    pos = PositionSnapshot(
        ticket=123,
        symbol="EURUSD",
        position_type=0,
        sl=1.0450,
        tp=1.0600,
    )
    assert pos.stop_loss == 1.0450
    assert pos.take_profit == 1.0600
    assert pos.type == 0


def test_order_snapshot_aliases() -> None:
    """Verify OrderSnapshot and HistoryOrderSnapshot aliases."""
    assert HistoryOrderSnapshot is OrderSnapshot

    order = OrderSnapshot(
        ticket=456,
        symbol="GBPUSD",
        order_type=1,
        sl=1.2900,
        tp=1.2800,
    )
    assert order.stop_loss == 1.2900
    assert order.take_profit == 1.2800
    assert order.type == 1


def test_deal_snapshot_aliases() -> None:
    """Verify DealSnapshot property aliases."""
    deal = DealSnapshot(
        ticket=789,
        order=456,
        deal_type=0,
    )
    assert deal.order_ticket == 456
    assert deal.type == 0


def test_trade_request_result_check_dataclasses() -> None:
    """Verify TradeRequest, TradeResult, and TradeCheckResult instantiation."""
    req = TradeRequest(
        action=TradeAction.DEAL,
        symbol="EURUSD",
        volume=0.1,
        price=1.0550,
    )
    assert req.action == TradeAction.DEAL
    assert req.symbol == "EURUSD"
    assert req.volume == 0.1
    assert req.order_type == OrderType.BUY
    assert req.type_filling == OrderFilling.FOK

    res = TradeResult(retcode=int(TradeRetcode.DONE), deal=101, order=202)
    assert res.retcode == int(TradeRetcode.DONE)
    assert res.deal == 101
    assert res.order == 202

    check = TradeCheckResult(retcode=int(TradeRetcode.DONE), margin=100.0)
    assert check.retcode == int(TradeRetcode.DONE)
    assert check.margin == 100.0


# ============================================================================
# Serialization Functions
# ============================================================================


def test_serialize_trade_request() -> None:
    """Verify _serialize_request correctly converts TradeRequest to dict."""
    exp_time = datetime(2026, 12, 31, 23, 59, 59, tzinfo=UTC)
    req = TradeRequest(
        action=TradeAction.DEAL,
        symbol="EURUSD",
        volume=0.5,
        order_type=OrderType.SELL,
        price=1.0500,
        stoplimit=0.0,
        sl=1.0600,
        tp=1.0400,
        deviation=10,
        magic=123456,
        order=0,
        position=0,
        position_by=0,
        type_filling=OrderFilling.IOC,
        type_time=OrderTime.SPECIFIED,
        expiration=exp_time,
        comment="test order",
    )
    data = _serialize_request(req)
    assert data["action"] == int(TradeAction.DEAL)
    assert data["symbol"] == "EURUSD"
    assert data["volume"] == 0.5
    assert data["order_type"] == int(OrderType.SELL)
    assert data["type_filling"] == int(OrderFilling.IOC)
    assert data["type_time"] == int(OrderTime.SPECIFIED)
    assert data["expiration"] == int(exp_time.timestamp())
    assert data["comment"] == "test order"


def test_serialize_trade_request_naive_datetime_raises() -> None:
    """Verify naive datetime in TradeRequest raises ValueError."""
    req = TradeRequest(
        action=TradeAction.DEAL,
        expiration=datetime(2026, 1, 1, 0, 0, 0),  # noqa: DTZ001 -- testing naive datetime
    )
    with pytest.raises(ValueError, match="trading datetimes must include a timezone"):
        _serialize_request(req)


def test_serialize_dict_request() -> None:
    """Verify _serialize_dict_request converts enums and datetimes in dicts."""
    exp_time = datetime(2026, 6, 1, 12, 0, 0, tzinfo=UTC)
    d = {
        "action": TradeAction.PENDING,
        "order_type": OrderType.BUY_LIMIT,
        "type_filling": OrderFilling.RETURN,
        "type_time": OrderTime.DAY,
        "expiration": exp_time,
        "symbol": "BTCUSD",
    }
    serialized = _serialize_dict_request(d)
    assert serialized["action"] == int(TradeAction.PENDING)
    assert serialized["order_type"] == int(OrderType.BUY_LIMIT)
    assert serialized["type_filling"] == int(OrderFilling.RETURN)
    assert serialized["type_time"] == int(OrderTime.DAY)
    assert serialized["expiration"] == int(exp_time.timestamp())

    # Naive datetime in dict
    naive_d = {
        "action": 1,
        "expiration": datetime(2026, 1, 1, 0, 0),  # noqa: DTZ001 -- testing naive
    }
    with pytest.raises(ValueError, match="trading datetimes must include a timezone"):
        _serialize_dict_request(naive_d)


def test_build_trade_request_result_check() -> None:
    """Verify _build_trade_request, _build_trade_result, _build_trade_check_result."""
    now_ts = 1700000000.0
    req_dict = {
        "action": int(TradeAction.DEAL),
        "order_type": int(OrderType.BUY),
        "type_filling": int(OrderFilling.FOK),
        "type_time": int(OrderTime.GTC),
        "expiration": now_ts,
        "symbol": "EURUSD",
        "volume": 1.0,
    }
    req = _build_trade_request(req_dict)
    assert req.action == TradeAction.DEAL
    assert req.order_type == OrderType.BUY
    assert req.expiration == datetime.fromtimestamp(now_ts, tz=UTC)

    # Date already as datetime
    req_dict_dt = {
        "action": TradeAction.SLTP,
        "expiration": datetime.now(UTC),
    }
    req2 = _build_trade_request(req_dict_dt)
    assert req2.action == TradeAction.SLTP
    assert isinstance(req2.expiration, datetime)

    res = _build_trade_result({"retcode": 10009, "deal": 10, "order": 20})
    assert res.retcode == 10009
    assert res.deal == 10
    assert res.order == 20

    check = _build_trade_check_result({"retcode": 10009, "margin": 500.0})
    assert check.retcode == 10009
    assert check.margin == 500.0


# ============================================================================
# BaseTradingClass / Proxy Dispatch
# ============================================================================


@pytest.mark.anyio
async def test_trading_class_dispatch_and_property() -> None:
    """Verify TradingClass converts datetime args and unpacks property values."""
    backend = MockTradingBackend()
    backend.default_response = {"ok": True, "value": "test_ok"}

    proxy = BaseTradingClass(backend, object_id="test-proxy-1")
    assert proxy.object_id == "test-proxy-1"
    assert proxy.last_command_id == "cmd-12345"

    aware_dt = datetime(2026, 10, 14, 12, 0, tzinfo=UTC)
    res = await proxy._property("TestMethod", "arg1", aware_dt)
    assert isinstance(res, PropertyValue)
    assert res.ok is True
    assert res.value == "test_ok"

    # Verify wire args converted datetime to integer timestamp
    assert len(backend.calls) == 1
    call = backend.calls[0]
    assert call["args"][0] == "arg1"
    assert call["args"][1] == int(aware_dt.timestamp())

    # Naive datetime must raise ValueError
    naive_dt = datetime(2026, 10, 14, 12, 0)  # noqa: DTZ001 -- testing naive datetime
    with pytest.raises(ValueError, match="trading datetimes must include a timezone"):
        await proxy._call("TestMethod", naive_dt)


# ============================================================================
# AccountInfo Proxy
# ============================================================================


@pytest.mark.anyio
async def test_account_info_proxy() -> None:
    """Verify AccountInfo proxy methods."""
    backend = MockTradingBackend()
    backend.call_responses[("AccountInfo", "AccountInfo")] = {
        "login": 99999,
        "balance": 50_000.0,
        "equity": 52_000.0,
    }
    backend.call_responses[("AccountInfo", "OrderProfitCheck")] = 150.0
    backend.call_responses[("AccountInfo", "MarginCheck")] = 500.0
    backend.call_responses[("AccountInfo", "FreeMarginCheck")] = 49_500.0
    backend.call_responses[("AccountInfo", "MaxLotCheck")] = 10.0

    acc = AccountInfo(backend)

    # Via method
    info = await acc.AccountInfo()
    assert isinstance(info, AccountSnapshot)
    assert info.login == 99999
    assert info.balance == 50_000.0

    # Via __call__
    info2 = await acc()
    assert isinstance(info2, AccountSnapshot)
    assert info2.equity == 52_000.0

    # Pre-instantiated snapshot return
    backend.call_responses[("AccountInfo", "AccountInfo")] = AccountSnapshot(
        login=11111, balance=1000.0
    )
    info3 = await acc.AccountInfo()
    assert info3.login == 11111

    # Invalid return type raises TypeError
    backend.call_responses[("AccountInfo", "AccountInfo")] = "unexpected_string"
    with pytest.raises(TypeError, match="unexpected account snapshot type"):
        await acc.AccountInfo()

    # Checks
    assert await acc.OrderProfitCheck("EURUSD", 0, 1.0, 1.05, 1.06) == 150.0
    assert await acc.MarginCheck("EURUSD", 0, 1.0, 1.05) == 500.0
    assert await acc.FreeMarginCheck("EURUSD", 0, 1.0, 1.05) == 49_500.0
    assert await acc.MaxLotCheck("EURUSD", 0, 1.05) == 10.0


# ============================================================================
# TerminalInfo Proxy
# ============================================================================


@pytest.mark.anyio
async def test_terminal_info_proxy() -> None:
    """Verify TerminalInfo proxy methods."""
    backend = MockTradingBackend()
    backend.call_responses[("TerminalInfo", "TerminalInfo")] = {
        "build": 5000,
        "connected": True,
        "name": "Live Terminal",
    }
    term = TerminalInfo(backend)

    info = await term.TerminalInfo()
    assert isinstance(info, TerminalSnapshot)
    assert info.build == 5000
    assert info.name == "Live Terminal"

    # Via __call__
    info2 = await term()
    assert isinstance(info2, TerminalSnapshot)
    assert info2.connected is True

    # Pre-instantiated snapshot return
    backend.call_responses[("TerminalInfo", "TerminalInfo")] = TerminalSnapshot(
        build=5001
    )
    info3 = await term.TerminalInfo()
    assert info3.build == 5001

    # Invalid type
    backend.call_responses[("TerminalInfo", "TerminalInfo")] = 12345
    with pytest.raises(TypeError, match="unexpected terminal snapshot type"):
        await term.TerminalInfo()


# ============================================================================
# SymbolInfo Proxy
# ============================================================================


@pytest.mark.anyio
async def test_symbol_info_proxy() -> None:
    """Verify SymbolInfo proxy methods including MarketBook queries."""
    backend = MockTradingBackend()
    sym_data = {
        "name": "EURUSD",
        "digits": 5,
        "ask": 1.0550,
        "bid": 1.0548,
    }
    backend.call_responses[("SymbolInfo", "SymbolInfo")] = sym_data
    backend.call_responses[("SymbolInfo", "as_dict")] = sym_data
    backend.call_responses[("SymbolInfo", "Refresh")] = True
    backend.call_responses[("SymbolInfo", "RefreshRates")] = True
    backend.call_responses[("SymbolInfo", "Name")] = "EURUSD"
    backend.call_responses[("SymbolInfo", "Select")] = True
    backend.call_responses[("SymbolInfo", "IsSynchronized")] = True
    backend.call_responses[("SymbolInfo", "NormalizePrice")] = 1.05500
    backend.call_responses[("SymbolInfo", "SymbolsTotal")] = 50
    backend.call_responses[("SymbolInfo", "SymbolsGet")] = ["EURUSD", "GBPUSD"]
    backend.call_responses[("SymbolInfo", "SymbolInfoTick")] = {"bid": 1.0548}
    backend.call_responses[("SymbolInfo", "SymbolSelect")] = True
    backend.call_responses[("SymbolInfo", "MarketBookAdd")] = True
    backend.call_responses[("SymbolInfo", "MarketBookGet")] = [
        {"type": 2, "price": 1.0550, "volume": 10, "volume_real": 10.0},
        BookInfo(type=BookType.BOOK_TYPE_SELL, price=1.0552, volume=5, volume_real=5.0),
    ]
    backend.call_responses[("SymbolInfo", "MarketBookRelease")] = True

    symbol = SymbolInfo(backend)

    info = await symbol.SymbolInfo("EURUSD")
    assert isinstance(info, SymbolSnapshot)
    assert info.name == "EURUSD"
    assert info.digits == 5

    # Via __call__
    info2 = await symbol("EURUSD")
    assert isinstance(info2, SymbolSnapshot)

    # as_dict
    d = await symbol.as_dict("EURUSD")
    assert isinstance(d, dict)
    assert d["name"] == "EURUSD"

    # as_dict with SymbolSnapshot response
    backend.call_responses[("SymbolInfo", "as_dict")] = SymbolSnapshot(name="GBPUSD")
    d2 = await symbol.as_dict("GBPUSD")
    assert d2["name"] == "GBPUSD"

    # Invalid type for SymbolInfo
    backend.call_responses[("SymbolInfo", "SymbolInfo")] = 999
    with pytest.raises(TypeError, match="unexpected symbol snapshot type"):
        await symbol.SymbolInfo("EURUSD")

    # Invalid type for as_dict
    backend.call_responses[("SymbolInfo", "as_dict")] = 999
    with pytest.raises(TypeError, match="unexpected symbol dictionary type"):
        await symbol.as_dict("EURUSD")

    # Native operations
    assert await symbol.Refresh() is True
    assert await symbol.RefreshRates() is True
    assert await symbol.Name() == "EURUSD"
    assert await symbol.Select(True) is True
    assert await symbol.IsSynchronized() is True
    assert await symbol.NormalizePrice(1.055) == 1.05500
    assert await symbol.SymbolsTotal() == 50
    assert await symbol.SymbolsGet() == ["EURUSD", "GBPUSD"]
    assert await symbol.SymbolInfoTick("EURUSD") == {"bid": 1.0548}
    assert await symbol.SymbolSelect("EURUSD", True) is True

    # Market Book
    assert await symbol.MarketBookAdd("EURUSD") is True
    books = await symbol.MarketBookGet("EURUSD")
    assert len(books) == 2
    assert books[0].type == BookType.BOOK_TYPE_BUY
    assert books[1].type == BookType.BOOK_TYPE_SELL
    assert await symbol.MarketBookRelease("EURUSD") is True

    # MarketBookGet empty
    backend.call_responses[("SymbolInfo", "MarketBookGet")] = None
    assert await symbol.MarketBookGet("EURUSD") == ()


# ============================================================================
# PositionInfo Proxy
# ============================================================================


@pytest.mark.anyio
async def test_position_info_proxy() -> None:
    """Verify PositionInfo proxy methods and collection queries."""
    backend = MockTradingBackend()
    pos_data = {
        "ticket": 1234,
        "symbol": "EURUSD",
        "volume": 0.5,
        "price_open": 1.0500,
    }
    backend.call_responses[("PositionInfo", "PositionInfo")] = pos_data
    backend.call_responses[("PositionInfo", "as_dict")] = pos_data
    backend.call_responses[("PositionInfo", "Select")] = True
    backend.call_responses[("PositionInfo", "SelectByIndex")] = True
    backend.call_responses[("PositionInfo", "SelectByMagic")] = True
    backend.call_responses[("PositionInfo", "SelectByTicket")] = True
    backend.call_responses[("PositionInfo", "StoreState")] = True
    backend.call_responses[("PositionInfo", "CheckState")] = True
    backend.call_responses[("PositionInfo", "PositionsTotal")] = 1
    backend.call_responses[("PositionInfo", "PositionsGet")] = [
        pos_data,
        PositionSnapshot(ticket=1235, symbol="GBPUSD"),
    ]

    pos = PositionInfo(backend)

    info = await pos.PositionInfo()
    assert isinstance(info, PositionSnapshot)
    assert info.ticket == 1234

    # Via __call__
    info2 = await pos()
    assert isinstance(info2, PositionSnapshot)

    # as_dict
    d = await pos.as_dict()
    assert d["ticket"] == 1234

    backend.call_responses[("PositionInfo", "as_dict")] = PositionSnapshot(ticket=999)
    d2 = await pos.as_dict()
    assert d2["ticket"] == 999

    # Invalid type
    backend.call_responses[("PositionInfo", "PositionInfo")] = "bad"
    with pytest.raises(TypeError, match="unexpected position snapshot type"):
        await pos.PositionInfo()

    backend.call_responses[("PositionInfo", "as_dict")] = "bad"
    with pytest.raises(TypeError, match="unexpected position dictionary type"):
        await pos.as_dict()

    # Operations
    assert await pos.Select("EURUSD") is True
    assert await pos.SelectByIndex(0) is True
    assert await pos.SelectByMagic("EURUSD", 123) is True
    assert await pos.SelectByTicket(1234) is True
    assert await pos.StoreState() is True
    assert await pos.CheckState() is True
    assert await pos.PositionsTotal() == 1

    # PositionsGet
    positions = await pos.PositionsGet(symbol="EURUSD")
    assert len(positions) == 2
    assert positions[0].ticket == 1234
    assert positions[1].ticket == 1235

    # PositionsGet error
    backend.call_responses[("PositionInfo", "PositionsGet")] = "not_a_list"
    with pytest.raises(TypeError, match="unexpected PositionsGet return type"):
        await pos.PositionsGet()


# ============================================================================
# OrderInfo & HistoryOrderInfo Proxies
# ============================================================================


@pytest.mark.anyio
async def test_order_info_proxy() -> None:
    """Verify OrderInfo proxy methods and collection queries."""
    backend = MockTradingBackend()
    order_data = {"ticket": 5678, "symbol": "EURUSD", "order_type": 0}
    backend.call_responses[("OrderInfo", "OrderInfo")] = order_data
    backend.call_responses[("OrderInfo", "as_dict")] = order_data
    backend.call_responses[("OrderInfo", "Select")] = True
    backend.call_responses[("OrderInfo", "SelectByIndex")] = True
    backend.call_responses[("OrderInfo", "StoreState")] = True
    backend.call_responses[("OrderInfo", "CheckState")] = True
    backend.call_responses[("OrderInfo", "OrdersTotal")] = 1
    backend.call_responses[("OrderInfo", "OrdersGet")] = [
        order_data,
        OrderSnapshot(ticket=5679),
    ]

    orders = OrderInfo(backend)

    info = await orders.OrderInfo()
    assert isinstance(info, OrderSnapshot)
    assert info.ticket == 5678

    info2 = await orders()
    assert info2.ticket == 5678

    d = await orders.as_dict()
    assert d["ticket"] == 5678

    backend.call_responses[("OrderInfo", "as_dict")] = OrderSnapshot(ticket=999)
    assert (await orders.as_dict())["ticket"] == 999

    assert await orders.Select(5678) is True
    assert await orders.SelectByIndex(0) is True
    assert await orders.StoreState() is True
    assert await orders.CheckState() is True
    assert await orders.OrdersTotal() == 1

    ord_list = await orders.OrdersGet(symbol="EURUSD")
    assert len(ord_list) == 2

    # Error handling
    backend.call_responses[("OrderInfo", "OrderInfo")] = 42
    with pytest.raises(TypeError, match="unexpected order snapshot type"):
        await orders.OrderInfo()

    backend.call_responses[("OrderInfo", "as_dict")] = 42
    with pytest.raises(TypeError, match="unexpected order dictionary type"):
        await orders.as_dict()

    backend.call_responses[("OrderInfo", "OrdersGet")] = "bad"
    with pytest.raises(TypeError, match="unexpected OrdersGet return type"):
        await orders.OrdersGet()


@pytest.mark.anyio
async def test_history_order_info_proxy() -> None:
    """Verify HistoryOrderInfo proxy methods."""
    backend = MockTradingBackend()
    horder_data = {"ticket": 9012, "symbol": "EURUSD"}
    backend.call_responses[("HistoryOrderInfo", "HistoryOrderInfo")] = horder_data
    backend.call_responses[("HistoryOrderInfo", "as_dict")] = horder_data
    backend.call_responses[("HistoryOrderInfo", "Ticket")] = 9012
    backend.call_responses[("HistoryOrderInfo", "SelectByIndex")] = True
    backend.call_responses[("HistoryOrderInfo", "HistoryOrdersTotal")] = 5
    backend.call_responses[("HistoryOrderInfo", "HistoryOrdersGet")] = [
        horder_data,
        HistoryOrderSnapshot(ticket=9013),
    ]

    horders = HistoryOrderInfo(backend)

    info = await horders.HistoryOrderInfo()
    assert isinstance(info, HistoryOrderSnapshot)
    assert info.ticket == 9012

    info2 = await horders()
    assert info2.ticket == 9012

    d = await horders.as_dict()
    assert d["ticket"] == 9012

    backend.call_responses[("HistoryOrderInfo", "as_dict")] = HistoryOrderSnapshot(
        ticket=1000
    )
    assert (await horders.as_dict())["ticket"] == 1000

    assert await horders.Ticket() == 9012
    assert await horders.SelectByIndex(0) is True
    assert await horders.HistoryOrdersTotal() == 5
    assert await horders.HistoryOrdersTotal(position=100) == 5

    res_list = await horders.HistoryOrdersGet(ticket=9012)
    assert len(res_list) == 2

    # Error handling
    backend.call_responses[("HistoryOrderInfo", "HistoryOrderInfo")] = 42
    with pytest.raises(TypeError, match="unexpected history order snapshot type"):
        await horders.HistoryOrderInfo()

    backend.call_responses[("HistoryOrderInfo", "as_dict")] = 42
    with pytest.raises(TypeError, match="unexpected history order dictionary type"):
        await horders.as_dict()

    backend.call_responses[("HistoryOrderInfo", "HistoryOrdersGet")] = 42
    with pytest.raises(TypeError, match="unexpected HistoryOrdersGet return type"):
        await horders.HistoryOrdersGet()


# ============================================================================
# DealInfo Proxy
# ============================================================================


@pytest.mark.anyio
async def test_deal_info_proxy() -> None:
    """Verify DealInfo proxy methods."""
    backend = MockTradingBackend()
    deal_data = {"ticket": 3456, "order": 1234, "deal_type": 0}
    backend.call_responses[("DealInfo", "DealInfo")] = deal_data
    backend.call_responses[("DealInfo", "as_dict")] = deal_data
    backend.call_responses[("DealInfo", "Ticket")] = 3456
    backend.call_responses[("DealInfo", "SelectByIndex")] = True
    backend.call_responses[("DealInfo", "HistoryDealsTotal")] = 3
    backend.call_responses[("DealInfo", "HistoryDealsGet")] = [
        deal_data,
        DealSnapshot(ticket=3457),
    ]

    deals = DealInfo(backend)

    info = await deals.DealInfo()
    assert isinstance(info, DealSnapshot)
    assert info.ticket == 3456

    info2 = await deals()
    assert info2.ticket == 3456

    d = await deals.as_dict()
    assert d["ticket"] == 3456

    backend.call_responses[("DealInfo", "as_dict")] = DealSnapshot(ticket=999)
    assert (await deals.as_dict())["ticket"] == 999

    assert await deals.Ticket() == 3456
    assert await deals.SelectByIndex(0) is True
    assert await deals.HistoryDealsTotal() == 3
    assert await deals.HistoryDealsTotal(position=200) == 3

    res_list = await deals.HistoryDealsGet(ticket=3456)
    assert len(res_list) == 2

    # Error handling
    backend.call_responses[("DealInfo", "DealInfo")] = 42
    with pytest.raises(TypeError, match="unexpected deal snapshot type"):
        await deals.DealInfo()

    backend.call_responses[("DealInfo", "as_dict")] = 42
    with pytest.raises(TypeError, match="unexpected deal dictionary type"):
        await deals.as_dict()

    backend.call_responses[("DealInfo", "HistoryDealsGet")] = 42
    with pytest.raises(TypeError, match="unexpected HistoryDealsGet return type"):
        await deals.HistoryDealsGet()


# ============================================================================
# Trade Execution Proxy
# ============================================================================


@pytest.mark.anyio
async def test_trade_proxy_order_send_and_check() -> None:
    """Verify Trade.OrderSend, OrderCheck, parameters, and metadata."""
    backend = MockTradingBackend()
    backend.call_responses[("Trade", "OrderSend")] = {
        "retcode": int(TradeRetcode.DONE),
        "deal": 1001,
        "order": 2001,
        "volume": 0.1,
        "price": 1.0550,
        "comment": "Done deal",
    }
    backend.call_responses[("Trade", "OrderCheck")] = {
        "retcode": int(TradeRetcode.DONE),
        "balance": 10_000.0,
        "margin": 100.0,
        "comment": "Check passed",
    }
    backend.call_responses[("Trade", "LogLevel")] = True
    backend.call_responses[("Trade", "SetExpertMagicNumber")] = None
    backend.call_responses[("Trade", "SetDeviationInPoints")] = None
    backend.call_responses[("Trade", "SetTypeFilling")] = None
    backend.call_responses[("Trade", "SetTypeFillingBySymbol")] = True
    backend.call_responses[("Trade", "SetAsyncMode")] = None
    backend.call_responses[("Trade", "SetMarginMode")] = None
    backend.call_responses[("Trade", "Request")] = {
        "action": 1,
        "symbol": "EURUSD",
        "volume": 0.1,
    }
    backend.call_responses[("Trade", "Result")] = {
        "retcode": int(TradeRetcode.DONE),
        "deal": 1001,
    }
    backend.call_responses[("Trade", "CheckResult")] = {
        "retcode": int(TradeRetcode.DONE),
        "margin": 100.0,
    }
    backend.call_responses[("Trade", "PrintRequest")] = True
    backend.call_responses[("Trade", "PrintResult")] = True
    backend.call_responses[("Trade", "FormatRequest")] = "Request: EURUSD BUY 0.1"
    backend.call_responses[("Trade", "FormatRequestResult")] = (
        "Request: ... Result: ..."
    )

    trade = Trade(backend)

    # LogLevel & configuration
    assert await trade.LogLevel(1) is True
    await trade.SetExpertMagicNumber(12345)
    await trade.SetDeviationInPoints(20)
    await trade.SetTypeFilling(OrderFilling.IOC)
    await trade.SetTypeFilling(1)
    assert await trade.SetTypeFillingBySymbol("EURUSD") is True
    await trade.SetAsyncMode(True)
    await trade.SetMarginMode()

    # OrderSend
    req = TradeRequest(action=TradeAction.DEAL, symbol="EURUSD", volume=0.1)
    out_res = TradeResult()
    result = await trade.OrderSend(req, out_res)
    assert result.retcode == int(TradeRetcode.DONE)
    assert result.deal == 1001
    assert out_res.deal == 1001

    # Via __call__
    result2 = await trade(req)
    assert result2.deal == 1001

    # OrderCheck
    out_check = TradeCheckResult()
    check = await trade.OrderCheck(req, out_check)
    assert check.retcode == int(TradeRetcode.DONE)
    assert check.margin == 100.0
    assert out_check.margin == 100.0

    # Inspection
    assert (await trade.Request()).symbol == "EURUSD"
    assert (await trade.Result()).deal == 1001
    assert (await trade.CheckResult()).margin == 100.0
    assert await trade.PrintRequest() is True
    assert await trade.PrintResult() is True
    assert "EURUSD" in await trade.FormatRequest()
    assert "Result" in await trade.FormatRequestResult()


# ============================================================================
# Master Trading Facade
# ============================================================================


@pytest.mark.anyio
async def test_master_trading_facade() -> None:
    """Verify Trading facade instantiates all eight proxies and manages lifecycle."""
    backend = MockTradingBackend()
    backend._receipts["cmd-test"] = Receipt(
        command_id="cmd-test",
        object_id="obj-test",
        class_name="Trade",
        method_name="OrderSend",
        status=ReceiptStatus.RESOLVED,
        created_at=100.0,
    )
    backend._events.append(BridgeEvent(event_type="on_quote", payload={"bid": 1.05}))

    trading = Trading(backend)

    # Check child proxies
    assert isinstance(trading.trade, Trade)
    assert isinstance(trading.account, AccountInfo)
    assert isinstance(trading.symbol, SymbolInfo)
    assert isinstance(trading.order, OrderInfo)
    assert isinstance(trading.history_order, HistoryOrderInfo)
    assert isinstance(trading.position, PositionInfo)
    assert isinstance(trading.deal, DealInfo)
    assert isinstance(trading.terminal, TerminalInfo)

    # Lifecycle
    await trading.start()
    assert backend.is_started()

    await trading.wait_connected(timeout=5.0)
    assert backend.connected_waited is True

    trading.arm()
    assert backend.is_armed()

    trading.disarm()
    assert not backend.is_armed()

    assert trading.last_command_id() == "cmd-12345"

    rcpt = trading.receipt("cmd-test")
    assert rcpt is not None
    assert rcpt.status == ReceiptStatus.RESOLVED

    ev = await trading.next_event(timeout=1.0)
    assert ev.event_type == "on_quote"

    req_ev = await trading.await_request_event(99)
    assert req_ev.request_id == 99

    await trading.close()
    assert backend.is_closed()

    # Async context manager
    backend.started = False
    backend.closed = False
    async with Trading(backend) as active_trading:
        assert isinstance(active_trading, Trading)
        assert backend.is_started()
    assert backend.is_closed()
