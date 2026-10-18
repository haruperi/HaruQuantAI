"""Master asynchronous trading library, MQL5 proxies, and unified facade.

Description:
    Provides the canonical asynchronous trading proxy library conforming to MQL5
    APIs and semantics. Includes TradingClass base identity and locking, mutation
    proxy Trade with request serialization, query proxies for account, terminal,
    symbol, order, history, and deal states, and the master unified Trading facade
    coordinating all child proxies for any TradingBackend.

Purpose:
    FEAT-TRADING-LIBRARY: Consolidated trading proxies, builders, and master facade.

Key Capabilities:
    - FR-TRADING-BASE-PROXY: Base proxy identity and serialized async command locking.
      Associated: `TradingClass`, `BaseTradingClass`.
      Logging: DEBUG on object creation and backend call invocation.
    - FR-TRADING-MUTATION-PROXY: Execution operations and order lifecycle methods.
      Associated: `Trade`, `Trade.OrderSend()`, `Trade.OrderCheck()`.
      Logging: DEBUG on order dispatch and check execution.
    - FR-TRADING-QUERY-PROXIES: Read-only state inspection and property resolution.
      Associated: `AccountProxy`, `TerminalProxy`, `SymbolProxy`, `PositionProxy`,
        `OrderProxy`, `HistoryOrderProxy`, `DealProxy`.
      Logging: DEBUG on account, terminal, symbol, position, order, and deal queries.
    - FR-TRADING-MASTER-FACADE: Unified eight-class trading composition facade.
      Associated: `Trading`, `Trading.start()`, `Trading.wait_connected()`,
        `Trading.close()`.
      Logging: DEBUG on master facade composition, startup, arming, and readiness.

Python API Usage:
    ```python
    from app.services.trading import Trading

    async with Trading(backend) as trading:
        await trading.wait_connected()
        account = await trading.account.AccountInfo()
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.trading
    ```
"""

# ruff: noqa: N802 -- MQL5 PascalCase API compatibility
from __future__ import annotations

import asyncio
import uuid
from dataclasses import asdict
from datetime import UTC, datetime
from types import TracebackType
from typing import Any, Self

from app.host.logging import get_logger
from app.services.include import contracts
from app.services.include.contracts import (
    BOOK_TYPE_DESCRIPTIONS,
    DEAL_ENTRY_DESCRIPTIONS,
    DEAL_TYPE_DESCRIPTIONS,
    ORDER_FILLING_DESCRIPTIONS,
    ORDER_STATE_DESCRIPTIONS,
    ORDER_TIME_DESCRIPTIONS,
    ORDER_TYPE_DESCRIPTIONS,
    POSITION_TYPE_DESCRIPTIONS,
    SYMBOL_CALC_MODE_DESCRIPTIONS,
    SYMBOL_SWAP_MODE_DESCRIPTIONS,
    SYMBOL_TRADE_EXECUTION_DESCRIPTIONS,
    SYMBOL_TRADE_MODE_DESCRIPTIONS,
    AccountInfo,
    BookInfo,
    BridgeEvent,
    DealInfo,
    OrderInfo,
    PositionInfo,
    PropertyValue,
    Receipt,
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
    StopoutMode,
    SymbolCalcMode,
    SymbolSwapMode,
    SymbolTradeExecution,
    SymbolTradeMode,
    TradeAction,
    TradeResolution,
    TradeRetcode,
)

__all__ = [
    "BOOK_TYPE_DESCRIPTIONS",
    "DEAL_ENTRY_DESCRIPTIONS",
    "DEAL_TYPE_DESCRIPTIONS",
    "ORDER_FILLING_DESCRIPTIONS",
    "ORDER_STATE_DESCRIPTIONS",
    "ORDER_TIME_DESCRIPTIONS",
    "ORDER_TYPE_DESCRIPTIONS",
    "POSITION_TYPE_DESCRIPTIONS",
    "SYMBOL_CALC_MODE_DESCRIPTIONS",
    "SYMBOL_SWAP_MODE_DESCRIPTIONS",
    "SYMBOL_TRADE_EXECUTION_DESCRIPTIONS",
    "SYMBOL_TRADE_MODE_DESCRIPTIONS",
    "AccountInfo",
    "AccountProxy",
    "AccountTradeMode",
    "BaseTradingClass",
    "BookInfo",
    "BookType",
    "BridgeEvent",
    "DealEntry",
    "DealInfo",
    "DealProxy",
    "DealType",
    "HistoryOrderProxy",
    "MarginMode",
    "OrderFilling",
    "OrderInfo",
    "OrderProxy",
    "OrderState",
    "OrderTime",
    "OrderType",
    "PositionInfo",
    "PositionProxy",
    "PositionType",
    "PropertyValue",
    "Receipt",
    "ReceiptStatus",
    "StopoutMode",
    "SymbolCalcMode",
    "SymbolInfo",
    "SymbolProxy",
    "SymbolSwapMode",
    "SymbolTradeExecution",
    "SymbolTradeMode",
    "TerminalInfo",
    "TerminalProxy",
    "Trade",
    "TradeAction",
    "TradeCheckResult",
    "TradeRequest",
    "TradeResolution",
    "TradeResult",
    "TradeRetcode",
    "Trading",
    "TradingBackend",
    "TradingClass",
    "_build_trade_check_result",
    "_build_trade_request",
    "_build_trade_result",
    "_serialize_dict_request",
    "_serialize_request",
]

