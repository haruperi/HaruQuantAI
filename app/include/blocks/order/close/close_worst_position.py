"""Canonical close worst position strategy block."""

from __future__ import annotations

from app.include.blocks.base import block
from app.include.blocks.metadata import (
    BlockSpec,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.blocks.order._common import (
    matching_positions,
    net_profit,
)
from app.include.blocks.order.runtime import TradingRuntime
from app.include.blocks.order.types import (
    TradeFilter,
)
from app.include.contracts import (
    TradeResult,
)


@block(
    BlockSpec(
        id="order.close_worst_position",
        name="Close Worst Position",
        description=(
            "Close the matching position with lowest profit plus swap and commission."
        ),
        category="order",
        execution_kind=ExecutionKind.ORDER,
        inputs=(InputPort("context", PortType.ANY), InputPort("scope", PortType.ANY)),
        outputs=(OutputPort("result", PortType.ANY),),
        required_market_inputs=(),
        is_generation_eligible=False,
        is_deterministic=False,
        is_causal=True,
    )
)
async def close_worst_position(
    context: TradingRuntime, scope: TradeFilter
) -> TradeResult | None:
    """Close the matching position with lowest profit plus swap and commission."""
    async with context.trade.operation_lock:
        positions = await matching_positions(context, scope)
        if not positions:
            return None
        return await context.trade.close(min(positions, key=net_profit))
