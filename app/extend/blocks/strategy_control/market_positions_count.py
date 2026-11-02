"""Market positions count strategy block.

Description:
    Counts matching open market positions, excluding pending orders.
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-MARKET-POSITIONS-COUNT: Count matching open positions.
Python API Usage:
    from app.extend.blocks.strategy_control.market_positions_count import (
        MarketPositionsCount,
        market_positions_count,
    )
    count = await market_positions_count(context, scope)
CLI Usage:
    uv run pytest tests/extend/blocks/test_strategy_control.py --no-cov
"""

from __future__ import annotations

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
from app.extend.blocks.order._common import (
    matching_positions,
)
from app.extend.functions.order_functions import (
    TradeFilter,
)

logger = get_logger(__name__)

market_positions_count_spec = BlockSpec(
    id="strategy_control.market_positions_count",
    name="Market Positions Count",
    description="Count matching market positions, excluding pending orders.",
    category="strategy_control",
    execution_kind=ExecutionKind.EXPRESSION,
    inputs=(InputPort("context", PortType.ANY), InputPort("scope", PortType.ANY)),
    outputs=(OutputPort("result", PortType.NUMBER),),
    required_market_inputs=(),
    is_generation_eligible=False,
    is_deterministic=False,
    is_causal=True,
)


@block(market_positions_count_spec)
async def market_positions_count(context: TradingRuntime, scope: TradeFilter) -> int:
    """Count matching market positions, excluding pending orders.

    Args:
        context: Active trading runtime context.
        scope: Filter defining symbol, magic, ticket, or order name.

    Returns:
        Integer count of matching open market positions.
    """
    logger.debug("FR-STRATEGY-CONTROL-MARKET-POSITIONS-COUNT: Counting positions")
    positions = await matching_positions(context, scope)
    return len(positions)


# Exact StrategyQuant donor snippet class alias
MarketPositionsCount = market_positions_count

__all__ = [
    "MarketPositionsCount",
    "market_positions_count",
    "market_positions_count_spec",
]
