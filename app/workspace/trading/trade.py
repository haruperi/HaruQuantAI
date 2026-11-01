"""Shared asynchronous order execution and request/result access.

Description:
    Provides concrete asynchronous order execution without strategy selection policy.
    Implements OrderSend, OrderCheck, send_checked, prepare_entry_request, close,
    cancel, and modify_protection with strict volume quantization and slippage guards.
Purpose:
    FEAT-LIVE-TRADING-FACADE: Centralize live trading facade and order execution.
Key Capabilities:
    - FR-trading-order-send: Check and execute orders via broker backend with arming.
    - FR-trading-order-check: Validate orders and calculate margin/profit.
    - FR-trading-position-close: Close positions with volume validation.
    - FR-trading-order-cancel: Cancel working pending orders.
    - FR-trading-order-modify: Modify stop-loss and take-profit protections.
Python API Usage:
    from app.workspace.trading.trade import Trade
CLI Usage:
    uv run python -m pytest tests/workspace/trading -q
"""

# ruff: noqa: N802 -- MQL5 PascalCase API compatibility
from __future__ import annotations

import asyncio
import math
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from app.core.data.contracts import (
    BridgeError,
    OrderInfo,
    PositionInfo,
    SymbolInfo,
    TradeCheckResult,
    TradeRequest,
    TradeResult,
    TradingBackend,
)
from app.core.enums import (
    OrderFilling,
    OrderTime,
    OrderType,
    TradeAction,
    TradeRetcode,
)
from app.core.host.logging import get_logger
from app.extend.blocks.order.types import normalize_price

from .base import (
    TradingClass,
    build_trade_check_result,
    build_trade_result,
    normalize_request,
    serialize_request,
)
from .symbol import SymbolProxy

logger = get_logger(__name__)


