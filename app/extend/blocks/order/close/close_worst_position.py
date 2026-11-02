"""Close Worst Position strategy block.

Description:
    Closes the matching open position with the lowest net profit (profit plus
    swap and commission), matching StrategyQuant CloseWorstPosition snippet logic.
Purpose:
    FEAT-ORDER-BLOCKS: StrategyQuant donor-faithful order execution blocks.
Key Capabilities:
    - FR-ORDER-CLOSE-WORST: Identify and close least profitable matching position.
Python API Usage:
    from app.extend.blocks.order.close import close_worst_position
    result = await close_worst_position(runtime, scope)
CLI Usage:
    uv run pytest tests/extend/blocks/test_order_blocks.py --no-cov
"""

from __future__ import annotations

from app.core.data.contracts import TradeResult
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
    net_profit,
)
from app.extend.functions.order_functions import TradeFilter

logger = get_logger(__name__)

close_worst_position_spec = BlockSpec(
    id="order.close_worst_position",
    name="Close Worst Position",
    description="Close matching position with lowest profit plus swap and commission.",
    category="order",
    execution_kind=ExecutionKind.ORDER,
    inputs=(InputPort("context", PortType.ANY), InputPort("scope", PortType.ANY)),
    outputs=(OutputPort("result", PortType.ANY),),
    required_market_inputs=(),
    is_generation_eligible=False,
    is_deterministic=False,
    is_causal=True,
)


@block(close_worst_position_spec)
async def close_worst_position(
    context: TradingRuntime, scope: TradeFilter
) -> TradeResult | None:
    """Close the matching position with lowest profit plus swap and commission."""
    async with context.trade.operation_lock:
        positions = await matching_positions(context, scope)
        if not positions:
            logger.debug(
                "FR-ORDER-CLOSE-WORST: No matching positions found for scope=%s", scope
            )
            return None
        worst = min(positions, key=net_profit)
        logger.debug(
            "FR-ORDER-CLOSE-WORST: Worst position ticket=%s net=%s scope=%s",
            worst.ticket,
            net_profit(worst),
            scope,
        )
        return await context.trade.close(worst)


__all__ = ["close_worst_position", "close_worst_position_spec"]
