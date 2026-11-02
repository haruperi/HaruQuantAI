"""Market position is not short strategy block.

Description:
    Returns True if no matching open market position is short, or False if at
    least one short position is currently open.
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-MARKET-POSITION-IS-NOT-SHORT: Test absence of short positions.
Python API Usage:
    from app.extend.blocks.strategy_control.market_position_is_not_short import (
        MarketPositionIsNotShort,
        market_position_is_not_short,
    )
    not_short = await market_position_is_not_short(context, scope)
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
from app.extend.blocks.strategy_control.market_position_is_short import (
    market_position_is_short,
)
from app.extend.functions.order_functions import (
    TradeFilter,
)

logger = get_logger(__name__)

market_position_is_not_short_spec = BlockSpec(
    id="strategy_control.market_position_is_not_short",
    name="Market Position Is Not Short",
    description="Return whether no matching short position exists.",
    category="strategy_control",
    execution_kind=ExecutionKind.CONDITION,
    inputs=(InputPort("context", PortType.ANY), InputPort("scope", PortType.ANY)),
    outputs=(OutputPort("result", PortType.BOOLEAN),),
    required_market_inputs=(),
    is_generation_eligible=False,
    is_deterministic=False,
    is_causal=True,
)


@block(market_position_is_not_short_spec)
async def market_position_is_not_short(
    context: TradingRuntime, scope: TradeFilter
) -> bool:
    """Return whether no matching short position exists.

    Args:
        context: Active trading runtime context.
        scope: Filter defining symbol, magic, ticket, or order name.

    Returns:
        True if no matching short position exists, False otherwise.
    """
    logger.debug(
        "FR-STRATEGY-CONTROL-MARKET-POSITION-IS-NOT-SHORT: Evaluating is_not_short"
    )
    return not await market_position_is_short(context, scope)


# Exact StrategyQuant donor snippet class alias
MarketPositionIsNotShort = market_position_is_not_short

__all__ = [
    "MarketPositionIsNotShort",
    "market_position_is_not_short",
    "market_position_is_not_short_spec",
]
