"""Canonical set profit target strategy block."""

from __future__ import annotations

from app.core.data.contracts import (
    TradeResult,
)
from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.order._common import (
    set_protection,
)
from app.extend.blocks.order.runtime import TradingRuntime
from app.extend.blocks.order.types import (
    TradeFilter,
)


@block(
    BlockSpec(
        id="order.set_profit_target",
        name="Set Profit Target",
        description="Set an absolute target on matches, preserving each stop loss.",
        category="order",
        execution_kind=ExecutionKind.ORDER,
        inputs=(
            InputPort("context", PortType.ANY),
            InputPort("scope", PortType.ANY),
            InputPort("price", PortType.NUMBER),
        ),
        outputs=(OutputPort("result", PortType.ANY),),
        required_market_inputs=(),
        is_generation_eligible=False,
        is_deterministic=False,
        is_causal=True,
    )
)
async def set_profit_target(
    context: TradingRuntime,
    scope: TradeFilter,
    price: float,
    *,
    include_pending: bool = True,
) -> list[TradeResult]:
    """Set an absolute target on matches, preserving each stop loss.

    Zero removes the target. Set include_pending=False for positions only.
    """
    async with context.trade.operation_lock:
        return await set_protection(
            context, scope, tp=price, include_pending=include_pending
        )
