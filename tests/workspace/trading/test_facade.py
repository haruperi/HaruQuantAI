"""Unit tests for the centralized live trading facade and proxies.

Description:
    Validates Trading facade composition, TradingRuntime structural protocol compliance,
    proxy delegation, request serialization, collection filtering, and volume guards.
"""

from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any, override

import pytest
from app.core.data.contracts import (
    BookInfo,
    SymbolInfo,
)
from app.core.enums import (
    BookType,
    OrderFilling,
    OrderType,
    ReceiptStatus,
    TradeAction,
    TradeRetcode,
)
from app.core.trading.connection.contracts import (
    AccountInfo,
    BridgeError,
    BridgeEvent,
    DealInfo,
    OrderInfo,
    PositionInfo,
    Receipt,
    TerminalInfo,
    TradeCheckResult,
    TradeRequest,
    TradeResult,
    TradingBackend,
)
from app.workspace.trading import (
    AccountProxy,
    DealProxy,
    ExitManager,
    HistoryOrderProxy,
    OrderProxy,
    PositionProxy,
    SymbolProxy,
    TerminalProxy,
    Trade,
    Trading,
)
from app.workspace.trading.base import (
    TradingClass,
    build_trade_check_result,
    build_trade_result,
    normalize_request,
    serialize_request,
)


class MockBackend(TradingBackend):
    """Configurable mock backend implementing TradingBackend."""

    def __init__(self) -> None:
        self.started: bool = False
        self.closed: bool = False
        self.armed: bool = False
        self.connected: bool = True
        self.calls: list[dict[str, Any]] = []
        self.responses: dict[str, Any] = {}
        self._last_cmd: str | None = None
        self._receipts: dict[str, Receipt] = {}
        self.events: list[BridgeEvent] = []

    @property
    def is_armed(self) -> bool:
        return self.armed

    @override
    async def start(self) -> None:
        self.started = True

    @override
    async def wait_connected(
        self,
        timeout: float | None = None,
    ) -> None:
        if not self.connected:
            raise TimeoutError("Backend connection timed out")

    @override
    def arm(self) -> None:
        self.armed = True

    @override
    def disarm(self) -> None:
        self.armed = False

    @override
    async def close(self) -> None:
        self.closed = True

    @override
    def last_command_id(self) -> str | None:
        return self._last_cmd

    @override
    def receipt(self, command_id: str) -> Receipt | None:
        return self._receipts.get(command_id)

    @override
    async def next_event(
        self,
        timeout: float | None = None,
    ) -> BridgeEvent:
        if self.events:
            return self.events.pop(0)
        return BridgeEvent(event_type="heartbeat", payload={})

    @override
    async def await_request_event(
        self,
        request_id: int,
        timeout: float | None = None,
    ) -> BridgeEvent:
        return BridgeEvent(event_type="done", payload={"request_id": request_id})

    @override
    async def call(
        self,
        *,
        object_id: str,
        class_name: str,
        method_name: str,
        args: list[Any],
        requires_arm: bool = False,
        timeout: float | None = None,
    ) -> Any:
        self._last_cmd = f"cmd-{len(self.calls) + 1}"
        if requires_arm and not self.armed:
            self._receipts[self._last_cmd] = Receipt(
                command_id=self._last_cmd,
                object_id=object_id,
                class_name=class_name,
                method_name=method_name,
                status=ReceiptStatus.REJECTED,
                created_at=datetime.now(tz=UTC).timestamp(),
                error={"code": "NOT_ARMED"},
            )
            raise BridgeError("Operation requires arming", code="NOT_ARMED")

        self.calls.append(
            {
                "object_id": object_id,
                "class_name": class_name,
                "method_name": method_name,
                "args": args,
            }
        )
        self._receipts[self._last_cmd] = Receipt(
            command_id=self._last_cmd,
            object_id=object_id,
            class_name=class_name,
            method_name=method_name,
            status=ReceiptStatus.RESOLVED,
            created_at=datetime.now(tz=UTC).timestamp(),
        )
        key = f"{class_name}.{method_name}"
        if key in self.responses:
            val = self.responses[key]
            return val(args) if callable(val) else val
        return {"ok": True}


