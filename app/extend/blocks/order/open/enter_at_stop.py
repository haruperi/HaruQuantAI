"""Enter At Stop strategy block.

Description:
    Opens a stop order at a specified price level, optionally replacing
    existing pending orders of the same direction and symbol, matching StrategyQuant
    EnterAtStop snippet logic.
Purpose:
    FEAT-ORDER-BLOCKS: StrategyQuant donor-faithful order execution blocks.
Key Capabilities:
    - FR-ORDER-ENTER-AT-STOP: Place stop entry order with pending order replacement.
Python API Usage:
    from app.extend.blocks.order.open import enter_at_stop
    result = await enter_at_stop(runtime, "EURUSD", 1, 0.1, 1.1050)
CLI Usage:
    uv run pytest tests/extend/blocks/test_order_blocks.py --no-cov
"""

from __future__ import annotations

from datetime import datetime

from app.core.enums import OrderType
from app.core.host.logging import get_logger
from app.core.trading.blocks.base import block
from app.core.trading.blocks.metadata import (
    BlockSpec,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.core.trading.blocks.runtime import TradingRuntime
from app.core.trading.connection.contracts import TradeResult
from app.extend.blocks.order.open._common import execute_entry

logger = get_logger(__name__)

enter_at_stop_spec = BlockSpec(
    id="order.enter_at_stop",
    name="Enter At Stop",
    description="Place a stop entry, optionally replacing matching pending entries.",
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


@block(enter_at_stop_spec)
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
    logger.debug(
        "FR-ORDER-ENTER-AT-STOP: Stop %s dir=%s vol=%s px=%s (sl=%s, tp=%s)",
        symbol,
        direction,
        volume,
        price,
        sl,
        tp,
    )
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


__all__ = ["enter_at_stop", "enter_at_stop_spec"]
