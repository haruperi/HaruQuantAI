"""Canonical order sl strategy block."""

from __future__ import annotations

from app.include.blocks.base import block
from app.include.blocks.metadata import (
    BlockSpec,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.blocks.order.runtime import TradingRuntime
from app.include.blocks.order.types import (
    TradeFilter,
)
from app.include.blocks.strategy_control._common import position_value


@block(
    BlockSpec(
        id="strategy_control.order_sl",
        name="Order Sl",
        description="Return the first matching live stop loss, or -1 when absent.",
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
async def order_sl(
    context: TradingRuntime, scope: TradeFilter, *, pending: bool | None = None
) -> float:
    """Return the first matching live stop loss, or -1 when absent."""
    return await position_value(context, scope, "sl", pending=pending)
