"""Canonical market position is flat strategy block."""

from __future__ import annotations

from app.core.trading.blocks.runtime import TradingRuntime
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
from app.extend.functions.order_functions import (
    TradeFilter,
)


@block(
    BlockSpec(
        id="strategy_control.market_position_is_flat",
        name="Market Position Is Flat",
        description="Return whether no matching market position exists.",
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
async def market_position_is_flat(context: TradingRuntime, scope: TradeFilter) -> bool:
    """Return whether no matching market position exists."""
    return not await matching_positions(context, scope)
