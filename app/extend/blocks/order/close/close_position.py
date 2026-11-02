"""Close Position strategy block.

Description:
    Closes the first matching open position, either fully or by an explicit volume,
    matching StrategyQuant ClosePosition snippet logic.
Purpose:
    FEAT-ORDER-BLOCKS: StrategyQuant donor-faithful order execution blocks.
Key Capabilities:
    - FR-ORDER-CLOSE-POSITION: Close matching position with volume specification.
Python API Usage:
    from app.extend.blocks.order.close import close_position
    result = await close_position(runtime, scope, volume=0.5)
CLI Usage:
    uv run pytest tests/extend/blocks/test_order_blocks.py --no-cov
"""

from __future__ import annotations

from app.core.data.contracts import TradeResult
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
from app.extend.blocks.order._common import matching_positions
from app.extend.functions.order_functions import TradeFilter

logger = get_logger(__name__)

close_position_spec = BlockSpec(
    id="order.close_position",
    name="Close Position",
    description="Close the first matching position, fully or by an explicit volume.",
    category="order",
    execution_kind=ExecutionKind.ORDER,
    inputs=(
        InputPort("context", PortType.ANY),
        InputPort("scope", PortType.ANY),
        InputPort("volume", PortType.NUMBER, required=False, default=None),
    ),
    outputs=(OutputPort("result", PortType.ANY),),
    required_market_inputs=(),
    is_generation_eligible=False,
    is_deterministic=False,
    is_causal=True,
)


@block(close_position_spec)
async def close_position(
    context: TradingRuntime, scope: TradeFilter, *, volume: float | None = None
) -> TradeResult | None:
    """Close the first matching position, fully or by an explicit volume."""
    async with context.trade.operation_lock:
        positions = await matching_positions(context, scope)
        if not positions:
            logger.debug(
                "FR-ORDER-CLOSE-POSITION: No matching positions found for scope=%s",
                scope,
            )
            return None
        target = positions[0]
        logger.debug(
            "FR-ORDER-CLOSE-POSITION: Close ticket=%s vol=%s scope=%s",
            target.ticket,
            volume,
            scope,
        )
        return await context.trade.close(target, volume)


__all__ = ["close_position", "close_position_spec"]
