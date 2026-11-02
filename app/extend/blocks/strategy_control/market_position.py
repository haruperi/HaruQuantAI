"""Market position strategy block.

Description:
    Returns the market position direction for the first matching open position:
    1 for long, -1 for short, or 0 if flat.
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-MARKET-POSITION: Active position direction detection.
Python API Usage:
    from app.extend.blocks.strategy_control.market_position import (
        MarketPosition,
        market_position,
    )
    pos = await market_position(context, scope)
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

market_position_spec = BlockSpec(
    id="strategy_control.market_position",
    name="Market Position",
    description="Return first matching direction: 1 long, -1 short, or 0 flat.",
    category="strategy_control",
    execution_kind=ExecutionKind.EXPRESSION,
    inputs=(InputPort("context", PortType.ANY), InputPort("scope", PortType.ANY)),
    outputs=(OutputPort("result", PortType.NUMBER),),
    required_market_inputs=(),
    is_generation_eligible=False,
    is_deterministic=False,
    is_causal=True,
)


@block(market_position_spec)
async def market_position(context: TradingRuntime, scope: TradeFilter) -> int:
    """Return first matching direction: 1 long, -1 short, or 0 flat.

    Args:
        context: Active trading runtime context.
        scope: Filter defining symbol, magic, ticket, or order name.

    Returns:
        1 for long, -1 for short, or 0 if flat.
    """
    logger.debug("FR-STRATEGY-CONTROL-MARKET-POSITION: Evaluating market position")
    positions = await matching_positions(context, scope)
    return (1 if positions[0].position_type == 0 else -1) if positions else 0


# Exact StrategyQuant donor snippet class alias
MarketPosition = market_position

__all__ = ["MarketPosition", "market_position", "market_position_spec"]