def sample_symbol(name: str = "EURUSD", filling: str = "Fill or Kill") -> SymbolInfo:
    info = SymbolInfo(name=name)
    info.price.bid = 1.10000
    info.price.ask = 1.10020
    info.price.tick_size = 0.00001
    info.price.tick_step = 0.00001
    info.volume.min = 0.01
    info.volume.max = 100.0
    info.volume.step = 0.01
    info.trade.filling = [filling]
    info.trade.execution = "Market"
    info.trade.stops_level = 10
    info.trade.freeze_level = 0
    return info


def test_trading_facade_composition_and_protocol() -> None:
    backend = MockBackend()
    trading = Trading(backend)

    # Assert structural protocol compatibility
    assert hasattr(trading, "position")
    assert hasattr(trading, "order")
    assert hasattr(trading, "account")
    assert hasattr(trading, "symbol")
    assert hasattr(trading, "deal")
    assert hasattr(trading, "trade")

    assert isinstance(trading.account, AccountProxy)
    assert isinstance(trading.symbol, SymbolProxy)
    assert isinstance(trading.order, OrderProxy)
    assert isinstance(trading.position, PositionProxy)
    assert isinstance(trading.deal, DealProxy)
    assert isinstance(trading.history_order, HistoryOrderProxy)
    assert isinstance(trading.terminal, TerminalProxy)
    assert isinstance(trading.trade, Trade)
    assert isinstance(trading.exits, ExitManager)

    # State isolation across distinct trading instances
    trading2 = Trading(backend)
    assert trading.trade.object_id != trading2.trade.object_id
    assert trading.account.object_id != trading2.account.object_id


def test_facade_lifecycle_and_events() -> None:
    async def scenario() -> None:
        backend = MockBackend()
        trading = Trading(backend)

        await trading.start()
        assert backend.started

        await trading.wait_connected(timeout=1.0)

        trading.arm()
        assert backend.is_armed is True
        trading.disarm()

        ev = await trading.next_event(timeout=0.5)
        assert ev.event_type == "heartbeat"

        req_ev = await trading.await_request_event(42, timeout=0.5)
        assert req_ev.event_type == "done"
        assert req_ev.payload["request_id"] == 42

        await trading.close()
        assert backend.closed

        # Context manager and disarm check
        backend2 = MockBackend()
        async with Trading(backend2) as t:
            assert backend2.started
            assert t.backend is backend2
            t.arm()
            t.disarm()
            assert backend2.is_armed is False
        assert backend2.closed

    asyncio.run(scenario())


def test_base_proxy_call_and_snapshot_helpers() -> None:
    async def scenario() -> None:
        backend = MockBackend()
        proxy = TradingClass(backend, object_id="test-obj")

        # Timezone check in _call
        naive_dt = datetime(2026, 10, 30)  # noqa: DTZ001
        with pytest.raises(ValueError, match="timezone"):
            await proxy._call("Test", naive_dt)

        aware_dt = datetime(2026, 10, 30, tzinfo=UTC)
        await proxy._call("Test", aware_dt)
        assert backend.calls[-1]["args"] == [int(aware_dt.timestamp())]

        # _property handling
        backend.responses["Base.Prop1"] = {"ok": True, "value": 123}
        prop1 = await proxy._property("Prop1")
        assert prop1.ok is True and prop1.value == 123

        backend.responses["Base.Prop2"] = 456
        prop2 = await proxy._property("Prop2")
        assert prop2.ok is True and prop2.value == 456

        # _snapshot handling
        backend.responses["Base.Snap"] = {"ticket": 99, "symbol": "EURUSD"}
        snap = await proxy._snapshot("Snap", PositionInfo, "position")
        assert isinstance(snap, PositionInfo)
        assert snap.ticket == 99

        backend.responses["Base.Snap"] = PositionInfo(ticket=100, symbol="EURUSD")
        snap2 = await proxy._snapshot("Snap", PositionInfo, "position")
        assert snap2.ticket == 100

        backend.responses["Base.Snap"] = "unexpected"
        with pytest.raises(TypeError, match="unexpected position type"):
            await proxy._snapshot("Snap", PositionInfo, "position")

        # _snapshot_dict handling
        backend.responses["Base.as_dict"] = {"ticket": 88, "symbol": "EURUSD"}
        d1 = await proxy._snapshot_dict(PositionInfo, "position")
        assert d1["ticket"] == 88

        backend.responses["Base.as_dict"] = PositionInfo(ticket=77, symbol="EURUSD")
        d2 = await proxy._snapshot_dict(PositionInfo, "position")
        assert d2["ticket"] == 77

        backend.responses["Base.as_dict"] = 123
        with pytest.raises(TypeError, match="unexpected position dictionary type"):
            await proxy._snapshot_dict(PositionInfo, "position")

        # _collection handling
        backend.responses["Base.Col"] = [
            {"ticket": 1, "symbol": "EURUSD"},
            {"ticket": 2, "symbol": "EURUSD"},
        ]
        col = await proxy._collection("Col", PositionInfo)
        assert len(col) == 2 and col[0].ticket == 1

        with pytest.raises(TypeError, match="use positional arguments or keyword"):
            await proxy._collection("Col", PositionInfo, 1, foo="bar")

        backend.responses["Base.Col"] = "not a list"
        with pytest.raises(TypeError, match="unexpected Col return type"):
            await proxy._collection("Col", PositionInfo)

    asyncio.run(scenario())