class Trade(TradingClass):
    """Concrete asynchronous order execution without strategy selection policy."""

    CLASS_NAME = "Trade"
    TRADING_METHODS = frozenset({"OrderSend"})

    def __init__(
        self,
        backend: TradingBackend,
        *,
        object_id: str | None = None,
        symbol: SymbolProxy | None = None,
    ) -> None:
        super().__init__(backend, object_id=object_id)
        self._symbol = symbol if symbol is not None else SymbolProxy(backend)
        self._operation_lock = asyncio.Lock()
        self._magic = 0
        self._deviation = 0
        self._filling: OrderFilling | None = None

    @property
    def operation_lock(self) -> asyncio.Lock:
        """Serialize complete workflows across blocks using this executor."""
        return self._operation_lock

    async def LogLevel(self, log_level: int) -> bool:
        """Set logging verbosity on the trade execution context."""
        logger.debug(
            "FR-trading-order-send: setting log level", extra={"level": log_level}
        )
        return bool(await self._call("LogLevel", log_level))

    async def SetExpertMagicNumber(self, magic: int) -> None:
        """Set default magic number for subsequent orders."""
        logger.debug(
            "FR-trading-order-send: setting magic number", extra={"magic": magic}
        )
        await self._call("SetExpertMagicNumber", magic)
        self._magic = magic

    async def SetDeviationInPoints(self, deviation: int) -> None:
        """Set default slippage deviation in points for market orders."""
        logger.debug(
            "FR-trading-order-send: setting deviation points",
            extra={"deviation": deviation},
        )
        await self._call("SetDeviationInPoints", deviation)
        self._deviation = deviation

    async def SetTypeFilling(self, filling: OrderFilling | int) -> None:
        """Set default order filling execution policy."""
        val = filling.value if isinstance(filling, OrderFilling) else filling
        logger.debug(
            "FR-trading-order-send: setting filling mode", extra={"filling": val}
        )
        await self._call("SetTypeFilling", val)
        self._filling = OrderFilling(val)

    async def SetTypeFillingBySymbol(self, symbol: str) -> bool:
        """Resolve and set the most appropriate filling mode supported by symbol."""
        logger.debug(
            "FR-trading-order-send: resolving filling mode by symbol",
            extra={"symbol": symbol},
        )
        spec = await self._symbol.SymbolInfo(symbol)
        filling = self._symbol_filling(spec)
        await self.SetTypeFilling(filling)
        return True

    async def SetAsyncMode(self, mode: bool) -> None:
        """Enable or disable asynchronous order sending mode."""
        logger.debug("FR-trading-order-send: setting async mode", extra={"mode": mode})
        await self._call("SetAsyncMode", mode)

    async def SetMarginMode(self) -> None:
        """Recalculate margin mode based on account and connected broker terminal."""
        logger.debug("FR-trading-order-send: setting margin mode")
        await self._call("SetMarginMode")

    async def OrderSend(
        self,
        request: TradeRequest | dict[str, Any],
        result: TradeResult | None = None,
    ) -> TradeResult:
        """Send a trade request to the broker terminal."""
        logger.debug("FR-trading-order-send: executing OrderSend")
        raw = await self._call("OrderSend", serialize_request(request))
        if isinstance(raw, TradeResult):
            res = raw
        elif isinstance(raw, dict):
            res = build_trade_result(raw)
        else:
            raise TypeError(
                f"Expected TradeResult or dict from OrderSend, got {type(raw).__name__}"
            )
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
        logger.debug("FR-trading-order-check: executing OrderCheck")
        raw = await self._call("OrderCheck", serialize_request(request))
        if isinstance(raw, TradeCheckResult):
            res = raw
        elif isinstance(raw, dict):
            res = build_trade_check_result(raw)
        else:
            raise TypeError(
                "Expected TradeCheckResult or dict from OrderCheck, "
                f"got {type(raw).__name__}"
            )
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
        logger.debug("FR-trading-order-send: fetching last request snapshot")
        raw = await self._call("Request")
        if isinstance(raw, TradeRequest):
            return raw
        if isinstance(raw, dict):
            return normalize_request(raw)
        raise TypeError(
            f"Expected TradeRequest or dict from Request, got {type(raw).__name__}"
        )

    async def Result(self) -> TradeResult:
        """Fetch the last trade result snapshot."""
        logger.debug("FR-trading-order-send: fetching last result snapshot")
        raw = await self._call("Result")
        if isinstance(raw, TradeResult):
            return raw
        if isinstance(raw, dict):
            return build_trade_result(raw)
        raise TypeError(
            f"Expected TradeResult or dict from Result, got {type(raw).__name__}"
        )

    async def CheckResult(self) -> TradeCheckResult:
        """Fetch the last trade check result snapshot."""
        logger.debug("FR-trading-order-check: fetching last check result snapshot")
        raw = await self._call("CheckResult")
        if isinstance(raw, TradeCheckResult):
            return raw
        if isinstance(raw, dict):
            return build_trade_check_result(raw)
        raise TypeError(
            "Expected TradeCheckResult or dict from CheckResult, "
            f"got {type(raw).__name__}"
        )

    async def PrintRequest(self) -> bool:
        """Log the last trade request metadata."""
        logger.debug("FR-trading-order-send: printing request")
        return bool(await self._call("PrintRequest"))

    async def PrintResult(self) -> bool:
        """Log the last trade result metadata."""
        logger.debug("FR-trading-order-send: printing result")
        return bool(await self._call("PrintResult"))

    async def FormatRequest(self) -> str:
        """Format the last trade request as a text string."""
        logger.debug("FR-trading-order-send: formatting request")
        return str(await self._call("FormatRequest"))

    async def FormatRequestResult(self) -> str:
        """Format the last trade request and result as a text string."""
        logger.debug("FR-trading-order-send: formatting request and result")
        return str(await self._call("FormatRequestResult"))

    @staticmethod
    def _symbol_filling(spec: SymbolInfo) -> OrderFilling:
        if "Fill or Kill" in spec.trade.filling:
            return OrderFilling.FOK
        if "Immediate or Cancel" in spec.trade.filling:
            return OrderFilling.IOC
        if spec.trade.execution != "Market":
            return OrderFilling.RETURN
        raise BridgeError("Symbol has no supported filling policy", code="INVALID_FILL")

    @staticmethod
    def _validate_volume(volume: float, spec: SymbolInfo) -> None:
        if (
            not math.isfinite(volume)
            or (
                volume < spec.volume.min
                and not math.isclose(volume, spec.volume.min, abs_tol=1e-9)
            )
            or (
                volume > spec.volume.max
                and not math.isclose(volume, spec.volume.max, abs_tol=1e-9)
            )
        ):
            raise ValueError("volume must be within symbol volume limits")
        step = spec.volume.step
        if not math.isfinite(step) or step <= 0:
            raise ValueError("symbol volume step must be positive")
        steps = (volume - spec.volume.min) / step
        if not math.isclose(steps, round(steps), rel_tol=0.0, abs_tol=1e-7):
            raise ValueError("volume must align to the symbol volume step")

    async def prepare_entry_request(
        self,
        symbol: str,
        direction: int,
        volume: float,
        buy_type: OrderType,
        *,
        price: float,
        sl: float,
        tp: float,
        magic: int | None,
        comment: str,
        expiration: datetime | None,
    ) -> TradeRequest:
        """Validate and normalize one concrete entry request."""
        logger.debug(
            "FR-trading-order-send: preparing entry request",
            extra={"symbol": symbol, "direction": direction, "volume": volume},
        )
        if type(direction) is not int or direction not in (-1, 1):
            raise ValueError("entry direction must be 1 or -1")
        if not symbol or symbol in ("Current", "Any"):
            raise ValueError("entry requires a resolved symbol name")
        if not math.isfinite(volume) or volume <= 0:
            raise ValueError("volume must be finite and positive")
        if expiration is not None and expiration.tzinfo is None:
            raise ValueError("expiration must include a timezone")
        spec = await self._symbol.SymbolInfo(symbol)
        self._validate_volume(volume, spec)
        pending = buy_type != OrderType.BUY
        if pending and (not math.isfinite(price) or price <= 0):
            raise ValueError("pending price must be finite and positive")
        level = (
            normalize_price(price, spec)
            if pending
            else (spec.price.ask if direction == 1 else spec.price.bid)
        )
        if not math.isfinite(level) or level <= 0:
            raise ValueError("entry requires a positive market quote or price")
        return TradeRequest(
            action=TradeAction.PENDING if pending else TradeAction.DEAL,
            symbol=symbol,
            volume=volume,
            order_type=buy_type if direction == 1 else OrderType(int(buy_type) + 1),
            price=level,
            sl=normalize_price(sl, spec),
            tp=normalize_price(tp, spec),
            magic=self._magic if magic is None else magic,
            comment=comment,
            deviation=self._deviation,
            type_filling=OrderFilling.RETURN
            if pending
            else (
                self._filling
                if self._filling is not None
                else self._symbol_filling(spec)
            ),
            type_time=OrderTime.SPECIFIED if expiration is not None else OrderTime.GTC,
            expiration=expiration,
        )

    async def send_checked(self, request: TradeRequest) -> TradeResult:
        """Check and submit one concrete execution request."""
        logger.debug(
            "FR-trading-order-send: sending checked order",
            extra={"symbol": request.symbol},
        )
        checked = await self.OrderCheck(request)
        # Native MT5 OrderCheck succeeds with zero; the simulator uses DONE.
        if checked.retcode not in (0, int(TradeRetcode.DONE)):
            return TradeResult(
                retcode=checked.retcode, comment=checked.comment, raw=checked
            )
        return await self.OrderSend(request)

    async def close(
        self, position: PositionInfo, volume: float | None = None
    ) -> TradeResult:
        """Close one explicitly selected position snapshot."""
        logger.debug(
            "FR-trading-position-close: closing position",
            extra={"ticket": position.ticket},
        )
        amount = position.volume if volume is None else volume
        if not math.isfinite(amount) or amount <= 0 or amount > position.volume:
            raise ValueError(
                "close volume must be positive and no greater than position volume"
            )
        spec = await self._symbol.SymbolInfo(position.symbol)
        self._validate_volume(amount, spec)
        remaining = position.volume - amount
        if not math.isclose(remaining, 0.0, abs_tol=1e-9):
            self._validate_volume(remaining, spec)
        selling = position.position_type == 0
        price = spec.price.bid if selling else spec.price.ask
        if not math.isfinite(price) or price <= 0:
            raise ValueError("close requires a positive market quote")
        return await self.send_checked(
            TradeRequest(
                action=TradeAction.DEAL,
                symbol=position.symbol,
                position=position.ticket,
                order_type=OrderType.SELL if selling else OrderType.BUY,
                volume=amount,
                price=price,
                magic=position.magic,
                comment=position.comment,
                deviation=self._deviation,
                type_filling=self._filling
                if self._filling is not None
                else self._symbol_filling(spec),
            )
        )

    async def cancel(self, order: OrderInfo) -> TradeResult:
        """Cancel one explicitly selected pending order."""
        logger.debug(
            "FR-trading-order-cancel: canceling pending order",
            extra={"ticket": order.ticket},
        )
        return await self.send_checked(
            TradeRequest(
                action=TradeAction.REMOVE,
                order=order.ticket,
                symbol=order.symbol,
                magic=order.magic,
                comment=order.comment,
            )
        )

    async def modify_protection(
        self,
        item: PositionInfo | OrderInfo,
        *,
        sl: float | None = None,
        tp: float | None = None,
    ) -> TradeResult:
        """Normalize and submit protection for one explicitly selected record."""
        logger.debug(
            "FR-trading-order-modify: modifying protection",
            extra={"ticket": item.ticket},
        )
        for value in (sl, tp):
            if value is not None and (not math.isfinite(value) or value < 0):
                raise ValueError("protection price must be finite and nonnegative")
        spec = await self._symbol.SymbolInfo(item.symbol)
        request = TradeRequest(
            symbol=item.symbol,
            magic=item.magic,
            comment=item.comment,
            sl=normalize_price(sl, spec) if sl is not None else item.sl,
            tp=normalize_price(tp, spec) if tp is not None else item.tp,
        )
        if isinstance(item, PositionInfo):
            request.action = TradeAction.SLTP
            request.position = item.ticket
        else:
            request.action = TradeAction.MODIFY
            request.order = item.ticket
            request.order_type = OrderType(item.order_type)
            request.price = item.price_open
            request.stoplimit = item.price_stop_limit
            request.type_time = OrderTime(item.type_time)
            request.type_filling = OrderFilling(item.type_filling)
            if item.time_expiration:
                request.expiration = datetime.fromtimestamp(
                    item.time_expiration, tz=UTC
                )
        return await self.send_checked(request)
