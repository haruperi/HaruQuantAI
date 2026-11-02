"""Shared pending replacement and entry execution workflow.

Description:
    Provides shared helper logic for market, limit, and stop entry execution
    under a unified runtime operation lock, including order checks, pending
    order cancellations, and position duplication guards.
Purpose:
    FEAT-ORDER-BLOCKS: StrategyQuant donor-faithful order execution blocks.
Key Capabilities:
    - FR-ORDER-OPEN-COMMON: Coordinate pending replacement and entry checks safely.
Python API Usage:
    from app.extend.blocks.order.open._common import execute_entry
CLI Usage:
    uv run pytest tests/extend/blocks/test_order_blocks.py --no-cov
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from app.core.data.contracts import (
    BridgeError,
    TradeRequest,
    TradeResult,
)
from app.core.enums import OrderType, TradeRetcode
from app.core.host.logging import get_logger
from app.core.trading.blocks.runtime import TradingRuntime
from app.extend.blocks.order._common import (
    cancel_orders,
    matching_orders,
    matching_positions,
)
from app.extend.functions.order_functions import TradeFilter

logger = get_logger(__name__)


async def _enter_pending(
    context: TradingRuntime,
    request: TradeRequest,
    scope: TradeFilter,
    *,
    replace_existing: bool,
) -> TradeResult | None:
    pending_scope = replace(
        scope, direction=1 if int(request.order_type) % 2 == 0 else -1
    )
    orders = await matching_orders(context, pending_scope)
    if orders and (not replace_existing):
        logger.debug("FR-ORDER-OPEN-COMMON: Pending order exists & replace=False; skip")
        return None
    checked = await context.trade.OrderCheck(request)
    if checked.retcode not in (0, int(TradeRetcode.DONE)):
        logger.debug(
            "FR-ORDER-OPEN-COMMON: OrderCheck rejected: code=%s comment=%s",
            checked.retcode,
            checked.comment,
        )
        return TradeResult(
            retcode=checked.retcode, comment=checked.comment, raw=checked
        )
    logger.debug(
        "FR-ORDER-OPEN-COMMON: Canceling %d pending orders for replacement",
        len(orders),
    )
    results = await cancel_orders(context, orders)
    if results and results[-1].retcode != int(TradeRetcode.DONE):
        return results[-1]
    if orders and await matching_orders(context, pending_scope):
        raise BridgeError(
            "Pending replacement cancellation is unconfirmed",
            code="OPERATION_UNCONFIRMED",
        )
    return await context.trade.send_checked(request)


async def execute_entry(
    context: TradingRuntime,
    symbol: str,
    direction: int,
    volume: float,
    buy_type: OrderType,
    *,
    price: float = 0.0,
    sl: float = 0.0,
    tp: float = 0.0,
    magic: int | None = None,
    comment: str = "",
    allow_duplicate_trades: bool = False,
    expiration: datetime | None = None,
    replace_existing: bool = True,
) -> TradeResult | None:
    """Execute the common market/limit/stop entry policy under one runtime lock."""
    async with context.trade.operation_lock:
        request = await context.trade.prepare_entry_request(
            symbol,
            direction,
            volume,
            buy_type,
            price=price,
            sl=sl,
            tp=tp,
            magic=magic,
            comment=comment,
            expiration=expiration,
        )
        scope = TradeFilter(symbol, magic=request.magic, comment=comment)
        if not allow_duplicate_trades and await matching_positions(context, scope):
            logger.debug(
                "FR-ORDER-OPEN-COMMON: Duplicate disallowed for scope=%s; skip",
                scope,
            )
            return None
        if buy_type == OrderType.BUY:
            return await context.trade.send_checked(request)
        return await _enter_pending(
            context, request, scope, replace_existing=replace_existing
        )


__all__ = ["execute_entry"]