def test_request_serialization_and_normalization() -> None:
    exp = datetime(2026, 11, 1, 12, tzinfo=UTC)
    req = TradeRequest(
        action=TradeAction.DEAL,
        symbol="EURUSD",
        volume=0.5,
        order_type=OrderType.BUY,
        price=1.105,
        expiration=exp,
    )
    wire = serialize_request(req)
    assert wire["symbol"] == "EURUSD"
    assert wire["volume"] == 0.5
    assert wire["expiration"] == int(exp.timestamp())

    # Naive expiration check
    req_naive = TradeRequest(expiration=datetime(2026, 11, 1))  # noqa: DTZ001
    with pytest.raises(ValueError, match="timezone"):
        serialize_request(req_naive)

    # Normalize from dict
    normalized = normalize_request(
        {
            "action": 1,
            "type": 0,
            "symbol": "GBPUSD",
            "volume": 0.2,
            "expiration": int(exp.timestamp()),
        }
    )
    assert normalized.symbol == "GBPUSD"
    assert normalized.order_type == OrderType.BUY
    assert normalized.expiration == exp

    # Result builders
    res = build_trade_result({"retcode": 10009, "deal": 12345})
    assert res.retcode == 10009
    assert res.deal == 12345

    chk = build_trade_check_result(
        {"retcode": 0, "balance": 10000.0, "margin_free": 9500.0}
    )
    assert chk.retcode == 0
    assert chk.balance == 10000.0


def test_account_order_position_queries() -> None:
    async def scenario() -> None:
        backend = MockBackend()
        trading = Trading(backend)

        # AccountInfo
        backend.responses["AccountInfo.AccountInfo"] = {
            "login": 1234,
            "balance": 50000.0,
        }
        acc = await trading.account.AccountInfo()
        assert isinstance(acc, AccountInfo)
        assert acc.login == 1234 and acc.balance == 50000.0
        acc_call = await trading.account()
        assert acc_call.login == 1234

        await trading.account.OrderProfitCheck(1, 2)
        await trading.account.MarginCheck(1, 2)
        await trading.account.FreeMarginCheck(1, 2)
        await trading.account.MaxLotCheck("EURUSD")

        # OrderProxy
        backend.responses["OrderInfo.OrderInfo"] = {"ticket": 10, "symbol": "EURUSD"}
        backend.responses["OrderInfo.OrdersGet"] = [{"ticket": 10, "symbol": "EURUSD"}]
        backend.responses["OrderInfo.as_dict"] = {"ticket": 10, "symbol": "EURUSD"}
        backend.responses["OrderInfo.OrdersTotal"] = 1

        ord1 = await trading.order.OrderInfo()
        assert isinstance(ord1, OrderInfo)
        assert ord1.ticket == 10
        assert (await trading.order()).ticket == 10
        assert (await trading.order.as_dict())["ticket"] == 10
        assert await trading.order.OrdersTotal() == 1
        orders = await trading.order.OrdersGet(symbol="EURUSD")
        assert len(orders) == 1

        await trading.order.Select(10)
        await trading.order.SelectByIndex(0)
        await trading.order.StoreState()
        await trading.order.CheckState()

        # PositionProxy
        backend.responses["PositionInfo.PositionInfo"] = {
            "ticket": 20,
            "symbol": "GBPUSD",
        }
        backend.responses["PositionInfo.PositionsGet"] = [
            {"ticket": 20, "symbol": "GBPUSD"}
        ]
        backend.responses["PositionInfo.as_dict"] = {"ticket": 20, "symbol": "GBPUSD"}
        backend.responses["PositionInfo.PositionsTotal"] = 1

        pos = await trading.position.PositionInfo()
        assert isinstance(pos, PositionInfo)
        assert pos.ticket == 20
        assert (await trading.position()).ticket == 20
        assert (await trading.position.as_dict())["ticket"] == 20
        assert await trading.position.PositionsTotal() == 1
        positions = await trading.position.PositionsGet(symbol="GBPUSD")
        assert len(positions) == 1

        await trading.position.Select(20)
        await trading.position.SelectByIndex(0)
        await trading.position.SelectByMagic(42)
        await trading.position.SelectByTicket(20)
        await trading.position.StoreState()
        await trading.position.CheckState()

    asyncio.run(scenario())


