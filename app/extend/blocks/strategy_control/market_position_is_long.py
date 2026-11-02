"""Market position is long strategy block.

Description:
    Returns True if any matching open market position is long (including
    hedged accounts), or False otherwise.
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-MARKET-POSITION-IS-LONG: Test for long market position.
Python API Usage:
    from app.extend.blocks.strategy_control.market_position_is_long import (
        MarketPositionIsLong,
        market_position_is_long,
    )
    is_long = await market_position_is_long(context, scope)
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

market_position_is_long_spec = BlockSpec(
    id="strategy_control.market_position_is_long",
    name="Market Position Is Long",
    description=(
        "Return whether any matching position is long, including hedged accounts."
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


@block(market_position_is_long_spec)
async def market_position_is_long(context: TradingRuntime, scope: TradeFilter) -> bool:
    """Return whether any matching position is long, including hedged accounts.

    Args:
        context: Active trading runtime context.
        scope: Filter defining symbol, magic, ticket, or order name.

    Returns:
        True if any matching position is long, False otherwise.
    """
    logger.debug("FR-STRATEGY-CONTROL-MARKET-POSITION-IS-LONG: Evaluating is_long")
    positions = await matching_positions(context, scope)
    return any(position.position_type == 0 for position in positions)


# Exact StrategyQuant donor snippet class alias
MarketPositionIsLong = market_position_is_long

__all__ = [
    "MarketPositionIsLong",
    "market_position_is_long",
    "market_position_is_long_spec",
]
