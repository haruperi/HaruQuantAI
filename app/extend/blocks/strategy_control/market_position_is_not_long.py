"""Market position is not long strategy block.

Description:
    Returns True if no matching open market position is long, or False if at
    least one long position is currently open.
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-MARKET-POSITION-IS-NOT-LONG: Test absence of long positions.
Python API Usage:
    from app.extend.blocks.strategy_control.market_position_is_not_long import (
        MarketPositionIsNotLong,
        market_position_is_not_long,
    )
    not_long = await market_position_is_not_long(context, scope)
CLI Usage:
    uv run pytest tests/extend/blocks/test_strategy_control.py --no-cov
"""

from __future__ import annotations

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
from app.extend.blocks.strategy_control.market_position_is_long import (
    market_position_is_long,
)
from app.extend.functions.order_functions import (
    TradeFilter,
)

logger = get_logger(__name__)

market_position_is_not_long_spec = BlockSpec(
    id="strategy_control.market_position_is_not_long",
    name="Market Position Is Not Long",
    description="Return whether no matching long position exists.",
    category="strategy_control",
    execution_kind=ExecutionKind.CONDITION,
    inputs=(InputPort("context", PortType.ANY), InputPort("scope", PortType.ANY)),
    outputs=(OutputPort("result", PortType.BOOLEAN),),
    required_market_inputs=(),
    is_generation_eligible=False,
    is_deterministic=False,
    is_causal=True,
)


@block(market_position_is_not_long_spec)
async def market_position_is_not_long(
    context: TradingRuntime, scope: TradeFilter
) -> bool:
    """Return whether no matching long position exists.

    Args:
        context: Active trading runtime context.
        scope: Filter defining symbol, magic, ticket, or order name.

    Returns:
        True if no matching long position exists, False otherwise.
    """
    logger.debug(
        "FR-STRATEGY-CONTROL-MARKET-POSITION-IS-NOT-LONG: Evaluating is_not_long"
    )
    return not await market_position_is_long(context, scope)


# Exact StrategyQuant donor snippet class alias
MarketPositionIsNotLong = market_position_is_not_long

__all__ = [
    "MarketPositionIsNotLong",
    "market_position_is_not_long",
    "market_position_is_not_long_spec",
]
