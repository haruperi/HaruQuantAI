"""Canonical last order was strategy block."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from app.core.trading.blocks.runtime import TradingRuntime
from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.strategy_control.history import last_trade
from app.extend.functions.order_functions import (
    TradeFilter,
)


@block(
    BlockSpec(
        id="strategy_control.last_order_was",
        name="Last Order Was",
        description=(
            "Test last completed entry direction; pending cancellations are excluded."
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
async def last_order_was(
    context: TradingRuntime,
    scope: TradeFilter,
    direction: int,
    *,
    as_of: datetime | None = None,
) -> bool:
    """Test last completed entry direction; pending cancellations are excluded."""
    if type(direction) is not int or direction not in (-1, 1):
        raise ValueError("direction must be 1 or -1")
    trade = await last_trade(context, replace(scope, direction=0), 0, as_of)
    return trade is not None and trade.direction == direction
