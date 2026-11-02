"""Close Best Position strategy block.

Description:
    Closes the matching open position with the highest net profit (profit plus
    swap and commission), matching StrategyQuant CloseBestPosition snippet logic.
Purpose:
    FEAT-ORDER-BLOCKS: StrategyQuant donor-faithful order execution blocks.
Key Capabilities:
    - FR-ORDER-CLOSE-BEST: Identify and close most profitable matching position.
Python API Usage:
    from app.extend.blocks.order.close import close_best_position
    result = await close_best_position(runtime, scope)
CLI Usage:
    uv run pytest tests/extend/blocks/test_order_blocks.py --no-cov
"""

from __future__ import annotations

from app.core.data.contracts import TradeResult
from app.core.host.logging import get_logger
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
    net_profit,
)
from app.extend.blocks.order.runtime import TradingRuntime
from app.extend.blocks.order.types import TradeFilter

logger = get_logger(__name__)

close_best_position_spec = BlockSpec(
    id="order.close_best_position",
    name="Close Best Position",
    description="Close matching position with highest profit plus swap and commission.",
    category="order",
    execution_kind=ExecutionKind.ORDER,
    inputs=(InputPort("context", PortType.ANY), InputPort("scope", PortType.ANY)),
    outputs=(OutputPort("result", PortType.ANY),),
    required_market_inputs=(),
    is_generation_eligible=False,
    is_deterministic=False,
    is_causal=True,
)


@block(close_best_position_spec)
async def close_best_position(
    context: TradingRuntime, scope: TradeFilter
) -> TradeResult | None:
    """Close the matching position with highest profit plus swap and commission."""
    async with context.trade.operation_lock:
        positions = await matching_positions(context, scope)
        if not positions:
            logger.debug(
                "FR-ORDER-CLOSE-BEST: No matching positions found for scope=%s", scope
            )
            return None
        best = max(positions, key=net_profit)
        logger.debug(
            "FR-ORDER-CLOSE-BEST: Best position ticket=%s net=%s scope=%s",
            best.ticket,
            net_profit(best),
            scope,
        )
        return await context.trade.close(best)


__all__ = ["close_best_position", "close_best_position_spec"]
