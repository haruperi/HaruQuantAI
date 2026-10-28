"""Canonical trade recently closed strategy block."""

from __future__ import annotations

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
    aware_timestamp,
)
from app.include.blocks.strategy_control.history import closed_trades


@block(
    BlockSpec(
        id="strategy_control.trade_recently_closed",
        name="Trade Recently Closed",
        description="Test a recent completion without consuming the matching event.",
        category="strategy_control",
        execution_kind=ExecutionKind.CONDITION,
        inputs=(
            InputPort("context", PortType.ANY),
            InputPort("scope", PortType.ANY),
            InputPort("as_of", PortType.ANY),
            InputPort("bar_start", PortType.ANY, required=False, default=None),
        ),
        outputs=(OutputPort("result", PortType.BOOLEAN),),
        required_market_inputs=(),
        is_generation_eligible=False,
        is_deterministic=False,
        is_causal=True,
    )
)
async def trade_recently_closed(
    context: TradingRuntime,
    scope: TradeFilter,
    *,
    as_of: datetime,
    bar_start: datetime | None = None,
    check_this_bar: bool = True,
    check_this_minute: bool = True,
) -> bool:
    """Test a recent completion without consuming the matching event."""
    end = aware_timestamp(as_of)
    starts = []
    if check_this_bar:
        if bar_start is None:
            raise ValueError("bar_start is required when checking this bar")
        start = aware_timestamp(bar_start)
        if start > end:
            raise ValueError("bar_start must not exceed evaluation time")
        starts.append(start)
    if check_this_minute:
        starts.append(end - end % 60)
    if not starts:
        return False
    return any(
        min(starts) <= trade.time_close_msc / 1000 <= end
        for trade in await closed_trades(context, scope, as_of=as_of)
    )
