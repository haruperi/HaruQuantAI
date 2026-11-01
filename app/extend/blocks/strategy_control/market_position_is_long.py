"""Canonical market position is long strategy block."""

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
        id="strategy_control.market_position_is_long",
        name="Market Position Is Long",
        description=(
            "Return whether any matching position is long, including hedged accounts."
        ),
        category="strategy_control",
        execution_kind=ExecutionKind.CONDITION,
        inputs=(InputPort("context", PortType.ANY), InputPort("scope", PortType.ANY)),
        outputs=(OutputPort("result", PortType.BOOLEAN),),
        required_market_inputs=(),
        is_generation_eligible=False,
        is_deterministic=False,
        is_causal=True,
    )
)
async def market_position_is_long(context: TradingRuntime, scope: TradeFilter) -> bool:
    """Return whether any matching position is long, including hedged accounts."""
    return any(
        position.position_type == 0
        for position in await matching_positions(context, scope)
    )
