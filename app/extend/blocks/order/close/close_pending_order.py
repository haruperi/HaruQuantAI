"""Canonical close pending order strategy block."""

from __future__ import annotations

from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.order._common import (
    matching_orders,
)
from app.extend.blocks.order.runtime import TradingRuntime
from app.extend.blocks.order.types import (
    TradeFilter,
)
from app.include.contracts import (
    TradeResult,
)


@block(
    BlockSpec(
        id="order.close_pending_order",
        name="Close Pending Order",
        description=(
            "Cancel the first matching pending order without touching positions."
        ),
        category="order",
        execution_kind=ExecutionKind.ORDER,
        inputs=(InputPort("context", PortType.ANY), InputPort("scope", PortType.ANY)),
        outputs=(OutputPort("result", PortType.ANY),),
        required_market_inputs=(),
        is_generation_eligible=False,
        is_deterministic=False,
        is_causal=True,
    )
)
async def close_pending_order(
    context: TradingRuntime, scope: TradeFilter
) -> TradeResult | None:
    """Cancel the first matching pending order without touching positions."""
    async with context.trade.operation_lock:
        orders = await matching_orders(context, scope)
        return await context.trade.cancel(orders[0]) if orders else None
