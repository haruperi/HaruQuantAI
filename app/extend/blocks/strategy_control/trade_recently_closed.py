"""Trade recently closed strategy block.

Description:
    Tests whether a matching trade was completed recently (during the current
    bar or the current minute) without consuming or modifying the trade event.
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-TRADE-RECENTLY-CLOSED: Recent trade completion detection.
Python API Usage:
    from app.extend.blocks.strategy_control.trade_recently_closed import (
        TradeRecentlyClosed,
        trade_recently_closed,
    )
    closed = await trade_recently_closed(context, scope, as_of=now)
CLI Usage:
    uv run pytest tests/extend/blocks/test_strategy_control.py --no-cov
"""

from __future__ import annotations

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
from app.extend.blocks.strategy_control.history import closed_trades
from app.extend.functions.order_functions import (
    TradeFilter,
    aware_timestamp,
)

logger = get_logger(__name__)

trade_recently_closed_spec = BlockSpec(
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


@block(trade_recently_closed_spec)
async def trade_recently_closed(
    context: TradingRuntime,
    scope: TradeFilter,
    *,
    as_of: datetime,
    bar_start: datetime | None = None,
    check_this_bar: bool = True,
    check_this_minute: bool = True,
) -> bool:
    """Test a recent completion without consuming the matching event.

    Args:
        context: Active trading runtime context.
        scope: Filter defining symbol, magic, ticket, or order name.
        as_of: Current evaluation timestamp.
        bar_start: Optional open timestamp of the current bar.
        check_this_bar: If True, inspect within the current bar.
        check_this_minute: If True, inspect within the last 60 seconds.

    Returns:
        True if a matching trade was completed recently, False otherwise.
    """
    logger.debug(
        "FR-STRATEGY-CONTROL-TRADE-RECENTLY-CLOSED: Evaluating as_of=%s",
        as_of,
    )
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
    trades = await closed_trades(context, scope, as_of=as_of)
    return any(min(starts) <= trade.time_close_msc / 1000 <= end for trade in trades)


# Exact StrategyQuant donor snippet class alias
TradeRecentlyClosed = trade_recently_closed

__all__ = [
    "TradeRecentlyClosed",
    "trade_recently_closed",
    "trade_recently_closed_spec",
]
