"""Canonical enter at stop strategy block."""

from __future__ import annotations

from datetime import datetime

from app.core.data.contracts import (
    TradeResult,
)
from app.core.enums import OrderType
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


@block(
    BlockSpec(
        id="order.enter_at_stop",
        name="Enter At Stop",
        description=(
            "Place a stop entry, optionally replacing matching pending entries."
        ),
        category="order",
        execution_kind=ExecutionKind.ORDER,
        inputs=(
            InputPort("context", PortType.ANY),
            InputPort("symbol", PortType.STRING),
            InputPort("direction", PortType.NUMBER),
            InputPort("volume", PortType.NUMBER),
            InputPort("price", PortType.NUMBER),
            InputPort("expiration", PortType.ANY, required=False, default=None),
        ),
        outputs=(OutputPort("result", PortType.ANY),),
        required_market_inputs=(),
        is_generation_eligible=False,
        is_deterministic=False,
        is_causal=True,
    )
)
async def enter_at_stop(
    context: TradingRuntime,
    symbol: str,
    direction: int,
    volume: float,
    price: float,
    *,
    sl: float = 0.0,
    tp: float = 0.0,
    magic: int | None = None,
    comment: str = "",
    allow_duplicate_trades: bool = False,
    expiration: datetime | None = None,
    replace_existing: bool = True,
) -> TradeResult | None:
    """Place a stop entry, optionally replacing matching pending entries.

    Direction is 1 for buy and -1 for sell; None means an entry was skipped.
    Size, stop loss, and target are evaluated values, not strategy formulas.
    """
    return await execute_entry(
        context,
        symbol,
        direction,
        volume,
        OrderType.BUY_STOP,
        sl=sl,
        tp=tp,
        magic=magic,
        comment=comment,
        allow_duplicate_trades=allow_duplicate_trades,
        price=price,
        expiration=expiration,
        replace_existing=replace_existing,
    )
