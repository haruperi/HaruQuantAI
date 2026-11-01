"""Canonical market position size strategy block."""

from __future__ import annotations

from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.order._common import (
    matching_positions,
)
from app.extend.blocks.order.runtime import TradingRuntime
from app.extend.blocks.order.types import (
    TradeFilter,
)


@block(
    BlockSpec(
        id="strategy_control.market_position_size",
        name="Market Position Size",
        description=(
            "Sum matching position volumes without netting opposing directions."
        ),
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
async def market_position_size(context: TradingRuntime, scope: TradeFilter) -> float:
    """Sum matching position volumes without netting opposing directions."""
    return sum(position.volume for position in await matching_positions(context, scope))
