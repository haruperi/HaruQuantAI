"""Close All Pending Orders strategy block.

Description:
    Cancels all pending orders that match the specified trade filter criteria
    (symbol, direction, magic number, comment), matching the StrategyQuant
    CloseAllPendingOrders snippet logic.
Purpose:
    FEAT-ORDER-BLOCKS: StrategyQuant donor-faithful order execution blocks.
Key Capabilities:
    - FR-ORDER-CLOSE-ALL-PENDING: Cancel all matching pending orders under lock.
Python API Usage:
    from app.extend.blocks.order.close import close_all_pending_orders
    results = await close_all_pending_orders(runtime, scope)
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
from app.extend.blocks.order._common import (
    cancel_orders,
    matching_orders,
)
from app.extend.functions.order_functions import TradeFilter

logger = get_logger(__name__)

close_all_pending_orders_spec = BlockSpec(
    id="order.close_all_pending_orders",
    name="Close All Pending Orders",
    description="Cancel a snapshot of matching pending orders, stopping on a failure.",
    category="order",
    execution_kind=ExecutionKind.ORDER,
    inputs=(InputPort("context", PortType.ANY), InputPort("scope", PortType.ANY)),
    outputs=(OutputPort("result", PortType.ANY),),
    required_market_inputs=(),
    is_generation_eligible=False,
    is_deterministic=False,
    is_causal=True,
)


@block(close_all_pending_orders_spec)
async def close_all_pending_orders(
    context: TradingRuntime, scope: TradeFilter
) -> list[TradeResult]:
    """Cancel a snapshot of matching pending orders, stopping on a failure."""
    async with context.trade.operation_lock:
        orders = await matching_orders(context, scope)
        logger.debug(
            "FR-ORDER-CLOSE-ALL-PENDING: Canceling %d orders for scope=%s",
            len(orders),
            scope,
        )
        return await cancel_orders(context, orders)


__all__ = ["close_all_pending_orders", "close_all_pending_orders_spec"]
