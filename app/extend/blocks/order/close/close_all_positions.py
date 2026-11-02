"""Canonical close all positions strategy block."""

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
    close_positions,
    matching_positions,
)
from app.extend.blocks.order.runtime import TradingRuntime
from app.extend.blocks.order.types import (
    TradeFilter,
)


@block(
    BlockSpec(
        id="order.close_all_positions",
        name="Close All Positions",
        description="Close matching positions, stopping at the first incomplete close.",
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
async def close_all_positions(
    context: TradingRuntime, scope: TradeFilter
) -> list[TradeResult]:
    """Close matching positions, stopping at the first incomplete close."""
    async with context.trade.operation_lock:
        return await close_positions(context, await matching_positions(context, scope))