logger = get_logger(__name__)


# ============================================================================
# TradingClass (Base Proxy)
# ============================================================================


class TradingClass:
    """Backend-neutral object identity and serialized async forwarding."""

    CLASS_NAME = "Base"
    TRADING_METHODS: frozenset[str] = frozenset()

    def __init__(
        self, backend: TradingBackend, *, object_id: str | None = None
    ) -> None:
        logger.debug("FR-TRADING-COMPOSITION: creating object")
        self.backend = backend
        self.object_id = object_id or f"{self.CLASS_NAME.lower()}-{uuid.uuid4().hex}"
        self._lock = asyncio.Lock()

    @property
    def last_command_id(self) -> str | None:
        """Return the last command in this task context."""
        return self.backend.last_command_id()

    async def _call(self, method: str, *args: Any) -> Any:
        logger.debug(
            "FR-TRADING-COMPOSITION: invoking backend",
            extra={"class_name": self.CLASS_NAME, "method_name": method},
        )
        wire_args: list[Any] = []
        for value in args:
            if isinstance(value, datetime):
                if value.tzinfo is None:
                    raise ValueError("trading datetimes must include a timezone")
                wire_args.append(int(value.timestamp()))
            else:
                wire_args.append(value)
        async with self._lock:
            return await self.backend.call(
                object_id=self.object_id,
                class_name=self.CLASS_NAME,
                method_name=method,
                args=wire_args,
                requires_arm=method in self.TRADING_METHODS,
            )

    async def _property(self, method: str, *args: Any) -> PropertyValue:
        value = await self._call(method, *args)
        if isinstance(value, dict) and {"ok", "value"} <= value.keys():
            return PropertyValue(
                ok=bool(value["ok"]),
                value=value.get("value"),
                error=value.get("error"),
            )
        return PropertyValue(ok=True, value=value)


BaseTradingClass = TradingClass


# ============================================================================
# Trade Request / Result Builders and Serializers
# ============================================================================


def _serialize_dict_request(req: dict[str, Any]) -> dict[str, Any]:
    data = dict(req)
    for key in ("action", "order_type", "type_filling", "type_time"):
        if key in data and hasattr(data[key], "value"):
            data[key] = int(data[key].value)
    exp = data.get("expiration")
    if isinstance(exp, datetime):
        if exp.tzinfo is None:
            raise ValueError("trading datetimes must include a timezone")
        data["expiration"] = int(exp.timestamp())
    return data


def _serialize_request(req: TradeRequest | dict[str, Any]) -> dict[str, Any]:
    """Serialize a TradeRequest or dictionary to wire-compatible dictionary."""
    if isinstance(req, TradeRequest):
        data: dict[str, Any] = {
            "action": int(req.action),
            "symbol": req.symbol,
            "volume": float(req.volume),
            "order_type": int(req.order_type),
            "price": float(req.price),
            "stoplimit": float(req.stoplimit),
            "sl": float(req.sl),
            "tp": float(req.tp),
            "deviation": req.deviation,
            "magic": req.magic,
            "order": req.order,
            "position": req.position,
            "position_by": req.position_by,
            "type_filling": int(req.type_filling),
            "type_time": int(req.type_time),
            "comment": req.comment,
        }
        if req.expiration is not None:
            if req.expiration.tzinfo is None:
                raise ValueError("trading datetimes must include a timezone")
            data["expiration"] = int(req.expiration.timestamp())
        return data
    return _serialize_dict_request(req)


