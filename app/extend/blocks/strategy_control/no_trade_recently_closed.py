"""No trade recently closed strategy block.

Description:
    Returns the logical complement of the recent-completion predicate: True
    if no matching trade was closed recently (in the current bar or minute),
    False if one was.
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-NO-TRADE-RECENTLY-CLOSED: Inverted recent close detection.
Python API Usage:
    from app.extend.blocks.strategy_control.no_trade_recently_closed import (
        NoTradeRecentlyClosed,
        no_trade_recently_closed,
    )
    ok = await no_trade_recently_closed(context, scope, as_of=now)
CLI Usage:
    uv run pytest tests/extend/blocks/test_strategy_control.py --no-cov
"""

from __future__ import annotations

from datetime import datetime

from app.core.host.logging import get_logger
from app.core.trading.blocks.base import block
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.core.trading.blocks.runtime import TradingRuntime
from app.extend.blocks.strategy_control.trade_recently_closed import (
    trade_recently_closed,
)
from app.extend.functions.order_functions import (
    TradeFilter,
)

logger = get_logger(__name__)

no_trade_recently_closed_spec = BlockSpec(
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


@block(no_trade_recently_closed_spec)
async def no_trade_recently_closed(
    context: TradingRuntime,
    scope: TradeFilter,
    *,
    as_of: datetime,
    bar_start: datetime | None = None,
    check_this_bar: bool = True,
    check_this_minute: bool = True,
) -> bool:
    """Return the complement of the stable recent-completion predicate.

    Args:
        context: Active trading runtime context.
        scope: Filter defining symbol, magic, ticket, or order name.
        as_of: Current evaluation timestamp.
        bar_start: Optional open timestamp of the current bar.
        check_this_bar: If True, inspect within the current bar.
        check_this_minute: If True, inspect within the last 60 seconds.

    Returns:
        True if NO matching trade was recently closed, False otherwise.
    """
    logger.debug(
        "FR-STRATEGY-CONTROL-NO-TRADE-RECENTLY-CLOSED: Evaluating as_of=%s",
        as_of,
    )
    return not await trade_recently_closed(
        context,
        scope,
        as_of=as_of,
        bar_start=bar_start,
        check_this_bar=check_this_bar,
        check_this_minute=check_this_minute,
    )


# Exact StrategyQuant donor snippet class alias
NoTradeRecentlyClosed = no_trade_recently_closed

__all__ = [
    "NoTradeRecentlyClosed",
    "no_trade_recently_closed",
    "no_trade_recently_closed_spec",
]
