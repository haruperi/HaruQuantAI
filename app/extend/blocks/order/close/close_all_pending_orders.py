"""Canonical close all pending orders strategy block."""

from __future__ import annotations

from app.core.data.contracts import (
    TradeResult,
)
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
from app.extend.blocks.order.runtime import TradingRuntime
from app.extend.blocks.order.types import (
    TradeFilter,
)


@block(
    BlockSpec(
        id="order.close_all_pending_orders",
        name="Close All Pending Orders",
        description=(
            "Cancel a snapshot of matching pending orders, stopping on a failure."
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
async def close_all_pending_orders(
    context: TradingRuntime, scope: TradeFilter
) -> list[TradeResult]:
    """Cancel a snapshot of matching pending orders, stopping on a failure."""
    async with context.trade.operation_lock:
        return await cancel_orders(context, await matching_orders(context, scope))
