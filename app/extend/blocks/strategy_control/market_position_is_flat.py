"""Market position is flat strategy block.

Description:
    Returns True if no matching open market position exists (flat), or False
    if one or more matching positions are open.
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-MARKET-POSITION-IS-FLAT: Test for flat market state.
Python API Usage:
    from app.extend.blocks.strategy_control.market_position_is_flat import (
        MarketPositionIsFlat,
        market_position_is_flat,
    )
    is_flat = await market_position_is_flat(context, scope)
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

market_position_is_flat_spec = BlockSpec(
    id="strategy_control.market_position_is_flat",
    name="Market Position Is Flat",
    description="Return whether no matching market position exists.",
    category="strategy_control",
    execution_kind=ExecutionKind.CONDITION,
    inputs=(InputPort("context", PortType.ANY), InputPort("scope", PortType.ANY)),
    outputs=(OutputPort("result", PortType.BOOLEAN),),
    required_market_inputs=(),
    is_generation_eligible=False,
    is_deterministic=False,
    is_causal=True,
)


@block(market_position_is_flat_spec)
async def market_position_is_flat(context: TradingRuntime, scope: TradeFilter) -> bool:
    """Return whether no matching market position exists.

    Args:
        context: Active trading runtime context.
        scope: Filter defining symbol, magic, ticket, or order name.

    Returns:
        True if no matching position exists, False otherwise.
    """
    logger.debug("FR-STRATEGY-CONTROL-MARKET-POSITION-IS-FLAT: Evaluating is_flat")
    return not await matching_positions(context, scope)


# Exact StrategyQuant donor snippet class alias
MarketPositionIsFlat = market_position_is_flat

__all__ = [
    "MarketPositionIsFlat",
    "market_position_is_flat",
    "market_position_is_flat_spec",
]
