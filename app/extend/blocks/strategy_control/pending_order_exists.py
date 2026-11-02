"""Pending order exists strategy block.

Description:
    Returns True if any matching pending order exists in the trading runtime,
    or False otherwise.
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-PENDING-ORDER-EXISTS: Test presence of pending order.
Python API Usage:
    from app.extend.blocks.strategy_control.pending_order_exists import (
        PendingOrderExists,
        pending_order_exists,
    )
    exists = await pending_order_exists(context, scope)
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
from app.extend.functions.order_functions import (
    TradeFilter,
)

logger = get_logger(__name__)

pending_order_exists_spec = BlockSpec(
    id="strategy_control.pending_order_exists",
    name="Pending Order Exists",
    description="Return whether any matching pending order exists.",
    category="strategy_control",
    execution_kind=ExecutionKind.CONDITION,
    inputs=(InputPort("context", PortType.ANY), InputPort("scope", PortType.ANY)),
    outputs=(OutputPort("result", PortType.BOOLEAN),),
    required_market_inputs=(),
    is_generation_eligible=False,
    is_deterministic=False,
    is_causal=True,
)


@block(pending_order_exists_spec)
async def pending_order_exists(context: TradingRuntime, scope: TradeFilter) -> bool:
    """Return whether any matching pending order exists.

    Args:
        context: Active trading runtime context.
        scope: Filter defining symbol, magic, ticket, or order name.

    Returns:
        True if at least one matching pending order exists, False otherwise.
    """
    logger.debug("FR-STRATEGY-CONTROL-PENDING-ORDER-EXISTS: Querying pending orders")
    orders = await context.order.OrdersGet()
    return any(
        scope.matches(order)
        for order in orders
        if order.order_type in (2, 3, 4, 5, 6, 7)
    )


# Exact StrategyQuant donor snippet class alias
PendingOrderExists = pending_order_exists

__all__ = [
    "PendingOrderExists",
    "pending_order_exists",
    "pending_order_exists_spec",
]
