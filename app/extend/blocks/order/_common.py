"""Reusable order selection and batch execution shared by canonical blocks.

Description:
    Provides shared matching, ranking, batch execution, and protection setting
    routines across all canonical order management blocks under strict broker
    contract constraints.
Purpose:
    FEAT-ORDER-BLOCKS: StrategyQuant donor-faithful order execution blocks.
Key Capabilities:
    - FR-ORDER-COMMON: Reusable position and order snapshot filtering and modification.
Python API Usage:
    from app.extend.blocks.order._common import matching_positions, set_protection
CLI Usage:
    uv run pytest tests/extend/blocks/test_order_blocks.py --no-cov
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import replace

from app.core.data.contracts import OrderInfo, PositionInfo, TradeResult
from app.core.enums import TradeRetcode
from app.core.host.logging import get_logger
from app.extend.blocks.order.runtime import TradingRuntime
from app.extend.blocks.order.types import TradeFilter, normalize_price

logger = get_logger(__name__)


async def matching_positions(
    context: TradingRuntime, scope: TradeFilter
) -> list[PositionInfo]:
    """Read matching position snapshots in backend order."""
    positions = [
        replace(p) for p in await context.position.PositionsGet() if scope.matches(p)
    ]
    logger.debug(
        "FR-ORDER-COMMON: Filtered %d matching positions for scope=%s",
        len(positions),
        scope,
    )
    return positions


async def matching_orders(
    context: TradingRuntime, scope: TradeFilter
) -> list[OrderInfo]:
    """Read only matching pending orders."""
    orders = [
        replace(o)
        for o in await context.order.OrdersGet()
        if o.order_type in (2, 3, 4, 5, 6, 7) and scope.matches(o)
    ]
    logger.debug(
        "FR-ORDER-COMMON: Filtered %d matching pending orders for scope=%s",
        len(orders),
        scope,
    )
    return orders


def net_profit(position: PositionInfo) -> float:
    """Rank current positions by net reported profit."""
    return position.profit + position.swap + position.commission


async def close_positions(
    context: TradingRuntime, positions: Sequence[PositionInfo]
) -> list[TradeResult]:
    """Close selected positions, stopping on an incomplete result."""
    results = []
    for position in positions:
        result = await context.trade.close(position)
        results.append(result)
        logger.debug(
            "FR-ORDER-COMMON: Closed position ticket=%s -> retcode=%s",
            position.ticket,
            result.retcode,
        )
        if result.retcode != int(TradeRetcode.DONE):
            break
    return results


async def cancel_orders(
    context: TradingRuntime, orders: Sequence[OrderInfo]
) -> list[TradeResult]:
    """Cancel selected orders, stopping on an incomplete result."""
    results = []
    for order in orders:
        result = await context.trade.cancel(order)
        results.append(result)
        logger.debug(
            "FR-ORDER-COMMON: Canceled pending order ticket=%s -> retcode=%s",
            order.ticket,
            result.retcode,
        )
        if result.retcode != int(TradeRetcode.DONE):
            break
    return results


async def set_protection(
    context: TradingRuntime,
    scope: TradeFilter,
    *,
    sl: float | None = None,
    tp: float | None = None,
    include_pending: bool = True,
    tighten_only: bool = False,
) -> list[TradeResult]:
    """Select protection targets and enforce the strategy tightening policy."""
    price = sl if sl is not None else tp
    if price is None or not math.isfinite(price) or price < 0:
        raise ValueError("protection price must be finite and nonnegative")
    positions = await matching_positions(context, scope)
    orders = await matching_orders(context, scope) if include_pending else []
    items: list[PositionInfo | OrderInfo] = [*positions, *orders]
    logger.debug(
        "FR-ORDER-COMMON: Protection (sl=%s, tp=%s) on %d items (tighten=%s)",
        sl,
        tp,
        len(items),
        tighten_only,
    )
    results = []
    for item in items:
        if tighten_only and sl is not None and item.sl > 0:
            spec = await context.symbol.SymbolInfo(item.symbol)
            rounded = normalize_price(sl, spec)
            kind = (
                item.position_type
                if isinstance(item, PositionInfo)
                else item.order_type
            )
            direction = 1 if kind in (0, 2, 4, 6) else -1
            if sl == 0 or direction * (rounded - item.sl) <= 0:
                logger.debug(
                    "FR-ORDER-COMMON: Keep tighter stop %s (requested %s)",
                    item.sl,
                    rounded,
                )
                results.append(
                    TradeResult(
                        retcode=int(TradeRetcode.NO_CHANGES),
                        price=item.sl,
                        comment="Existing stop is at least as protective",
                    )
                )
                continue
        result = await context.trade.modify_protection(item, sl=sl, tp=tp)
        results.append(result)
        if result.retcode not in (int(TradeRetcode.DONE), int(TradeRetcode.NO_CHANGES)):
            break
    return results


__all__ = [
    "cancel_orders",
    "close_positions",
    "matching_orders",
    "matching_positions",
    "net_profit",
    "set_protection",
]