def _build_trade_request(data: dict[str, Any]) -> TradeRequest:
    action_val = data.get("action", TradeAction.DEAL)
    action = (
        action_val
        if isinstance(action_val, TradeAction)
        else TradeAction(int(action_val))
    )
    order_type_val = data.get("type", data.get("order_type", OrderType.BUY))
    order_type = (
        order_type_val
        if isinstance(order_type_val, OrderType)
        else OrderType(int(order_type_val))
    )
    filling_val = data.get("type_filling", OrderFilling.FOK)
    filling = (
        filling_val
        if isinstance(filling_val, OrderFilling)
        else OrderFilling(int(filling_val))
    )
    time_val = data.get("type_time", OrderTime.GTC)
    type_time = (
        time_val if isinstance(time_val, OrderTime) else OrderTime(int(time_val))
    )

    exp_val = data.get("expiration")
    expiration: datetime | None = None
    if isinstance(exp_val, datetime):
        expiration = exp_val
    elif isinstance(exp_val, (int, float)) and exp_val > 0:
        expiration = datetime.fromtimestamp(exp_val, tz=UTC)

    return TradeRequest(
        action=action,
        magic=int(data.get("magic", 0)),
        order=int(data.get("order", 0)),
        symbol=str(data.get("symbol", "")),
        volume=float(data.get("volume", 0.0)),
        price=float(data.get("price", 0.0)),
        stoplimit=float(data.get("stoplimit", 0.0)),
        sl=float(data.get("sl", 0.0)),
        tp=float(data.get("tp", 0.0)),
        deviation=int(data.get("deviation", 0)),
        order_type=order_type,
        type_filling=filling,
        type_time=type_time,
        expiration=expiration,
        comment=str(data.get("comment", "")),
        position=int(data.get("position", 0)),
        position_by=int(data.get("position_by", 0)),
    )


def _build_trade_result(data: dict[str, Any]) -> TradeResult:
    return TradeResult(
        retcode=int(data.get("retcode", int(TradeRetcode.ERROR))),
        deal=int(data.get("deal", 0)),
        order=int(data.get("order", 0)),
        volume=float(data.get("volume", 0.0)),
        price=float(data.get("price", 0.0)),
        bid=float(data.get("bid", 0.0)),
        ask=float(data.get("ask", 0.0)),
        comment=str(data.get("comment", "")),
        request_id=int(data.get("request_id", 0)),
        retcode_external=int(data.get("retcode_external", 0)),
        raw=data.get("raw", data),
    )


def _build_trade_check_result(data: dict[str, Any]) -> TradeCheckResult:
    return TradeCheckResult(
        retcode=int(data.get("retcode", int(TradeRetcode.DONE))),
        balance=float(data.get("balance", 0.0)),
        equity=float(data.get("equity", 0.0)),
        profit=float(data.get("profit", 0.0)),
        margin=float(data.get("margin", 0.0)),
        margin_free=float(data.get("margin_free", 0.0)),
        margin_level=float(data.get("margin_level", 0.0)),
        comment=str(data.get("comment", "")),
        raw=data.get("raw", data),
    )


# ============================================================================
# Trade (Mutation Proxy)
# ============================================================================


