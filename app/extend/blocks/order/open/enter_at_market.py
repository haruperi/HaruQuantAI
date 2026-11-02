"""Enter At Market strategy block.

Description:
    Opens a market order at the current quote price, checking for duplicate trades
    when disallowed, matching StrategyQuant EnterAtMarket snippet logic.
Purpose:
    FEAT-ORDER-BLOCKS: StrategyQuant donor-faithful order execution blocks.
Key Capabilities:
    - FR-ORDER-ENTER-AT-MARKET: Place market order with duplicate checks.
Python API Usage:
    from app.extend.blocks.order.open import enter_at_market
    result = await enter_at_market(runtime, "EURUSD", 1, 0.1)
CLI Usage:
    uv run pytest tests/extend/blocks/test_order_blocks.py --no-cov
"""

from __future__ import annotations

from app.core.data.contracts import TradeResult
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
from app.extend.blocks.order.open._common import execute_entry

logger = get_logger(__name__)

enter_at_market_spec = BlockSpec(
    id="order.enter_at_market",
    name="Enter At Market",
    description="Enter at the current quote unless a matching position already exists.",
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


@block(enter_at_market_spec)
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
    logger.debug(
        "FR-ORDER-ENTER-AT-MARKET: Market %s dir=%s vol=%s (sl=%s, tp=%s)",
        symbol,
        direction,
        volume,
        sl,
        tp,
    )
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


__all__ = ["enter_at_market", "enter_at_market_spec"]
