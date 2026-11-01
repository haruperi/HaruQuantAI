"""Canonical order pt strategy block."""

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
from app.extend.blocks.strategy_control._common import position_value


@block(
    BlockSpec(
        id="strategy_control.order_pt",
        name="Order Pt",
        description="Return the first matching live profit target, or -1 when absent.",
        category="strategy_control",
        execution_kind=ExecutionKind.EXPRESSION,
        inputs=(InputPort("context", PortType.ANY), InputPort("scope", PortType.ANY)),
        outputs=(OutputPort("result", PortType.NUMBER),),
        required_market_inputs=(),
        is_generation_eligible=False,
        is_deterministic=False,
        is_causal=True,
    )
)
async def order_pt(
    context: TradingRuntime, scope: TradeFilter, *, pending: bool | None = None
) -> float:
    """Return the first matching live profit target, or -1 when absent."""
    return await position_value(context, scope, "tp", pending=pending)
