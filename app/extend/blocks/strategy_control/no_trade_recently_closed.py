"""Canonical no trade recently closed strategy block."""

from __future__ import annotations

from datetime import datetime

from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.order.runtime import TradingRuntime
from app.extend.blocks.order.types import (
    TradeFilter,
)
from app.extend.blocks.strategy_control.trade_recently_closed import (
    trade_recently_closed,
)


@block(
    BlockSpec(
        id="strategy_control.no_trade_recently_closed",
        name="No Trade Recently Closed",
        description="Return the complement of the stable recent-completion predicate.",
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
async def no_trade_recently_closed(
    context: TradingRuntime,
    scope: TradeFilter,
    *,
    as_of: datetime,
    bar_start: datetime | None = None,
    check_this_bar: bool = True,
    check_this_minute: bool = True,
) -> bool:
    """Return the complement of the stable recent-completion predicate."""
    return not await trade_recently_closed(
        context,
        scope,
        as_of=as_of,
        bar_start=bar_start,
        check_this_bar=check_this_bar,
        check_this_minute=check_this_minute,
    )