class Trade(TradingClass):
    """Canonical asynchronous Trade API conforming to standard MQL5 CTrade."""

    CLASS_NAME = "Trade"
    TRADING_METHODS = frozenset({"OrderSend"})

    async def LogLevel(self, log_level: int) -> bool:
        """Set logging verbosity on the trade execution context."""
        return bool(await self._call("LogLevel", log_level))

    async def SetExpertMagicNumber(self, magic: int) -> None:
        """Set default magic number for subsequent orders."""
        await self._call("SetExpertMagicNumber", magic)

    async def SetDeviationInPoints(self, deviation: int) -> None:
        """Set default slippage deviation in points for market orders."""
        await self._call("SetDeviationInPoints", deviation)

    async def SetTypeFilling(self, filling: OrderFilling | int) -> None:
        """Set default order filling execution policy."""
        val = filling.value if isinstance(filling, OrderFilling) else filling
        await self._call("SetTypeFilling", val)

    async def SetTypeFillingBySymbol(self, symbol: str) -> bool:
        """Resolve and set the most appropriate filling mode supported by symbol."""
        return bool(await self._call("SetTypeFillingBySymbol", symbol))

    async def SetAsyncMode(self, mode: bool) -> None:
        """Enable or disable asynchronous order sending mode."""
        await self._call("SetAsyncMode", mode)

    async def SetMarginMode(self) -> None:
        """Recalculate margin mode based on account and connected broker terminal."""
        await self._call("SetMarginMode")

    async def OrderSend(
        self,
        request: TradeRequest | dict[str, Any],
        result: TradeResult | None = None,
    ) -> TradeResult:
        """Send a trade request to the broker terminal."""
        logger.debug("FR-TRADING-MUTATION: executing OrderSend")
        wire_payload = _serialize_request(request)
        raw = await self._call("OrderSend", wire_payload)
        data = raw if isinstance(raw, dict) else {}
        res = _build_trade_result(data)
        if result is not None:
            for k, v in asdict(res).items():
                if hasattr(result, k):
                    setattr(result, k, v)
        return res

    async def OrderCheck(
        self,
        request: TradeRequest | dict[str, Any],
        result: TradeCheckResult | None = None,
    ) -> TradeCheckResult:
        """Validate an order request and calculate required margin and profit."""
        logger.debug("FR-TRADING-MUTATION: executing OrderCheck")
        wire_payload = _serialize_request(request)
        raw = await self._call("OrderCheck", wire_payload)
        data = raw if isinstance(raw, dict) else {}
        res = _build_trade_check_result(data)
        if result is not None:
            for k, v in asdict(res).items():
                if hasattr(result, k):
                    setattr(result, k, v)
        return res

    async def __call__(
        self,
        request: TradeRequest | dict[str, Any],
        result: TradeResult | None = None,
    ) -> TradeResult:
        """Forward directly to OrderSend."""
        return await self.OrderSend(request, result)

    async def Request(self) -> TradeRequest:
        """Fetch the last trade request snapshot."""
        raw = await self._call("Request")
        data = raw if isinstance(raw, dict) else {}
        return _build_trade_request(data)

    async def Result(self) -> TradeResult:
        """Fetch the last trade result snapshot."""
        raw = await self._call("Result")
        data = raw if isinstance(raw, dict) else {}
        return _build_trade_result(data)

    async def CheckResult(self) -> TradeCheckResult:
        """Fetch the last trade check result snapshot."""
        raw = await self._call("CheckResult")
        data = raw if isinstance(raw, dict) else {}
        return _build_trade_check_result(data)

    async def PrintRequest(self) -> bool:
        """Log the last trade request metadata."""
        return bool(await self._call("PrintRequest"))

    async def PrintResult(self) -> bool:
        """Log the last trade result metadata."""
        return bool(await self._call("PrintResult"))

    async def FormatRequest(self) -> str:
        """Format the last trade request as a text string."""
        return str(await self._call("FormatRequest"))

    async def FormatRequestResult(self) -> str:
        """Format the last trade request and result as a text string."""
        return str(await self._call("FormatRequestResult"))


# ============================================================================
# Query Proxies (Account, Terminal, Symbol, Position, Order, History, Deal)
# ============================================================================


class AccountProxy(TradingClass):
    """Canonical asynchronous AccountInfo API proxy."""

    CLASS_NAME = "AccountInfo"

    async def AccountInfo(self, *args: Any) -> contracts.AccountInfo:
        """Await the backend AccountInfo snapshot."""
        logger.debug("FR-TRADING-ACCOUNT-SNAPSHOT: querying account snapshot")
        data = await self._call("AccountInfo", *args)
        if isinstance(data, contracts.AccountInfo):
            return data
        if isinstance(data, dict):
            return contracts.AccountInfo(**data)
        raise TypeError(f"unexpected account info type: {type(data).__name__}")

    async def __call__(self, *args: Any) -> contracts.AccountInfo:
        """Await the backend AccountInfo snapshot directly via call syntax."""
        return await self.AccountInfo(*args)

    async def OrderProfitCheck(self, *args: Any) -> Any:
        """Await the backend AccountInfo.OrderProfitCheck operation."""
        return await self._call("OrderProfitCheck", *args)

    async def MarginCheck(self, *args: Any) -> Any:
        """Await the backend AccountInfo.MarginCheck operation."""
        return await self._call("MarginCheck", *args)

    async def FreeMarginCheck(self, *args: Any) -> Any:
        """Await the backend AccountInfo.FreeMarginCheck operation."""
        return await self._call("FreeMarginCheck", *args)

    async def MaxLotCheck(self, *args: Any) -> Any:
        """Await the backend AccountInfo.MaxLotCheck operation."""
        return await self._call("MaxLotCheck", *args)


