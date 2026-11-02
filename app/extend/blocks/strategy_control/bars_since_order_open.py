"""Canonical bars since order open strategy block."""

from __future__ import annotations

from collections.abc import Sequence
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
from app.extend.blocks.order._common import (
    matching_positions,
)
from app.extend.functions.order_functions import (
    TradeFilter,
    aware_timestamp,
    bars_since,
)


@block(
    BlockSpec(
        id="strategy_control.bars_since_order_open",
        name="Bars Since Order Open",
        description=(
            "Count bar starts since first matching entry; return -1 when absent."
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
)
async def bars_since_order_open(
    context: TradingRuntime,
    scope: TradeFilter,
    bar_times: Sequence[datetime],
    *,
    as_of: datetime,
) -> int:
    """Count bar starts since first matching entry; return -1 when absent."""
    end = aware_timestamp(as_of)
    positions = await matching_positions(context, scope)
    if not positions:
        return -1
    position = positions[0]
    timestamp = position.time_msc / 1000 if position.time_msc else float(position.time)
    return bars_since(timestamp, bar_times, as_of) if timestamp <= end else -1
