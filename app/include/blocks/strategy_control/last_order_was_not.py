"""Canonical last order was not strategy block."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

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
from app.include.blocks.strategy_control.history import last_trade


@block(
    BlockSpec(
        id="strategy_control.last_order_was_not",
        name="Last Order Was Not",
        description=(
            "Test opposite last entry direction; false when no completed trade exists."
        ),
        category="strategy_control",
        execution_kind=ExecutionKind.CONDITION,
        inputs=(
            InputPort("context", PortType.ANY),
            InputPort("scope", PortType.ANY),
            InputPort("direction", PortType.NUMBER),
            InputPort("as_of", PortType.ANY, required=False, default=None),
        ),
        outputs=(OutputPort("result", PortType.BOOLEAN),),
        required_market_inputs=(),
        is_generation_eligible=False,
        is_deterministic=False,
        is_causal=True,
    )
)
async def last_order_was_not(
    context: TradingRuntime,
    scope: TradeFilter,
    direction: int,
    *,
    as_of: datetime | None = None,
) -> bool:
    """Test opposite last entry direction; false when no completed trade exists."""
    if type(direction) is not int or direction not in (-1, 1):
        raise ValueError("direction must be 1 or -1")
    trade = await last_trade(context, replace(scope, direction=0), 0, as_of)
    return trade is not None and trade.direction != direction
