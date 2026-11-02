"""Canonical bars since order closed strategy block."""

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
from app.extend.blocks.strategy_control.history import last_trade
from app.extend.functions.order_functions import (
    TradeFilter,
    bars_since,
)


@block(
    BlockSpec(
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
)
async def bars_since_order_closed(
    context: TradingRuntime,
    scope: TradeFilter,
    bar_times: Sequence[datetime],
    *,
    as_of: datetime,
) -> int:
    """Count chart bar starts since latest matching completion, or -1 if absent."""
    trade = await last_trade(context, scope, 0, as_of)
    return bars_since(trade.time_close_msc / 1000, bar_times, as_of) if trade else -1
