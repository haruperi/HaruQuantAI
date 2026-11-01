"""Canonical closed pl in pips strategy block."""

from __future__ import annotations

from datetime import datetime

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
    pip_size,
)
from app.extend.blocks.strategy_control.history import last_trade


@block(
    BlockSpec(
        id="strategy_control.closed_pl_in_pips",
        name="Closed Pl In Pips",
        description=(
            "Return directional weighted price change in pips, or zero when absent."
        ),
        category="strategy_control",
        execution_kind=ExecutionKind.EXPRESSION,
        inputs=(
            InputPort("context", PortType.ANY),
            InputPort("scope", PortType.ANY),
            InputPort("as_of", PortType.ANY, required=False, default=None),
        ),
        outputs=(OutputPort("result", PortType.NUMBER),),
        required_market_inputs=(),
        is_generation_eligible=False,
        is_deterministic=False,
        is_causal=True,
    )
)
async def closed_pl_in_pips(
    context: TradingRuntime,
    scope: TradeFilter,
    *,
    trades_ago: int = 0,
    as_of: datetime | None = None,
) -> float:
    """Return directional weighted price change in pips, or zero when absent."""
    trade = await last_trade(context, scope, trades_ago, as_of)
    if trade is None:
        return 0.0
    spec = await context.symbol.SymbolInfo(trade.symbol)
    size = pip_size(spec.price.pip_size, spec.price.tick_size)
    return trade.direction * (trade.price_close - trade.price_open) / size
