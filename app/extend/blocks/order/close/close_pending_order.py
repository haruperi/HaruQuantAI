"""Close Pending Order strategy block.

Description:
    Cancels the first matching pending order without touching open positions,
    matching StrategyQuant ClosePendingOrder snippet logic.
Purpose:
    FEAT-ORDER-BLOCKS: StrategyQuant donor-faithful order execution blocks.
Key Capabilities:
    - FR-ORDER-CLOSE-PENDING: Cancel first matching pending order under operation lock.
Python API Usage:
    from app.extend.blocks.order.close import close_pending_order
    result = await close_pending_order(runtime, scope)
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
from app.extend.blocks.order._common import matching_orders
from app.extend.functions.order_functions import TradeFilter

logger = get_logger(__name__)

close_pending_order_spec = BlockSpec(
    id="order.close_pending_order",
    name="Close Pending Order",
    description="Cancel the first matching pending order without touching positions.",
    category="order",
    execution_kind=ExecutionKind.ORDER,
    inputs=(InputPort("context", PortType.ANY), InputPort("scope", PortType.ANY)),
    outputs=(OutputPort("result", PortType.ANY),),
    required_market_inputs=(),
    is_generation_eligible=False,
    is_deterministic=False,
    is_causal=True,
)


@block(close_pending_order_spec)
async def close_pending_order(
    context: TradingRuntime, scope: TradeFilter
) -> TradeResult | None:
    """Cancel the first matching pending order without touching positions."""
    async with context.trade.operation_lock:
        orders = await matching_orders(context, scope)
        if not orders:
            logger.debug(
                "FR-ORDER-CLOSE-PENDING: No matching pending orders found for scope=%s",
                scope,
            )
            return None
        target = orders[0]
        logger.debug(
            "FR-ORDER-CLOSE-PENDING: Canceling pending order ticket=%s for scope=%s",
            target.ticket,
            scope,
        )
        return await context.trade.cancel(target)


__all__ = ["close_pending_order", "close_pending_order_spec"]
