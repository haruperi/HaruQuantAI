"""Shared pending replacement workflow."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from app.include.blocks.order._common import (
    cancel_orders,
    matching_orders,
    matching_positions,
)
from app.include.blocks.order.runtime import TradingRuntime
from app.include.blocks.order.types import (
    TradeFilter,
)
from app.include.contracts import (
    BridgeError,
    TradeRequest,
    TradeResult,
)
from app.include.enums import OrderType, TradeRetcode


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
        return None
    checked = await context.trade.OrderCheck(request)
    if checked.retcode not in (0, int(TradeRetcode.DONE)):
        return TradeResult(
            retcode=checked.retcode, comment=checked.comment, raw=checked
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
            return None
        if buy_type == OrderType.BUY:
            return await context.trade.send_checked(request)
        return await _enter_pending(
            context, request, scope, replace_existing=replace_existing
        )
