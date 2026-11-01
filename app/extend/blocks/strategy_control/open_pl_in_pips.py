"""Canonical open pl in pips strategy block."""

from __future__ import annotations

from collections.abc import Mapping

from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.order._common import (
    matching_positions,
)
from app.extend.blocks.order.runtime import TradingRuntime
from app.extend.blocks.order.types import (
    TradeFilter,
    pip_size,
)
from app.extend.blocks.strategy_control._common import valuation


@block(
    BlockSpec(
        id="strategy_control.open_pl_in_pips",
        name="Open Pl In Pips",
        description=(
            "Sum directional pip changes per position, without volume weighting."
        ),
        category="strategy_control",
        execution_kind=ExecutionKind.EXPRESSION,
        inputs=(
            InputPort("context", PortType.ANY),
            InputPort("scope", PortType.ANY),
            InputPort("prices", PortType.ANY, required=False, default=None),
        ),
        outputs=(OutputPort("result", PortType.NUMBER),),
        required_market_inputs=(),
        is_generation_eligible=False,
        is_deterministic=False,
        is_causal=True,
    )
)
async def open_pl_in_pips(
    context: TradingRuntime,
    scope: TradeFilter,
    *,
    prices: Mapping[str, float] | None = None,
) -> float:
    """Sum directional pip changes per position, without volume weighting."""
    total = 0.0
    for position in await matching_positions(context, scope):
        spec = await context.symbol.SymbolInfo(position.symbol)
        size = pip_size(spec.price.pip_size, spec.price.tick_size)
        direction = 1 if position.position_type == 0 else -1
        total += direction * (valuation(position, prices) - position.price_open) / size
    return total
