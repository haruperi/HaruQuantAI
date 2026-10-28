"""Canonical market position strategy block."""

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
)
from app.include.blocks.order.runtime import TradingRuntime
from app.include.blocks.order.types import (
    TradeFilter,
)


@block(
    BlockSpec(
        id="strategy_control.market_position",
        name="Market Position",
        description="Return first matching direction: 1 long, -1 short, or 0 flat.",
        category="strategy_control",
        execution_kind=ExecutionKind.EXPRESSION,
        inputs=(InputPort("context", PortType.ANY), InputPort("scope", PortType.ANY)),
        outputs=(OutputPort("result", PortType.NUMBER),),
        required_market_inputs=(),
        is_generation_eligible=False,
        is_deterministic=False,
        is_causal=True,
    )
)
async def market_position(context: TradingRuntime, scope: TradeFilter) -> int:
    """Return first matching direction: 1 long, -1 short, or 0 flat."""
    positions = await matching_positions(context, scope)
    return (1 if positions[0].position_type == 0 else -1) if positions else 0
