"""Canonical enter at market strategy block."""

from __future__ import annotations

from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.order.open._common import execute_entry
from app.extend.blocks.order.runtime import TradingRuntime
from app.include.contracts import (
    TradeResult,
)
from app.include.enums import OrderType


@block(
    BlockSpec(
        id="order.enter_at_market",
        name="Enter At Market",
        description=(
            "Enter at the current quote unless a matching position already exists."
        ),
        category="order",
        execution_kind=ExecutionKind.ORDER,
        inputs=(
            InputPort("context", PortType.ANY),
            InputPort("symbol", PortType.STRING),
            InputPort("direction", PortType.NUMBER),
            InputPort("volume", PortType.NUMBER),
        ),
        outputs=(OutputPort("result", PortType.ANY),),
        required_market_inputs=(),
        is_generation_eligible=False,
        is_deterministic=False,
        is_causal=True,
    )
)
async def enter_at_market(
    context: TradingRuntime,
    symbol: str,
    direction: int,
    volume: float,
    *,
    sl: float = 0.0,
    tp: float = 0.0,
    magic: int | None = None,
    comment: str = "",
    allow_duplicate_trades: bool = False,
) -> TradeResult | None:
    """Enter at the current quote unless a matching position already exists.

    Direction is 1 for buy and -1 for sell; None means an entry was skipped.
    Size, stop loss, and target are evaluated values, not strategy formulas.
    """
    return await execute_entry(
        context,
        symbol,
        direction,
        volume,
        OrderType.BUY,
        sl=sl,
        tp=tp,
        magic=magic,
        comment=comment,
        allow_duplicate_trades=allow_duplicate_trades,
    )
