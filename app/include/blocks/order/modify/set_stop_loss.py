"""Canonical set stop loss strategy block."""

from __future__ import annotations

from app.include.blocks.base import block
from app.include.blocks.metadata import (
    BlockSpec,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.include.blocks.order._common import (
    set_protection,
)
from app.include.blocks.order.runtime import TradingRuntime
from app.include.blocks.order.types import (
    TradeFilter,
)
from app.include.contracts import (
    TradeResult,
)


@block(
    BlockSpec(
        id="order.set_stop_loss",
        name="Set Stop Loss",
        description=(
            "Set an absolute stop price on matches, preserving each profit target."
        ),
        category="order",
        execution_kind=ExecutionKind.ORDER,
        inputs=(
            InputPort("context", PortType.ANY),
            InputPort("scope", PortType.ANY),
            InputPort("price", PortType.NUMBER),
        ),
        outputs=(OutputPort("result", PortType.ANY),),
        required_market_inputs=(),
        is_generation_eligible=False,
        is_deterministic=False,
        is_causal=True,
    )
)
async def set_stop_loss(
    context: TradingRuntime,
    scope: TradeFilter,
    price: float,
    *,
    include_pending: bool = True,
    tighten_only: bool = False,
) -> list[TradeResult]:
    """Set an absolute stop price on matches, preserving each profit target.

    Zero removes the stop unless tighten_only=True, which preserves tighter stops.
    Set include_pending=False for positions only.
    """
    async with context.trade.operation_lock:
        return await set_protection(
            context,
            scope,
            sl=price,
            include_pending=include_pending,
            tighten_only=tighten_only,
        )
