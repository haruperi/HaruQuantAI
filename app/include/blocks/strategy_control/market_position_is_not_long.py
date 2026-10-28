"""Canonical market position is not long strategy block."""

from __future__ import annotations

from app.include.blocks.base import block
from app.include.blocks.metadata import (
    BlockSpec,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.blocks.order.runtime import TradingRuntime
from app.include.blocks.order.types import (
    TradeFilter,
)
from app.include.blocks.strategy_control.market_position_is_long import (
    market_position_is_long,
)


@block(
    BlockSpec(
        id="strategy_control.market_position_is_not_long",
        name="Market Position Is Not Long",
        description="Return whether no matching long position exists.",
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
async def market_position_is_not_long(
    context: TradingRuntime, scope: TradeFilter
) -> bool:
    """Return whether no matching long position exists."""
    return not await market_position_is_long(context, scope)