def test_history_and_terminal_queries() -> None:
    async def scenario() -> None:
        backend = MockBackend()
        trading = Trading(backend)

        # HistoryOrderProxy
        backend.responses["HistoryOrderInfo.HistoryOrderInfo"] = {
            "ticket": 30,
            "symbol": "USDJPY",
        }
        backend.responses["HistoryOrderInfo.HistoryOrdersGet"] = [
            {"ticket": 30, "symbol": "USDJPY"}
        ]
        backend.responses["HistoryOrderInfo.as_dict"] = {
            "ticket": 30,
            "symbol": "USDJPY",
        }
        backend.responses["HistoryOrderInfo.HistoryOrdersTotal"] = 5

        h_ord = await trading.history_order.HistoryOrderInfo()
        assert isinstance(h_ord, OrderInfo)
        assert h_ord.ticket == 30
        assert (await trading.history_order()).ticket == 30
        assert (await trading.history_order.as_dict())["ticket"] == 30
        assert await trading.history_order.HistoryOrdersTotal() == 5
        assert len(await trading.history_order.HistoryOrdersGet()) == 1
        await trading.history_order.Ticket()
        await trading.history_order.SelectByIndex(0)

        # DealProxy
        backend.responses["DealInfo.DealInfo"] = {"ticket": 40, "symbol": "AUDUSD"}
        backend.responses["DealInfo.HistoryDealsGet"] = [
            {"ticket": 40, "symbol": "AUDUSD"}
        ]
        backend.responses["DealInfo.as_dict"] = {"ticket": 40, "symbol": "AUDUSD"}
        backend.responses["DealInfo.HistoryDealsTotal"] = 3

        deal = await trading.deal.DealInfo()
        assert isinstance(deal, DealInfo)
        assert deal.ticket == 40
        assert (await trading.deal()).ticket == 40
        assert (await trading.deal.as_dict())["ticket"] == 40
        assert await trading.deal.HistoryDealsTotal() == 3
        assert len(await trading.deal.HistoryDealsGet()) == 1
        await trading.deal.Ticket()
        await trading.deal.SelectByIndex(0)

        # TerminalInfo
        backend.responses["TerminalInfo.TerminalInfo"] = {
            "name": "MetaTrader 5",
            "connected": True,
        }
        term = await trading.terminal.TerminalInfo()
        assert isinstance(term, TerminalInfo)
        assert term.name == "MetaTrader 5"
        assert (await trading.terminal()).name == "MetaTrader 5"

    asyncio.run(scenario())


