"""Market position size strategy block.

Description:
    Sums matching open position volumes without netting opposing directions.
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-MARKET-POSITION-SIZE: Aggregate open position lot size.
Python API Usage:
    from app.extend.blocks.strategy_control.market_position_size import (
        MarketPositionSize,
        market_position_size,
    )
    size = await market_position_size(context, scope)
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

market_position_size_spec = BlockSpec(
    id="strategy_control.market_position_size",
    name="Market Position Size",
    description=("Sum matching position volumes without netting opposing directions."),
    category="strategy_control",
    execution_kind=ExecutionKind.EXPRESSION,
    inputs=(InputPort("context", PortType.ANY), InputPort("scope", PortType.ANY)),
    outputs=(OutputPort("result", PortType.NUMBER),),
    required_market_inputs=(),
    is_generation_eligible=False,
    is_deterministic=False,
    is_causal=True,
)


@block(market_position_size_spec)
async def market_position_size(context: TradingRuntime, scope: TradeFilter) -> float:
    """Sum matching position volumes without netting opposing directions.

    Args:
        context: Active trading runtime context.
        scope: Filter defining symbol, magic, ticket, or order name.

    Returns:
        Total volume of matching positions as float.
    """
    logger.debug("FR-STRATEGY-CONTROL-MARKET-POSITION-SIZE: Evaluating position size")
    positions = await matching_positions(context, scope)
    return float(sum(position.volume for position in positions))


# Exact StrategyQuant donor snippet class alias
MarketPositionSize = market_position_size

__all__ = [
    "MarketPositionSize",
    "market_position_size",
    "market_position_size_spec",
]
