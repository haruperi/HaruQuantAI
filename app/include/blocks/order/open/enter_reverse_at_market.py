"""Canonical enter reverse at market strategy block."""

from __future__ import annotations

import math
from dataclasses import replace

from app.include.blocks.base import block
from app.include.blocks.metadata import (
    BlockSpec,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.blocks.order._common import (
    close_positions,
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


@block(
    BlockSpec(
        id="order.enter_reverse_at_market",
        name="Enter Reverse At Market",
        description="Close matching opposite positions, confirm closure, then enter.",
        category="order",
        execution_kind=ExecutionKind.ORDER,
        inputs=(
            InputPort("context", PortType.ANY),
            InputPort("symbol", PortType.STRING),
            InputPort("direction", PortType.NUMBER),
            InputPort("volume", PortType.NUMBER),
        ),
        outputs=(OutputPort("result", PortType.ANY),),
        required_market_inputs=(),
        is_generation_eligible=False,
        is_deterministic=False,
        is_causal=True,
    )
)
async def enter_reverse_at_market(
    context: TradingRuntime,
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
    async with context.trade.operation_lock:
        request = await context.trade.prepare_entry_request(
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
        if not allow_duplicate_trades and await matching_positions(
            context, replace(scope, direction=direction)
        ):
            return None
        return await _reverse_entry(
            context, request, scope, allow_duplicate_trades=allow_duplicate_trades
        )


async def _reverse_entry(
    context: TradingRuntime,
    request: TradeRequest,
    scope: TradeFilter,
    *,
    allow_duplicate_trades: bool,
) -> TradeResult | None:
    direction = 1 if request.order_type == OrderType.BUY else -1
    opposite_scope = replace(scope, direction=-direction)
    results = await close_positions(
        context, await matching_positions(context, opposite_scope)
    )
    if results and results[-1].retcode != int(TradeRetcode.DONE):
        return results[-1]
    if await matching_positions(context, opposite_scope):
        raise BridgeError(
            "Opposite position closure is unconfirmed", code="OPERATION_UNCONFIRMED"
        )
    if not allow_duplicate_trades and await matching_positions(
        context, replace(scope, direction=direction)
    ):
        return None
    spec = await context.symbol.SymbolInfo(request.symbol)
    request.price = spec.price.ask if direction == 1 else spec.price.bid
    if not math.isfinite(request.price) or request.price <= 0:
        raise ValueError("reversal requires a positive market quote")
    return await context.trade.send_checked(request)
