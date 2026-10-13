# ruff: noqa: N802 -- public names preserve the eight-class compatibility API.
"""Shared Trade proxy for native broker operations.

Description:
    Forwards canonical trading requests and configuration through TradingClass.
    OrderSend and OrderCheck execute typed operations returning TradeResult and
    TradeCheckResult snapshots. Placement is shared; method semantics remain
    those of native MT5.

Purpose:
    FEAT-BROKER-PROXIES: Expose explicit asynchronous broker class operations
    without duplicating transport or persistence ownership.

Key Capabilities:
    - FR-BROKER-PROXIES-TRADE-FORWARDING: Forward native trading methods.
      Associated: `Trade`, `TradingClass._call()`
      Logging: Transport emits DEBUG encoding-attempt metadata for remote calls;
        no payload logging or proxy logging configuration is introduced here.

Python API Usage:
    Access this proxy through a configured MetaTrader facade or bind it to the
    async backend capability. Remote calls are asynchronous.

CLI Usage:
    uv run pytest tests/unit/services/test_trading_api.py --no-cov
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.services.brokers.contracts import (
    OrderFilling,
    OrderTime,
    OrderType,
    TradeAction,
    TradeCheckResult,
    TradeRequest,
    TradeResult,
    TradeRetcode,
)

from .base import TradingClass


def _serialize_dict_request(data_in: dict[str, Any]) -> dict[str, Any]:
    data = dict(data_in)
    for key in ("action", "order_type", "type", "type_filling", "type_time"):
        val = data.get(key)
        if isinstance(val, (TradeAction, OrderType, OrderFilling, OrderTime)):
            data[key] = int(val)
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


def _build_trade_request(data: dict[str, Any]) -> TradeRequest:
    action_val = data.get("action", TradeAction.DEAL)
    action = (
        TradeAction[action_val.removeprefix("TRADE_ACTION_")]
        if isinstance(action_val, str)
        else TradeAction(action_val)
    )
    type_val = data.get("order_type", data.get("type", OrderType.BUY))
    order_type = (
        OrderType[type_val.removeprefix("ORDER_TYPE_")]
        if isinstance(type_val, str)
        else OrderType(type_val)
    )
    fill_val = data.get("type_filling", data.get("filling", OrderFilling.FOK))
    filling = (
        OrderFilling[fill_val.removeprefix("ORDER_FILLING_")]
        if isinstance(fill_val, str)
        else OrderFilling(fill_val)
    )
    time_val = data.get("type_time", data.get("time_type", OrderTime.GTC))
    time_type = (
        OrderTime[time_val.removeprefix("ORDER_TIME_")]
        if isinstance(time_val, str)
        else OrderTime(time_val)
    )
    exp = data.get("expiration")
    if isinstance(exp, (int, float)):
        exp_dt = datetime.fromtimestamp(exp, tz=UTC) if exp else None
    elif isinstance(exp, datetime):
        exp_dt = exp
    else:
        exp_dt = None

    return TradeRequest(
        action=action,
        symbol=str(data.get("symbol", "")),
        volume=float(data.get("volume", 0.0)),
        order_type=order_type,
        price=float(data.get("price", 0.0)),
        stoplimit=float(data.get("stoplimit", 0.0)),
        sl=float(data.get("sl", 0.0)),
        tp=float(data.get("tp", 0.0)),
        deviation=int(data.get("deviation", 0)),
        magic=int(data.get("magic", 0)),
        order=int(data.get("order", 0)),
        position=int(data.get("position", 0)),
        position_by=int(data.get("position_by", 0)),
        type_filling=filling,
        type_time=time_type,
        expiration=exp_dt,
        comment=str(data.get("comment", "")),
    )


class Trade(TradingClass):
    """Canonical asynchronous Trade API."""

    CLASS_NAME = "Trade"
    TRADING_METHODS = frozenset(["OrderSend"])

    async def __call__(
        self,
        request: TradeRequest | dict[str, Any],
        result: TradeResult | None = None,
    ) -> TradeResult:
        """Await a trade operation through OrderSend."""
        return await self.OrderSend(request, result)

    async def LogLevel(self, log_level: int) -> bool:
        """Set the trade logging level."""
        return bool(await self._call("LogLevel", log_level))

    async def SetExpertMagicNumber(self, magic: int) -> bool:
        """Set the default expert magic number for subsequent orders."""
        return bool(await self._call("SetExpertMagicNumber", magic))

    async def SetDeviationInPoints(self, deviation: int) -> bool:
        """Set the default price deviation in points for orders."""
        return bool(await self._call("SetDeviationInPoints", deviation))

    async def SetTypeFilling(self, filling: OrderFilling | int) -> bool:
        """Set the default order filling type."""
        return bool(await self._call("SetTypeFilling", int(filling)))

    async def SetTypeFillingBySymbol(self, symbol: str) -> bool:
        """Configure filling type automatically based on symbol capabilities."""
        return bool(await self._call("SetTypeFillingBySymbol", symbol))

    async def SetAsyncMode(self, mode: bool) -> bool:
        """Set asynchronous order dispatch mode."""
        return bool(await self._call("SetAsyncMode", mode))

    async def SetMarginMode(self) -> bool:
        """Update margin calculation mode according to current account state."""
        return bool(await self._call("SetMarginMode"))

    async def OrderSend(
        self,
        request: TradeRequest | dict[str, Any],
        result: TradeResult | None = None,
    ) -> TradeResult:
        """Execute a trade request and return the TradeResult snapshot."""
        payload = _serialize_request(request)
        raw = await self._call("OrderSend", payload)
        data = raw if isinstance(raw, dict) else {}
        res = _build_trade_result(data)
        if result is not None:
            result.retcode = res.retcode
            result.deal = res.deal
            result.order = res.order
            result.volume = res.volume
            result.price = res.price
            result.bid = res.bid
            result.ask = res.ask
            result.comment = res.comment
            result.request_id = res.request_id
            result.retcode_external = res.retcode_external
            result.raw = res.raw
            return result
        return res

    async def OrderCheck(
        self,
        request: TradeRequest | dict[str, Any],
        result: TradeCheckResult | None = None,
    ) -> TradeCheckResult:
        """Validate a trade request and return the TradeCheckResult snapshot."""
        payload = _serialize_request(request)
        raw = await self._call("OrderCheck", payload)
        data = raw if isinstance(raw, dict) else {}
        chk = _build_trade_check_result(data)
        if result is not None:
            result.retcode = chk.retcode
            result.balance = chk.balance
            result.equity = chk.equity
            result.profit = chk.profit
            result.margin = chk.margin
            result.margin_free = chk.margin_free
            result.margin_level = chk.margin_level
            result.comment = chk.comment
            result.raw = chk.raw
            return result
        return chk

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