class TerminalProxy(TradingClass):
    """Canonical asynchronous TerminalInfo API proxy."""

    CLASS_NAME = "TerminalInfo"

    async def TerminalInfo(self, *args: Any) -> contracts.TerminalInfo:
        """Await the backend TerminalInfo snapshot."""
        logger.debug("FR-TRADING-TERMINAL-SNAPSHOT: querying terminal snapshot")
        data = await self._call("TerminalInfo", *args)
        if isinstance(data, contracts.TerminalInfo):
            return data
        if isinstance(data, dict):
            return contracts.TerminalInfo(**data)
        raise TypeError(f"unexpected terminal info type: {type(data).__name__}")

    async def __call__(self, *args: Any) -> contracts.TerminalInfo:
        """Await the backend TerminalInfo snapshot directly via call syntax."""
        return await self.TerminalInfo(*args)


class SymbolProxy(TradingClass):
    """Canonical asynchronous SymbolInfo API proxy."""

    CLASS_NAME = "SymbolInfo"

    async def SymbolInfo(self, *args: Any) -> contracts.SymbolInfo:
        """Await the backend SymbolInfo snapshot."""
        logger.debug("FR-TRADING-SYMBOL-SNAPSHOT: querying symbol snapshot")
        data = await self._call("SymbolInfo", *args)
        if isinstance(data, contracts.SymbolInfo):
            return data
        if isinstance(data, dict):
            return contracts.SymbolInfo(**data)
        raise TypeError(f"unexpected symbol info type: {type(data).__name__}")

    async def __call__(self, *args: Any) -> contracts.SymbolInfo:
        """Await the backend SymbolInfo snapshot directly via call syntax."""
        return await self.SymbolInfo(*args)

    async def as_dict(self, *args: Any) -> dict[str, Any]:
        """Await the backend symbol snapshot represented as a dictionary."""
        data = await self._call("as_dict", *args)
        if isinstance(data, dict):
            return data
        if isinstance(data, contracts.SymbolInfo):
            return asdict(data)
        raise TypeError(f"unexpected symbol dictionary type: {type(data).__name__}")

    async def Refresh(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.Refresh operation."""
        return await self._call("Refresh", *args)

    async def RefreshRates(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.RefreshRates operation."""
        return await self._call("RefreshRates", *args)

    async def Name(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.Name operation."""
        return await self._call("Name", *args)

    async def Select(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.Select operation."""
        return await self._call("Select", *args)

    async def IsSynchronized(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.IsSynchronized operation."""
        return await self._call("IsSynchronized", *args)

    async def NormalizePrice(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.NormalizePrice operation."""
        return await self._call("NormalizePrice", *args)

    async def SymbolsTotal(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SymbolsTotal operation."""
        return await self._call("SymbolsTotal", *args)

    async def SymbolsGet(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SymbolsGet operation."""
        return await self._call("SymbolsGet", *args)

    async def SymbolInfoTick(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SymbolInfoTick operation."""
        return await self._call("SymbolInfoTick", *args)

    async def SymbolSelect(self, *args: Any) -> Any:
        """Await the backend SymbolInfo.SymbolSelect operation."""
        return await self._call("SymbolSelect", *args)

    async def MarketBookAdd(self, *args: Any) -> Any:
        """Subscribes the MetaTrader 5 terminal to Market Depth change events."""
        return await self._call("MarketBookAdd", *args)

    async def MarketBookGet(self, *args: Any) -> tuple[contracts.BookInfo, ...]:
        """Return a tuple of BookInfo featuring Market Depth entries for a symbol."""
        logger.debug("FR-TRADING-SYMBOL-SNAPSHOT: reading market depth")
        raw = await self._call("MarketBookGet", *args)
        if not raw:
            return ()
        entries: list[contracts.BookInfo] = []
        for item in raw:
            if isinstance(item, contracts.BookInfo):
                entries.append(item)
            elif isinstance(item, dict):
                raw_vol = item.get("volume_real")
                if raw_vol is None:
                    raw_vol = item.get("volume", 0.0)
                entries.append(
                    contracts.BookInfo(
                        type=BookType(int(item.get("type", BookType.BOOK_TYPE_BUY))),
                        price=float(item.get("price", 0.0)),
                        volume=int(item.get("volume", 0)),
                        volume_real=float(raw_vol if raw_vol is not None else 0.0),
                    )
                )
        return tuple(entries)

    async def MarketBookRelease(self, *args: Any) -> Any:
        """Cancel subscription of terminal to Market Depth change events."""
        return await self._call("MarketBookRelease", *args)


class PositionProxy(TradingClass):
    """Canonical asynchronous PositionInfo API proxy."""

    CLASS_NAME = "PositionInfo"

    async def PositionInfo(self, *args: Any) -> contracts.PositionInfo:
        """Await the backend PositionInfo snapshot."""
        logger.debug("FR-TRADING-POSITIONS: querying position snapshot")
        data = await self._call("PositionInfo", *args)
        if isinstance(data, contracts.PositionInfo):
            return data
        if isinstance(data, dict):
            return contracts.PositionInfo(**data)
        raise TypeError(f"unexpected position info type: {type(data).__name__}")

    async def __call__(self, *args: Any) -> contracts.PositionInfo:
        """Await the backend PositionInfo snapshot directly via call syntax."""
        return await self.PositionInfo(*args)

    async def as_dict(self, *args: Any) -> dict[str, Any]:
        """Await the backend position snapshot represented as a dictionary."""
        data = await self._call("as_dict", *args)
        if isinstance(data, dict):
            return data
        if isinstance(data, contracts.PositionInfo):
            return asdict(data)
        raise TypeError(f"unexpected position dictionary type: {type(data).__name__}")

    async def Select(self, *args: Any) -> Any:
        """Await the backend PositionInfo.Select operation."""
        return await self._call("Select", *args)

    async def SelectByIndex(self, *args: Any) -> Any:
        """Await the backend PositionInfo.SelectByIndex operation."""
        return await self._call("SelectByIndex", *args)

    async def SelectByMagic(self, *args: Any) -> Any:
        """Await the backend PositionInfo.SelectByMagic operation."""
        return await self._call("SelectByMagic", *args)

    async def SelectByTicket(self, *args: Any) -> Any:
        """Await the backend PositionInfo.SelectByTicket operation."""
        return await self._call("SelectByTicket", *args)

    async def StoreState(self, *args: Any) -> Any:
        """Await the backend PositionInfo.StoreState operation."""
        return await self._call("StoreState", *args)

    async def CheckState(self, *args: Any) -> Any:
        """Await the backend PositionInfo.CheckState operation."""
        return await self._call("CheckState", *args)

    async def PositionsTotal(self, *args: Any) -> Any:
        """Await the backend PositionInfo.PositionsTotal operation."""
        return await self._call("PositionsTotal", *args)

    async def PositionsGet(
        self, *args: Any, **kwargs: Any
    ) -> list[contracts.PositionInfo]:
        """Await the backend PositionInfo.PositionsGet operation."""
        logger.debug("FR-TRADING-POSITIONS: querying positions collection")
        data = (
            await self._call("PositionsGet", kwargs)
            if kwargs
            else await self._call("PositionsGet", *args)
        )
        if isinstance(data, list):
            return [
                item
                if isinstance(item, contracts.PositionInfo)
                else contracts.PositionInfo(**item)
                for item in data
            ]
        raise TypeError(f"unexpected PositionsGet return type: {type(data).__name__}")


class OrderProxy(TradingClass):
    """Canonical asynchronous OrderInfo API proxy."""

    CLASS_NAME = "OrderInfo"

    async def OrderInfo(self, *args: Any) -> contracts.OrderInfo:
        """Await the backend OrderInfo snapshot."""
        logger.debug("FR-TRADING-ORDERS: querying order snapshot")
        data = await self._call("OrderInfo", *args)
        if isinstance(data, contracts.OrderInfo):
            return data
        if isinstance(data, dict):
            return contracts.OrderInfo(**data)
        raise TypeError(f"unexpected order info type: {type(data).__name__}")

    async def __call__(self, *args: Any) -> contracts.OrderInfo:
        """Await the backend OrderInfo snapshot directly via call syntax."""
        return await self.OrderInfo(*args)

    async def as_dict(self, *args: Any) -> dict[str, Any]:
        """Await the backend order snapshot represented as a dictionary."""
        data = await self._call("as_dict", *args)
        if isinstance(data, dict):
            return data
        if isinstance(data, contracts.OrderInfo):
            return asdict(data)
        raise TypeError(f"unexpected order dictionary type: {type(data).__name__}")

    async def Select(self, *args: Any) -> Any:
        """Await the backend OrderInfo.Select operation."""
        return await self._call("Select", *args)

    async def SelectByIndex(self, *args: Any) -> Any:
        """Await the backend OrderInfo.SelectByIndex operation."""
        return await self._call("SelectByIndex", *args)

    async def StoreState(self, *args: Any) -> Any:
        """Await the backend OrderInfo.StoreState operation."""
        return await self._call("StoreState", *args)

    async def CheckState(self, *args: Any) -> Any:
        """Await the backend OrderInfo.CheckState operation."""
        return await self._call("CheckState", *args)

    async def OrdersTotal(self, *args: Any) -> Any:
        """Await the backend OrderInfo.OrdersTotal operation."""
        return await self._call("OrdersTotal", *args)

    async def OrdersGet(self, *args: Any, **kwargs: Any) -> list[contracts.OrderInfo]:
        """Await the backend OrderInfo.OrdersGet operation."""
        logger.debug("FR-TRADING-ORDERS: querying orders collection")
        data = (
            await self._call("OrdersGet", kwargs)
            if kwargs
            else await self._call("OrdersGet", *args)
        )
        if isinstance(data, list):
            return [
                item
                if isinstance(item, contracts.OrderInfo)
                else contracts.OrderInfo(**item)
                for item in data
            ]
        raise TypeError(f"unexpected OrdersGet return type: {type(data).__name__}")


class HistoryOrderProxy(TradingClass):
    """Canonical asynchronous HistoryOrderInfo API proxy."""

    CLASS_NAME = "HistoryOrderInfo"

    async def HistoryOrderInfo(self, *args: Any) -> contracts.OrderInfo:
        """Await the backend HistoryOrderInfo snapshot."""
        logger.debug("FR-TRADING-HISTORY: querying history order snapshot")
        data = await self._call("HistoryOrderInfo", *args)
        if isinstance(data, contracts.OrderInfo):
            return data
        if isinstance(data, dict):
            return contracts.OrderInfo(**data)
        raise TypeError(f"unexpected history order info type: {type(data).__name__}")

    async def __call__(self, *args: Any) -> contracts.OrderInfo:
        """Await the backend HistoryOrderInfo snapshot directly via call syntax."""
        return await self.HistoryOrderInfo(*args)

    async def as_dict(self, *args: Any) -> dict[str, Any]:
        """Await the backend historical order snapshot represented as a dictionary."""
        data = await self._call("as_dict", *args)
        if isinstance(data, dict):
            return data
        if isinstance(data, contracts.OrderInfo):
            return asdict(data)
        raise TypeError(
            f"unexpected history order dictionary type: {type(data).__name__}"
        )

    async def Ticket(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.Ticket operation."""
        return await self._call("Ticket", *args)

    async def SelectByIndex(self, *args: Any) -> Any:
        """Await the backend HistoryOrderInfo.SelectByIndex operation."""
        return await self._call("SelectByIndex", *args)

    async def HistoryOrdersTotal(self, *args: Any, **kwargs: Any) -> Any:
        """Await the backend HistoryOrderInfo.HistoryOrdersTotal operation."""
        if kwargs:
            return await self._call("HistoryOrdersTotal", kwargs)
        return await self._call("HistoryOrdersTotal", *args)

    async def HistoryOrdersGet(
        self, *args: Any, **kwargs: Any
    ) -> list[contracts.OrderInfo]:
        """Await the backend HistoryOrderInfo.HistoryOrdersGet operation."""
        logger.debug("FR-TRADING-HISTORY: querying history orders collection")
        data = (
            await self._call("HistoryOrdersGet", kwargs)
            if kwargs
            else await self._call("HistoryOrdersGet", *args)
        )
        if isinstance(data, list):
            return [
                item
                if isinstance(item, contracts.OrderInfo)
                else contracts.OrderInfo(**item)
                for item in data
            ]
        raise TypeError(
            f"unexpected HistoryOrdersGet return type: {type(data).__name__}"
        )


class DealProxy(TradingClass):
    """Canonical asynchronous DealInfo API proxy."""

    CLASS_NAME = "DealInfo"

    async def DealInfo(self, *args: Any) -> contracts.DealInfo:
        """Await the backend DealInfo snapshot."""
        logger.debug("FR-TRADING-HISTORY: querying deal snapshot")
        data = await self._call("DealInfo", *args)
        if isinstance(data, contracts.DealInfo):
            return data
        if isinstance(data, dict):
            return contracts.DealInfo(**data)
        raise TypeError(f"unexpected deal info type: {type(data).__name__}")

    async def __call__(self, *args: Any) -> contracts.DealInfo:
        """Await the backend DealInfo snapshot directly via call syntax."""
        return await self.DealInfo(*args)

    async def as_dict(self, *args: Any) -> dict[str, Any]:
        """Await the backend historical deal snapshot represented as a dictionary."""
        data = await self._call("as_dict", *args)
        if isinstance(data, dict):
            return data
        if isinstance(data, contracts.DealInfo):
            return asdict(data)
        raise TypeError(f"unexpected deal dictionary type: {type(data).__name__}")

    async def Ticket(self, *args: Any) -> Any:
        """Await the backend DealInfo.Ticket operation."""
        return await self._call("Ticket", *args)

    async def SelectByIndex(self, *args: Any) -> Any:
        """Await the backend DealInfo.SelectByIndex operation."""
        return await self._call("SelectByIndex", *args)

    async def HistoryDealsTotal(self, *args: Any, **kwargs: Any) -> Any:
        """Await the backend DealInfo.HistoryDealsTotal operation."""
        if kwargs:
            return await self._call("HistoryDealsTotal", kwargs)
        return await self._call("HistoryDealsTotal", *args)

    async def HistoryDealsGet(
        self, *args: Any, **kwargs: Any
    ) -> list[contracts.DealInfo]:
        """Await the backend DealInfo.HistoryDealsGet operation."""
        logger.debug("FR-TRADING-HISTORY: querying history deals collection")
        data = (
            await self._call("HistoryDealsGet", kwargs)
            if kwargs
            else await self._call("HistoryDealsGet", *args)
        )
        if isinstance(data, list):
            return [
                item
                if isinstance(item, contracts.DealInfo)
                else contracts.DealInfo(**item)
                for item in data
            ]
        raise TypeError(
            f"unexpected HistoryDealsGet return type: {type(data).__name__}"
        )


# ============================================================================
# Trading (Master Composition Facade)
# ============================================================================


class Trading:
    """The unified eight-class composition for every async trading backend."""

    def __init__(self, backend: TradingBackend) -> None:
        logger.debug("FR-TRADING-COMPOSITION: composing trading classes")
        self.backend = backend
        self.trade = Trade(backend)
        self.account = AccountProxy(backend)
        self.symbol = SymbolProxy(backend)
        self.order = OrderProxy(backend)
        self.history_order = HistoryOrderProxy(backend)
        self.position = PositionProxy(backend)
        self.deal = DealProxy(backend)
        self.terminal = TerminalProxy(backend)

    async def start(self) -> None:
        """Start the selected backend."""
        logger.debug("FR-TRADING-COMPOSITION: starting backend")
        await self.backend.start()

    async def wait_connected(self, timeout: float | None = None) -> None:  # noqa: ASYNC109
        """Wait for backend readiness."""
        logger.debug("FR-TRADING-COMPOSITION: waiting for backend")
        await self.backend.wait_connected(timeout)

    def arm(self) -> None:
        """Permit mutation operations on the selected backend."""
        logger.debug("FR-TRADING-COMPOSITION: arming backend")
        self.backend.arm()

    def disarm(self) -> None:
        """Revoke mutation permission."""
        logger.debug("FR-TRADING-COMPOSITION: disarming backend")
        self.backend.disarm()

    async def close(self) -> None:
        """Close the selected backend."""
        logger.debug("FR-TRADING-COMPOSITION: closing backend")
        await self.backend.close()

    def last_command_id(self) -> str | None:
        """Read the current task's last backend command identifier."""
        logger.debug("FR-TRADING-COMPOSITION: reading command identity")
        return self.backend.last_command_id()

    def receipt(self, command_id: str) -> Receipt | None:
        """Read a backend command receipt."""
        logger.debug("FR-TRADING-COMPOSITION: reading receipt")
        return self.backend.receipt(command_id)

    async def next_event(self, timeout: float | None = None) -> BridgeEvent:  # noqa: ASYNC109
        """Wait for a backend event within the requested timeout."""
        logger.debug("FR-TRADING-COMPOSITION: waiting for event")
        return await self.backend.next_event(timeout)

    async def await_request_event(
        self,
        request_id: int,
        timeout: float | None = None,  # noqa: ASYNC109
    ) -> BridgeEvent:
        """Delegate supported request correlation, or surface capability failure."""
        logger.debug("FR-TRADING-COMPOSITION: waiting for correlated event")
        return await self.backend.await_request_event(request_id, timeout)

    async def __aenter__(self) -> Self:
        """Start the selected backend on context entry."""
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Close the selected backend on context exit."""
        await self.close()


def main() -> None:
    """Demonstrate Trading facade definition."""
    logger.info(
        "Master composition Trading class initialized: %s",
        Trading.__name__,
    )


if __name__ == "__main__":
    main()