def test_symbol_proxy_queries() -> None:
    async def scenario() -> None:
        backend = MockBackend()
        trading = Trading(backend)

        sym = sample_symbol("EURUSD")
        backend.responses["SymbolInfo.SymbolInfo"] = sym
        backend.responses["SymbolInfo.as_dict"] = asdict(sym)

        s = await trading.symbol.SymbolInfo("EURUSD")
        assert s.name == "EURUSD"
        assert (await trading.symbol("EURUSD")).name == "EURUSD"
        assert (await trading.symbol.as_dict("EURUSD"))["name"] == "EURUSD"

        await trading.symbol.Refresh("EURUSD")
        await trading.symbol.RefreshRates("EURUSD")
        await trading.symbol.Name()
        await trading.symbol.Select("EURUSD")
        await trading.symbol.IsSynchronized("EURUSD")
        await trading.symbol.NormalizePrice("EURUSD", 1.12345)
        await trading.symbol.SymbolsTotal()
        await trading.symbol.SymbolsGet()
        await trading.symbol.SymbolInfoTick("EURUSD")
        await trading.symbol.SymbolSelect("EURUSD")

        # MarketBook
        await trading.symbol.MarketBookAdd("EURUSD")
        backend.responses["SymbolInfo.MarketBookGet"] = [
            {"type": 1, "price": 1.1001, "volume": 10, "volume_real": 10.0},
            BookInfo(
                type=BookType.BOOK_TYPE_SELL,
                price=1.1002,
                volume=5,
                volume_real=5.0,
            ),
        ]
        book = await trading.symbol.MarketBookGet("EURUSD")
        assert len(book) == 2
        assert book[0].price == 1.1001
        await trading.symbol.MarketBookRelease("EURUSD")

    asyncio.run(scenario())


def test_trade_configuration_and_checks() -> None:
    async def scenario() -> None:
        backend = MockBackend()
        trade = Trade(backend)

        await trade.LogLevel(2)
        await trade.SetExpertMagicNumber(123456)
        assert trade._magic == 123456

        await trade.SetDeviationInPoints(15)
        assert trade._deviation == 15

        await trade.SetTypeFilling(OrderFilling.IOC)
        assert trade._filling == OrderFilling.IOC

        backend.responses["SymbolInfo.SymbolInfo"] = sample_symbol(
            filling="Immediate or Cancel"
        )
        await trade.SetTypeFillingBySymbol("EURUSD")
        assert trade._filling == OrderFilling.IOC

        await trade.SetAsyncMode(True)
        await trade.SetMarginMode()

        # Formats & prints
        backend.responses["Trade.FormatRequest"] = "Request: Buy 1 lot"
        backend.responses["Trade.FormatRequestResult"] = "Result: Done"
        assert await trade.FormatRequest() == "Request: Buy 1 lot"
        assert await trade.FormatRequestResult() == "Result: Done"
        await trade.PrintRequest()
        await trade.PrintResult()

        # Request / Result / CheckResult snapshots
        backend.responses["Trade.Request"] = TradeRequest(symbol="EURUSD", volume=1.0)
        backend.responses["Trade.Result"] = TradeResult(retcode=10009, deal=999)
        backend.responses["Trade.CheckResult"] = TradeCheckResult(
            retcode=0, balance=5000.0
        )

        assert (await trade.Request()).symbol == "EURUSD"
        assert (await trade.Result()).deal == 999
        assert (await trade.CheckResult()).balance == 5000.0

    asyncio.run(scenario())


