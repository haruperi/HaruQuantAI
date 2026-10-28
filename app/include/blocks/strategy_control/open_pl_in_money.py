"""Canonical open pl in money strategy block."""

from __future__ import annotations

from collections.abc import Mapping

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
from app.include.blocks.strategy_control._common import valuation


@block(
    BlockSpec(
        id="strategy_control.open_pl_in_money",
        name="Open Pl In Money",
        description=(
            "Sum net open P/L, optionally valuing at explicit strategy decision prices."
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
async def open_pl_in_money(
    context: TradingRuntime,
    scope: TradeFilter,
    *,
    prices: Mapping[str, float] | None = None,
) -> float:
    """Sum net open P/L, optionally valuing at explicit strategy decision prices.

    Supplied prices must cover every matched symbol. No position is mutated.
    """
    total = 0.0
    for position in await matching_positions(context, scope):
        gross = position.profit
        if prices is not None:
            gross = float(
                await context.account.OrderProfitCheck(
                    position.symbol,
                    position.position_type,
                    position.volume,
                    position.price_open,
                    valuation(position, prices),
                )
            )
        total += gross + position.swap + position.commission
    return total
