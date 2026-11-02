"""Market position is short strategy block.

Description:
    Returns True if any matching open market position is short (including
    hedged accounts), or False otherwise.
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-MARKET-POSITION-IS-SHORT: Test for short market position.
Python API Usage:
    from app.extend.blocks.strategy_control.market_position_is_short import (
        MarketPositionIsShort,
        market_position_is_short,
    )
    is_short = await market_position_is_short(context, scope)
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
from app.extend.blocks.order._common import (
    matching_positions,
)
from app.extend.functions.order_functions import (
    TradeFilter,
)

logger = get_logger(__name__)

market_position_is_short_spec = BlockSpec(
    id="strategy_control.market_position_is_short",
    name="Market Position Is Short",
    description=(
        "Return whether any matching position is short, including hedged accounts."
    ),
    category="strategy_control",
    execution_kind=ExecutionKind.CONDITION,
    inputs=(InputPort("context", PortType.ANY), InputPort("scope", PortType.ANY)),
    outputs=(OutputPort("result", PortType.BOOLEAN),),
    required_market_inputs=(),
    is_generation_eligible=False,
    is_deterministic=False,
    is_causal=True,
)


@block(market_position_is_short_spec)
async def market_position_is_short(context: TradingRuntime, scope: TradeFilter) -> bool:
    """Return whether any matching position is short, including hedged accounts.

    Args:
        context: Active trading runtime context.
        scope: Filter defining symbol, magic, ticket, or order name.

    Returns:
        True if any matching position is short, False otherwise.
    """
    logger.debug("FR-STRATEGY-CONTROL-MARKET-POSITION-IS-SHORT: Evaluating is_short")
    positions = await matching_positions(context, scope)
    return any(position.position_type == 1 for position in positions)


# Exact StrategyQuant donor snippet class alias
MarketPositionIsShort = market_position_is_short

__all__ = [
    "MarketPositionIsShort",
    "market_position_is_short",
    "market_position_is_short_spec",
]
