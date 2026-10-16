"""Mutation proxy Trade and request/result serialization builders.

Description:
    Provides the Trade proxy class implementing order placement, modification,
    cancellation, and position closure, alongside wire serialization and request
    building helper routines.

Purpose:
    FEAT-TRADING-MUTATION: Order execution, modification, and position closure.

Key Capabilities:
    - FR-TRADING-MUTATION-PROXY: Execution operations and order lifecycle methods.
      Associated: `Trade`, `Trade.OrderSend()`, `Trade.OrderCheck()`,
        `Trade.PositionClose()`.
      Logging: DEBUG order dispatches and transaction life cycle.

Python API Usage:
    ```python
    from app.services.trading.trade import Trade

    trade = Trade(backend)
    ```

CLI Usage:
    ```bash
    uv run python -m app.services.trading.trade
    ```
"""

# ruff: noqa: N802 -- MQL5 PascalCase API compatibility
from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from app.host.logging import get_logger
from app.services.libs.contracts import (
    TradeCheckResult,
    TradeRequest,
    TradeResult,
)
from app.services.libs.enums import (
    OrderFilling,
    OrderTime,
    OrderType,
    TradeAction,
    TradeRetcode,
)

from .base import TradingClass

__all__ = [
    "Trade",
    "_build_trade_check_result",
    "_build_trade_request",
    "_build_trade_result",
    "_serialize_dict_request",
    "_serialize_request",
]

logger = get_logger(__name__)


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


def main() -> None:
    """Demonstrate Trade proxy request builders."""
    req_data = {"symbol": "EURUSD", "volume": 0.1, "action": TradeAction.DEAL}
    built = _build_trade_request(req_data)
    serialized = _serialize_request(built)
    print(f"Trade request built: symbol={serialized['symbol']}")


if __name__ == "__main__":
    main()
