"""Canonical close position strategy block."""

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
    matching_positions,
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
        id="order.close_position",
        name="Close Position",
        description=(
            "Close the first matching position, fully or by an explicit volume."
        ),
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
)
async def close_position(
    context: TradingRuntime, scope: TradeFilter, *, volume: float | None = None
) -> TradeResult | None:
    """Close the first matching position, fully or by an explicit volume."""
    async with context.trade.operation_lock:
        positions = await matching_positions(context, scope)
        return await context.trade.close(positions[0], volume) if positions else None
