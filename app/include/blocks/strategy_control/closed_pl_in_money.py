"""Canonical closed pl in money strategy block."""

from __future__ import annotations

from datetime import datetime

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
from app.include.blocks.strategy_control.history import last_trade


@block(
    BlockSpec(
        id="strategy_control.closed_pl_in_money",
        name="Closed Pl In Money",
        description=(
            "Return net P/L for the selected completed trade, or zero when absent."
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
async def closed_pl_in_money(
    context: TradingRuntime,
    scope: TradeFilter,
    *,
    trades_ago: int = 0,
    as_of: datetime | None = None,
) -> float:
    """Return net P/L for the selected completed trade, or zero when absent."""
    trade = await last_trade(context, scope, trades_ago, as_of)
    return trade.net_profit if trade is not None else 0.0
