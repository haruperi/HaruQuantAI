"""Consolidated facade for order management and execution blocks.

Description:
    Provides an object-oriented and namespace-bound API facade over discrete
    StrategyQuant-faithful order opening, closing, modification, and sizing
    building blocks.
Purpose:
    FEAT-ORDER-BLOCKS: StrategyQuant donor-faithful order execution blocks.
Key Capabilities:
    - FR-ORDER-FACADE: Unified object interface for all order operations.
Python API Usage:
    from app.extend.blocks.order import Orders
    orders = Orders(runtime)
    await orders.enter_at_market("EURUSD", 1, 0.1)
CLI Usage:
    uv run pytest tests/extend/blocks/test_order_blocks.py --no-cov
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.core.data.contracts import SymbolInfo
from app.core.host.logging import get_logger
from app.core.trading.blocks.runtime import TradingRuntime
from app.core.trading.connection.contracts import TradeResult
from app.extend.blocks.order.close.close_all_pending_orders import (
    close_all_pending_orders,
)
from app.extend.blocks.order.close.close_all_positions import (
    close_all_positions,
)
from app.extend.blocks.order.close.close_best_position import (
    close_best_position,
)
from app.extend.blocks.order.close.close_pending_order import (
    close_pending_order,
)
from app.extend.blocks.order.close.close_position import (
    close_position,
)
from app.extend.blocks.order.close.close_worst_position import (
    close_worst_position,
)
from app.extend.blocks.order.modify.set_profit_target import (
    set_profit_target,
)
from app.extend.blocks.order.modify.set_stop_loss import (
    set_stop_loss,
)
from app.extend.blocks.order.open.enter_at_limit import (
    enter_at_limit,
)
from app.extend.blocks.order.open.enter_at_market import (
    enter_at_market,
)
from app.extend.blocks.order.open.enter_at_stop import (
    enter_at_stop,
)
from app.extend.blocks.order.open.enter_reverse_at_market import (
    enter_reverse_at_market,
)
from app.extend.formulas.price_level import (
    PriceFormulaMode,
    evaluate_price_level,
)
from app.extend.functions.order_functions import TradeFilter
from app.extend.money_management.sizing import SizingMethod, evaluate_sizing
from app.extend.trading.validity import schedule_bar_validity

logger = get_logger(__name__)


class Orders:
    """Consolidated facade for order management and execution blocks."""

    def __init__(self, context: TradingRuntime | None = None) -> None:
        """Initialize Orders facade with an optional default TradingRuntime context."""
        self._context = context
        logger.debug(
            "FR-ORDER-FACADE: Initialized Orders facade with context=%s", context
        )

    def _resolve_context(self, context: TradingRuntime | None) -> TradingRuntime:
        ctx = context if context is not None else self._context
        if ctx is None:
            raise ValueError(
                "A TradingRuntime context must be provided at init or call."
            )
        return ctx

    # -------------------------------------------------------------------------
    # Close operations
    # -------------------------------------------------------------------------

    async def close_all_pending_orders(
        self, scope: TradeFilter, *, context: TradingRuntime | None = None
    ) -> list[TradeResult]:
        """Cancel all matching pending orders."""
        ctx = self._resolve_context(context)
        return await close_all_pending_orders(ctx, scope)

    async def close_all_positions(
        self, scope: TradeFilter, *, context: TradingRuntime | None = None
    ) -> list[TradeResult]:
        """Close all matching open positions."""
        ctx = self._resolve_context(context)
        return await close_all_positions(ctx, scope)

    async def close_best_position(
        self, scope: TradeFilter, *, context: TradingRuntime | None = None
    ) -> TradeResult | None:
        """Close the matching position with the highest net profit."""
        ctx = self._resolve_context(context)
        return await close_best_position(ctx, scope)

    async def close_pending_order(
        self, scope: TradeFilter, *, context: TradingRuntime | None = None
    ) -> TradeResult | None:
        """Cancel the first matching pending order."""
        ctx = self._resolve_context(context)
        return await close_pending_order(ctx, scope)

    async def close_position(
        self,
        scope: TradeFilter,
        *,
        volume: float | None = None,
        context: TradingRuntime | None = None,
    ) -> TradeResult | None:
        """Close the first matching position, fully or by specified volume."""
        ctx = self._resolve_context(context)
        return await close_position(ctx, scope, volume=volume)

    async def close_worst_position(
        self, scope: TradeFilter, *, context: TradingRuntime | None = None
    ) -> TradeResult | None:
        """Close the matching position with the lowest net profit."""
        ctx = self._resolve_context(context)
        return await close_worst_position(ctx, scope)

    # -------------------------------------------------------------------------
    # Modify operations
    # -------------------------------------------------------------------------

    async def set_profit_target(
        self,
        scope: TradeFilter,
        price: float,
        *,
        include_pending: bool = True,
        context: TradingRuntime | None = None,
    ) -> list[TradeResult]:
        """Set or move profit target price on matching orders and positions."""
        ctx = self._resolve_context(context)
        return await set_profit_target(
            ctx, scope, price, include_pending=include_pending
        )

    async def set_stop_loss(
        self,
        scope: TradeFilter,
        price: float,
        *,
        include_pending: bool = True,
        tighten_only: bool = False,
        context: TradingRuntime | None = None,
    ) -> list[TradeResult]:
        """Set or move stop loss price on matching orders and positions."""
        ctx = self._resolve_context(context)
        return await set_stop_loss(
            ctx,
            scope,
            price,
            include_pending=include_pending,
            tighten_only=tighten_only,
        )

    # -------------------------------------------------------------------------
    # Open operations
    # -------------------------------------------------------------------------

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
        context: TradingRuntime | None = None,
    ) -> TradeResult | None:
        """Open a limit order at specified price level."""
        ctx = self._resolve_context(context)
        return await enter_at_limit(
            ctx,
            symbol,
            direction,
            volume,
            price,
            sl=sl,
            tp=tp,
            magic=magic,
            comment=comment,
            allow_duplicate_trades=allow_duplicate_trades,
            expiration=expiration,
            replace_existing=replace_existing,
        )

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
        context: TradingRuntime | None = None,
    ) -> TradeResult | None:
        """Open a market order at current quote price."""
        ctx = self._resolve_context(context)
        return await enter_at_market(
            ctx,
            symbol,
            direction,
            volume,
            sl=sl,
            tp=tp,
            magic=magic,
            comment=comment,
            allow_duplicate_trades=allow_duplicate_trades,
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
        context: TradingRuntime | None = None,
    ) -> TradeResult | None:
        """Open a stop order at specified price level."""
        ctx = self._resolve_context(context)
        return await enter_at_stop(
            ctx,
            symbol,
            direction,
            volume,
            price,
            sl=sl,
            tp=tp,
            magic=magic,
            comment=comment,
            allow_duplicate_trades=allow_duplicate_trades,
            expiration=expiration,
            replace_existing=replace_existing,
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
        context: TradingRuntime | None = None,
    ) -> TradeResult | None:
        """Reverse position at market, closing opposite positions first."""
        ctx = self._resolve_context(context)
        return await enter_reverse_at_market(
            ctx,
            symbol,
            direction,
            volume,
            sl=sl,
            tp=tp,
            magic=magic,
            comment=comment,
            allow_duplicate_trades=allow_duplicate_trades,
        )

    # -------------------------------------------------------------------------
    # Sizing, formulas, and validity evaluations
    # -------------------------------------------------------------------------

    def evaluate_sizing(
        self,
        method: SizingMethod,
        **kwargs: Any,
    ) -> float:
        """Calculate position size volume according to the chosen risk model."""
        return evaluate_sizing(method, **kwargs)

    def evaluate_price_level(
        self,
        mode: PriceFormulaMode,
        base_price: float,
        direction: int,
        *,
        pips: float = 0.0,
        pip_size: float = 0.0001,
        atr_value: float = 0.0,
        multiplier: float = 1.0,
        percent: float = 0.0,
        absolute_price: float = 0.0,
        is_protective: bool = False,
        spec: SymbolInfo | None = None,
    ) -> float:
        """Calculate absolute order price level from relative formula offset."""
        return evaluate_price_level(
            mode,
            base_price,
            direction,
            pips=pips,
            pip_size=pip_size,
            atr_value=atr_value,
            multiplier=multiplier,
            percent=percent,
            absolute_price=absolute_price,
            is_protective=is_protective,
            spec=spec,
        )

    def schedule_bar_validity(
        self,
        bar_start: datetime,
        timeframe: str,
        valid_bars: int,
    ) -> datetime | None:
        """Calculate pending order expiration datetime from discrete bar count."""
        return schedule_bar_validity(bar_start, timeframe, valid_bars)


__all__ = ["Orders"]
