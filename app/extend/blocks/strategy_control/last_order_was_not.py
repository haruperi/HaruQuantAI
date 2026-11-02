"""Last order was not strategy block.

Description:
    Tests whether the last completed entry direction does not match the
    specified direction (or returns False if no completed trade exists).
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-LAST-ORDER-WAS-NOT: Test opposite last completed direction.
Python API Usage:
    from app.extend.blocks.strategy_control.last_order_was_not import (
        LastOrderWasNot,
        last_order_was_not,
    )
    not_long = await last_order_was_not(context, scope, direction=1)
CLI Usage:
    uv run pytest tests/extend/blocks/test_strategy_control.py --no-cov
"""

from __future__ import annotations

from dataclasses import replace
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
)

logger = get_logger(__name__)

last_order_was_not_spec = BlockSpec(
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


@block(last_order_was_not_spec)
async def last_order_was_not(
    context: TradingRuntime,
    scope: TradeFilter,
    direction: int,
    *,
    as_of: datetime | None = None,
) -> bool:
    """Test opposite last entry direction; false when no completed trade exists.

    Args:
        context: Active trading runtime context.
        scope: Filter defining symbol, magic, ticket, or order name.
        direction: Direction to negate: 1 (long) or -1 (short).
        as_of: Optional cutoff timestamp.

    Returns:
        True if the last trade exists and its direction != direction, else False.
    """
    logger.debug(
        "FR-STRATEGY-CONTROL-LAST-ORDER-WAS-NOT: last_order_was_not direction=%d",
        direction,
    )
    if type(direction) is not int or direction not in (-1, 1):
        raise ValueError("direction must be 1 or -1")
    trade = await last_trade(context, replace(scope, direction=0), 0, as_of)
    return trade is not None and trade.direction != direction


# Exact StrategyQuant donor snippet class alias
LastOrderWasNot = last_order_was_not

__all__ = ["LastOrderWasNot", "last_order_was_not", "last_order_was_not_spec"]
