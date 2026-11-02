"""Bars since order open strategy block.

Description:
    Counts chart bar starts since the first matching active position was
    opened, or returns -1 if no matching position is open.
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-BARS-SINCE-ORDER-OPEN: Open position bar elapsed count.
Python API Usage:
    from app.extend.blocks.strategy_control.bars_since_order_open import (
        BarsSinceOrderOpen,
        bars_since_order_open,
    )
    bars = await bars_since_order_open(context, scope, bar_times, as_of=now)
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
from app.extend.blocks.order._common import (
    matching_positions,
)
from app.extend.functions.order_functions import (
    TradeFilter,
    aware_timestamp,
    bars_since,
)

logger = get_logger(__name__)

bars_since_order_open_spec = BlockSpec(
    id="strategy_control.bars_since_order_open",
    name="Bars Since Order Open",
    description=("Count bar starts since first matching entry; return -1 when absent."),
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


@block(bars_since_order_open_spec)
async def bars_since_order_open(
    context: TradingRuntime,
    scope: TradeFilter,
    bar_times: Sequence[datetime],
    *,
    as_of: datetime,
) -> int:
    """Count bar starts since first matching entry; return -1 when absent.

    Args:
        context: Active trading runtime context.
        scope: Filter defining symbol, magic, ticket, or order name.
        bar_times: Sequence of bar open timestamps.
        as_of: Current evaluation timestamp.

    Returns:
        Integer count of bars since open, or -1 if absent.
    """
    logger.debug(
        "FR-STRATEGY-CONTROL-BARS-SINCE-ORDER-OPEN: bars_since_order_open as_of=%s",
        as_of,
    )
    end = aware_timestamp(as_of)
    positions = await matching_positions(context, scope)
    if not positions:
        return -1
    position = positions[0]
    timestamp = position.time_msc / 1000 if position.time_msc else float(position.time)
    return bars_since(timestamp, bar_times, as_of) if timestamp <= end else -1


# Exact StrategyQuant donor snippet class alias
BarsSinceOrderOpen = bars_since_order_open

__all__ = [
    "BarsSinceOrderOpen",
    "bars_since_order_open",
    "bars_since_order_open_spec",
]