def test_trade_prepare_entry_validations() -> None:
    async def scenario() -> None:
        backend = MockBackend()
        trade = Trade(backend)
        backend.responses["SymbolInfo.SymbolInfo"] = sample_symbol("EURUSD")

        # Invalid direction
        with pytest.raises(ValueError, match="direction"):
            await trade.prepare_entry_request(
                "EURUSD",
                0,
                0.1,
                OrderType.BUY,
                price=1.1,
                sl=1.09,
                tp=1.12,
                magic=1,
                comment="",
                expiration=None,
            )

        # Invalid symbol
        with pytest.raises(ValueError, match="resolved symbol name"):
            await trade.prepare_entry_request(
                "Current",
                1,
                0.1,
                OrderType.BUY,
                price=1.1,
                sl=1.09,
                tp=1.12,
                magic=1,
                comment="",
                expiration=None,
            )

        # Invalid volume (negative or unaligned)
        with pytest.raises(ValueError, match="volume must be finite and positive"):
            await trade.prepare_entry_request(
                "EURUSD",
                1,
                -0.1,
                OrderType.BUY,
                price=1.1,
                sl=1.09,
                tp=1.12,
                magic=1,
                comment="",
                expiration=None,
            )
        with pytest.raises(ValueError, match="volume must align"):
            await trade.prepare_entry_request(
                "EURUSD",
                1,
                0.015,
                OrderType.BUY,
                price=1.1,
                sl=1.09,
                tp=1.12,
                magic=1,
                comment="",
                expiration=None,
            )

        # Naive expiration
        with pytest.raises(ValueError, match="expiration must include a timezone"):
            await trade.prepare_entry_request(
                "EURUSD",
                1,
                0.1,
                OrderType.BUY,
                price=1.1,
                sl=1.09,
                tp=1.12,
                magic=1,
                comment="",
                expiration=datetime(2026, 12, 1),  # noqa: DTZ001
            )

        # Valid market buy
        req_buy = await trade.prepare_entry_request(
            "EURUSD",
            1,
            0.1,
            OrderType.BUY,
            price=1.1,
            sl=1.09,
            tp=1.12,
            magic=42,
            comment="buy",
            expiration=None,
        )
        assert req_buy.action == TradeAction.DEAL
        assert req_buy.order_type == OrderType.BUY
        assert req_buy.price == 1.10020  # Ask price

        # Valid pending sell limit
        req_limit = await trade.prepare_entry_request(
            "EURUSD",
            -1,
            0.1,
            OrderType.BUY_LIMIT,
            price=1.11,
            sl=1.12,
            tp=1.08,
            magic=42,
            comment="sell limit",
            expiration=None,
        )
        assert req_limit.action == TradeAction.PENDING
        assert req_limit.order_type == OrderType.SELL_LIMIT
        assert req_limit.price == 1.11

    asyncio.run(scenario())


def test_trade_execution_arming_and_mutations() -> None:
    async def scenario() -> None:
        backend = MockBackend()
        trade = Trade(backend)
        backend.responses["SymbolInfo.SymbolInfo"] = sample_symbol("EURUSD")

        # OrderSend requires arming
        backend.disarm()
        with pytest.raises(BridgeError) as err:
            await trade.OrderSend(TradeRequest(symbol="EURUSD", volume=0.1))
        assert err.value.code == "NOT_ARMED"

        # OrderCheck does not require arming
        backend.responses["Trade.OrderCheck"] = {"retcode": 0, "balance": 10000.0}
        check = await trade.OrderCheck(TradeRequest(symbol="EURUSD", volume=0.1))
        assert check.retcode == 0

        # Arm and send_checked
        backend.arm()
        backend.responses["Trade.OrderSend"] = {
            "retcode": int(TradeRetcode.DONE),
            "order": 1234,
        }
        res = await trade.send_checked(TradeRequest(symbol="EURUSD", volume=0.1))
        assert res.retcode == int(TradeRetcode.DONE)
        assert res.order == 1234

        # send_checked fails when check fails
        backend.responses["Trade.OrderCheck"] = {
            "retcode": 10014,
            "comment": "Invalid volume",
        }
        res_fail = await trade.send_checked(TradeRequest(symbol="EURUSD", volume=0.1))
        assert res_fail.retcode == 10014
        assert res_fail.comment == "Invalid volume"

        # Close position
        backend.responses["Trade.OrderCheck"] = {"retcode": 0}
        pos = PositionInfo(ticket=55, symbol="EURUSD", volume=0.5, position_type=0)
        close_res = await trade.close(pos)
        assert close_res.retcode == int(TradeRetcode.DONE)
        last_call = backend.calls[-1]
        assert last_call["args"][0]["position"] == 55
        assert last_call["args"][0]["volume"] == 0.5

        # Cancel pending order
        order = OrderInfo(ticket=66, symbol="EURUSD", magic=10)
        cancel_res = await trade.cancel(order)
        assert cancel_res.retcode == int(TradeRetcode.DONE)
        assert backend.calls[-1]["args"][0]["order"] == 66

        # Modify protection
        mod_res = await trade.modify_protection(pos, sl=1.095, tp=1.115)
        assert mod_res.retcode == int(TradeRetcode.DONE)
        assert backend.calls[-1]["args"][0]["action"] == int(TradeAction.SLTP)

    asyncio.run(scenario())
