"""Bars since order closed strategy block.

Description:
    Counts chart bar starts since the latest matching completed position exit,
    or returns -1 if no matching closed trade is found.
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-BARS-SINCE-ORDER-CLOSED: Closed trade bar elapsed count.
Python API Usage:
    from app.extend.blocks.strategy_control.bars_since_order_closed import (
        BarsSinceOrderClosed,
        bars_since_order_closed,
    )
    bars = await bars_since_order_closed(context, scope, bar_times, as_of=now)
CLI Usage:
    uv run pytest tests/extend/blocks/test_strategy_control.py --no-cov
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from app.core.host.logging import get_logger
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
    bars_since,
)

logger = get_logger(__name__)

bars_since_order_closed_spec = BlockSpec(
    id="strategy_control.bars_since_order_closed",
    name="Bars Since Order Closed",
    description=(
        "Count chart bar starts since latest matching completion, or -1 if absent."
    ),
    category="strategy_control",
    execution_kind=ExecutionKind.EXPRESSION,
    inputs=(
        InputPort("context", PortType.ANY),
        InputPort("scope", PortType.ANY),
        InputPort("bar_times", PortType.ANY),
        InputPort("as_of", PortType.ANY),
    ),
    outputs=(OutputPort("result", PortType.NUMBER),),
    required_market_inputs=(),
    is_generation_eligible=False,
    is_deterministic=False,
    is_causal=True,
)


@block(bars_since_order_closed_spec)
async def bars_since_order_closed(
    context: TradingRuntime,
    scope: TradeFilter,
    bar_times: Sequence[datetime],
    *,
    as_of: datetime,
) -> int:
    """Count chart bar starts since latest matching completion, or -1 if absent.

    Args:
        context: Active trading runtime context.
        scope: Filter defining symbol, magic, ticket, or order name.
        bar_times: Sequence of bar open timestamps.
        as_of: Current evaluation timestamp.

    Returns:
        Integer count of bars since close, or -1 if absent.
    """
    logger.debug(
        "FR-STRATEGY-CONTROL-BARS-SINCE-ORDER-CLOSED: bars_since_order_closed as_of=%s",
        as_of,
    )
    trade = await last_trade(context, scope, 0, as_of)
    if not trade:
        return -1
    return bars_since(trade.time_close_msc / 1000, bar_times, as_of)


# Exact StrategyQuant donor snippet class alias
BarsSinceOrderClosed = bars_since_order_closed

__all__ = [
    "BarsSinceOrderClosed",
    "bars_since_order_closed",
    "bars_since_order_closed_spec",
]
