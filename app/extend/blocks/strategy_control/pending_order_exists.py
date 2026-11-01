"""Canonical pending order exists strategy block."""

from __future__ import annotations

from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.order.runtime import TradingRuntime
from app.extend.blocks.order.types import (
    TradeFilter,
)


@block(
    BlockSpec(
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
)
async def pending_order_exists(context: TradingRuntime, scope: TradeFilter) -> bool:
    """Return whether any matching pending order exists."""
    return any(
        scope.matches(order)
        for order in await context.order.OrdersGet()
        if order.order_type in (2, 3, 4, 5, 6, 7)
    )
