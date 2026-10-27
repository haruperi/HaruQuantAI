"""Shared asynchronous order execution and request/result access."""

# ruff: noqa: N802 -- MQL5 PascalCase API compatibility
from __future__ import annotations

import asyncio
import math
from dataclasses import asdict, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.host.logging import get_logger
from app.include.contracts import (
    BridgeError,
    OrderInfo,
    PositionInfo,
    SymbolInfo,
    TradeCheckResult,
    TradeRequest,
    TradeResult,
    TradingBackend,
)
from app.include.enums import (
    OrderFilling,
    OrderTime,
    OrderType,
    TradeAction,
    TradeRetcode,
)

from .base import (
    TradeFilter,
    TradingClass,
    build_trade_check_result,
    build_trade_result,
    normalize_request,
    serialize_request,
)
from .orders import OrderProxy
from .positions import PositionProxy
from .symbol import SymbolProxy

logger = get_logger(__name__)


class Trade(TradingClass):
    """Shared order actions and low-level asynchronous MQL5-compatible execution."""

    CLASS_NAME = "Trade"
    TRADING_METHODS = frozenset({"OrderSend"})

    def __init__(
        self,
        backend: TradingBackend,
        *,
        object_id: str | None = None,
        position: PositionProxy | None = None,
        order: OrderProxy | None = None,
        symbol: SymbolProxy | None = None,
    ) -> None:
        super().__init__(backend, object_id=object_id)
        self._position = position if position is not None else PositionProxy(backend)
        self._order = order if order is not None else OrderProxy(backend)
        self._symbol = symbol if symbol is not None else SymbolProxy(backend)
        self._operation_lock = asyncio.Lock()
        self._magic = 0
        self._deviation = 0
        self._filling: OrderFilling | None = None

    async def LogLevel(self, log_level: int) -> bool:
        """Set logging verbosity on the trade execution context."""
        return bool(await self._call("LogLevel", log_level))

    async def SetExpertMagicNumber(self, magic: int) -> None:
        """Set default magic number for subsequent orders."""
        await self._call("SetExpertMagicNumber", magic)
        self._magic = magic

    async def SetDeviationInPoints(self, deviation: int) -> None:
        """Set default slippage deviation in points for market orders."""
        await self._call("SetDeviationInPoints", deviation)
        self._deviation = deviation

    async def SetTypeFilling(self, filling: OrderFilling | int) -> None:
        """Set default order filling execution policy."""
        val = filling.value if isinstance(filling, OrderFilling) else filling
        await self._call("SetTypeFilling", val)
        self._filling = OrderFilling(val)

    async def SetTypeFillingBySymbol(self, symbol: str) -> bool:
        """Resolve and set the most appropriate filling mode supported by symbol."""
        spec = await self._symbol.SymbolInfo(symbol)
        filling = self._symbol_filling(spec)
        await self.SetTypeFilling(filling)
        return True

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
        logger.debug("FR-TRADING-MUTATION: executing OrderCheck")
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

    async def enter_at_market(
        self,
        symbol: str,
        direction: int,
        volume: float,
        *,
        sl: float = 0.0,
        tp: float = 0.0,
        magic: int | None = None,
        comment: str = "",
        allow_duplicate_trades: bool = False,
    ) -> TradeResult | None:
        """Enter at the current quote unless a matching position already exists.

        Direction is 1 for buy and -1 for sell; None means an entry was skipped.
        Size, stop loss, and target are evaluated values, not strategy formulas.
        """
        async with self._operation_lock:
            request = await self._entry_request(
                symbol,
                direction,
                volume,
                OrderType.BUY,
                price=0.0,
                sl=sl,
                tp=tp,
                magic=magic,
                comment=comment,
                expiration=None,
            )
            scope = TradeFilter(symbol, magic=request.magic, comment=comment)
            if not allow_duplicate_trades and await self._matching_positions(scope):
                return None
            return await self._checked_send(request)

    async def enter_at_limit(
        self,
        symbol: str,
        direction: int,
        volume: float,
        price: float,
        *,
        sl: float = 0.0,
        tp: float = 0.0,
        magic: int | None = None,
        comment: str = "",
        allow_duplicate_trades: bool = False,
        expiration: datetime | None = None,
        replace_existing: bool = True,
    ) -> TradeResult | None:
        """Place a limit entry, optionally replacing matching pending entries.

        Direction is 1 for buy and -1 for sell; None means an entry was skipped.
        Size, stop loss, and target are evaluated values, not strategy formulas.
        """
        async with self._operation_lock:
            request = await self._entry_request(
                symbol,
                direction,
                volume,
                OrderType.BUY_LIMIT,
                price=price,
                sl=sl,
                tp=tp,
                magic=magic,
                comment=comment,
                expiration=expiration,
            )
            scope = TradeFilter(symbol, magic=request.magic, comment=comment)
            if not allow_duplicate_trades and await self._matching_positions(scope):
                return None
            return await self._enter_pending(
                request, scope, replace_existing=replace_existing
            )

    async def enter_at_stop(
        self,
        symbol: str,
        direction: int,
        volume: float,
        price: float,
        *,
        sl: float = 0.0,
        tp: float = 0.0,
        magic: int | None = None,
        comment: str = "",
        allow_duplicate_trades: bool = False,
        expiration: datetime | None = None,
        replace_existing: bool = True,
    ) -> TradeResult | None:
        """Place a stop entry, optionally replacing matching pending entries.

        Direction is 1 for buy and -1 for sell; None means an entry was skipped.
        Size, stop loss, and target are evaluated values, not strategy formulas.
        """
        async with self._operation_lock:
            request = await self._entry_request(
                symbol,
                direction,
                volume,
                OrderType.BUY_STOP,
                price=price,
                sl=sl,
                tp=tp,
                magic=magic,
                comment=comment,
                expiration=expiration,
            )
            scope = TradeFilter(symbol, magic=request.magic, comment=comment)
            if not allow_duplicate_trades and await self._matching_positions(scope):
                return None
            return await self._enter_pending(
                request, scope, replace_existing=replace_existing
            )

    async def enter_reverse_at_market(
        self,
        symbol: str,
        direction: int,
        volume: float,
        *,
        sl: float = 0.0,
        tp: float = 0.0,
        magic: int | None = None,
        comment: str = "",
        allow_duplicate_trades: bool = False,
    ) -> TradeResult | None:
        """Close matching opposite positions, confirm closure, then enter.

        Direction is 1 for buy and -1 for sell; None means an entry was skipped.
        Size, stop loss, and target are evaluated values, not strategy formulas.
        """
        async with self._operation_lock:
            request = await self._entry_request(
                symbol,
                direction,
                volume,
                OrderType.BUY,
                price=0.0,
                sl=sl,
                tp=tp,
                magic=magic,
                comment=comment,
                expiration=None,
            )
            scope = TradeFilter(symbol, magic=request.magic, comment=comment)
            if not allow_duplicate_trades and await self._matching_positions(
                replace(scope, direction=direction)
            ):
                return None
            return await self._reverse_entry(
                request, scope, allow_duplicate_trades=allow_duplicate_trades
            )

    async def close_position(
        self, scope: TradeFilter, *, volume: float | None = None
    ) -> TradeResult | None:
        """Close the first matching position, fully or by an explicit volume."""
        async with self._operation_lock:
            positions = await self._matching_positions(scope)
            return await self._close(positions[0], volume) if positions else None

    async def close_all_positions(self, scope: TradeFilter) -> list[TradeResult]:
        """Close matching positions, stopping at the first incomplete close."""
        async with self._operation_lock:
            return await self._close_positions(await self._matching_positions(scope))

    async def close_best_position(self, scope: TradeFilter) -> TradeResult | None:
        """Close the matching position with highest profit plus swap and commission."""
        async with self._operation_lock:
            positions = await self._matching_positions(scope)
            if not positions:
                return None
            return await self._close(max(positions, key=self._net_profit))

    async def close_worst_position(self, scope: TradeFilter) -> TradeResult | None:
        """Close the matching position with lowest profit plus swap and commission."""
        async with self._operation_lock:
            positions = await self._matching_positions(scope)
            if not positions:
                return None
            return await self._close(min(positions, key=self._net_profit))

    async def cancel_pending_order(self, scope: TradeFilter) -> TradeResult | None:
        """Cancel the first matching pending order without touching positions."""
        async with self._operation_lock:
            orders = await self._matching_orders(scope)
            return await self._cancel(orders[0]) if orders else None

    async def cancel_all_pending_orders(self, scope: TradeFilter) -> list[TradeResult]:
        """Cancel a snapshot of matching pending orders, stopping on a failure."""
        async with self._operation_lock:
            return await self._cancel_orders(await self._matching_orders(scope))

    async def set_stop_loss(
        self,
        scope: TradeFilter,
        price: float,
        *,
        include_pending: bool = True,
        tighten_only: bool = False,
    ) -> list[TradeResult]:
        """Set an absolute stop price on matches, preserving each profit target.

        Zero removes the stop unless tighten_only=True, which preserves tighter stops.
        Set include_pending=False for positions only.
        """
        async with self._operation_lock:
            return await self._set_protection(
                scope,
                sl=price,
                include_pending=include_pending,
                tighten_only=tighten_only,
            )

    async def set_profit_target(
        self, scope: TradeFilter, price: float, *, include_pending: bool = True
    ) -> list[TradeResult]:
        """Set an absolute target on matches, preserving each stop loss.

        Zero removes the target. Set include_pending=False for positions only.
        """
        async with self._operation_lock:
            return await self._set_protection(
                scope, tp=price, include_pending=include_pending
            )

    async def _matching_positions(self, scope: TradeFilter) -> list[PositionInfo]:
        return [
            replace(p) for p in await self._position.PositionsGet() if scope.matches(p)
        ]

    async def _matching_orders(self, scope: TradeFilter) -> list[OrderInfo]:
        return [
            replace(o)
            for o in await self._order.OrdersGet()
            if o.order_type in (2, 3, 4, 5, 6, 7) and scope.matches(o)
        ]

    @staticmethod
    def _net_profit(position: PositionInfo) -> float:
        return position.profit + position.swap + position.commission

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
    def _level(value: float, spec: SymbolInfo) -> float:
        if not math.isfinite(value) or value < 0:
            raise ValueError("prices must be finite and nonnegative")
        step = spec.price.tick_step
        if not math.isfinite(step) or step <= 0:
            raise ValueError("symbol tick step must be positive")
        grid = Decimal(str(step))
        rounded = float(round(Decimal(str(value)) / grid) * grid)
        if value > 0 and rounded <= 0:
            raise ValueError("positive price is smaller than the symbol tick step")
        return rounded

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

    async def _entry_request(
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
            self._level(price, spec)
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
            sl=self._level(sl, spec),
            tp=self._level(tp, spec),
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

    async def _checked_send(self, request: TradeRequest) -> TradeResult:
        checked = await self.OrderCheck(request)
        # Native MT5 OrderCheck succeeds with zero; the simulator uses DONE.
        if checked.retcode not in (0, int(TradeRetcode.DONE)):
            return TradeResult(
                retcode=checked.retcode, comment=checked.comment, raw=checked
            )
        return await self.OrderSend(request)

    async def _close(
        self, position: PositionInfo, volume: float | None = None
    ) -> TradeResult:
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
        return await self._checked_send(
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

    async def _close_positions(
        self, positions: list[PositionInfo]
    ) -> list[TradeResult]:
        results = []
        for position in positions:
            result = await self._close(position)
            results.append(result)
            if result.retcode != int(TradeRetcode.DONE):
                break
        return results

    async def _cancel(self, order: OrderInfo) -> TradeResult:
        return await self._checked_send(
            TradeRequest(
                action=TradeAction.REMOVE,
                order=order.ticket,
                symbol=order.symbol,
                magic=order.magic,
                comment=order.comment,
            )
        )

    async def _cancel_orders(self, orders: list[OrderInfo]) -> list[TradeResult]:
        results = []
        for order in orders:
            result = await self._cancel(order)
            results.append(result)
            if result.retcode != int(TradeRetcode.DONE):
                break
        return results

    async def _enter_pending(
        self, request: TradeRequest, scope: TradeFilter, *, replace_existing: bool
    ) -> TradeResult | None:
        pending_scope = replace(
            scope, direction=1 if int(request.order_type) % 2 == 0 else -1
        )
        orders = await self._matching_orders(pending_scope)
        if orders and not replace_existing:
            return None
        checked = await self.OrderCheck(request)
        if checked.retcode not in (0, int(TradeRetcode.DONE)):
            return TradeResult(
                retcode=checked.retcode, comment=checked.comment, raw=checked
            )
        results = await self._cancel_orders(orders)
        if results and results[-1].retcode != int(TradeRetcode.DONE):
            return results[-1]
        if orders and await self._matching_orders(pending_scope):
            raise BridgeError(
                "Pending replacement cancellation is unconfirmed",
                code="OPERATION_UNCONFIRMED",
            )
        return await self._checked_send(request)

    async def _reverse_entry(
        self, request: TradeRequest, scope: TradeFilter, *, allow_duplicate_trades: bool
    ) -> TradeResult | None:
        direction = 1 if request.order_type == OrderType.BUY else -1
        opposite_scope = replace(scope, direction=-direction)
        results = await self._close_positions(
            await self._matching_positions(opposite_scope)
        )
        if results and results[-1].retcode != int(TradeRetcode.DONE):
            return results[-1]
        if await self._matching_positions(opposite_scope):
            raise BridgeError(
                "Opposite position closure is unconfirmed", code="OPERATION_UNCONFIRMED"
            )
        if not allow_duplicate_trades and await self._matching_positions(
            replace(scope, direction=direction)
        ):
            return None
        # Refresh the quote after closing; no order is retried automatically.
        spec = await self._symbol.SymbolInfo(request.symbol)
        request.price = spec.price.ask if direction == 1 else spec.price.bid
        if not math.isfinite(request.price) or request.price <= 0:
            raise ValueError("reversal requires a positive market quote")
        return await self._checked_send(request)

    async def _set_protection(
        self,
        scope: TradeFilter,
        *,
        sl: float | None = None,
        tp: float | None = None,
        include_pending: bool = True,
        tighten_only: bool = False,
    ) -> list[TradeResult]:
        price = sl if sl is not None else tp
        if price is None or not math.isfinite(price) or price < 0:
            raise ValueError("protection price must be finite and nonnegative")
        positions = await self._matching_positions(scope)
        orders = await self._matching_orders(scope) if include_pending else []
        results = []
        items: list[PositionInfo | OrderInfo] = [*positions, *orders]
        for item in items:
            spec = await self._symbol.SymbolInfo(item.symbol)
            if tighten_only and sl is not None and item.sl > 0:
                kind = (
                    item.position_type
                    if isinstance(item, PositionInfo)
                    else item.order_type
                )
                direction = 1 if kind in (0, 2, 4, 6) else -1
                if sl == 0 or direction * (self._level(sl, spec) - item.sl) <= 0:
                    results.append(
                        TradeResult(
                            retcode=int(TradeRetcode.NO_CHANGES),
                            price=item.sl,
                            comment="Existing stop is at least as protective",
                        )
                    )
                    continue
            request = TradeRequest(
                symbol=item.symbol,
                magic=item.magic,
                comment=item.comment,
                sl=self._level(sl, spec) if sl is not None else item.sl,
                tp=self._level(tp, spec) if tp is not None else item.tp,
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
            result = await self._checked_send(request)
            results.append(result)
            if result.retcode not in (
                int(TradeRetcode.DONE),
                int(TradeRetcode.NO_CHANGES),
            ):
                break
        return results
