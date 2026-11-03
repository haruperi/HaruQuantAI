"""Enter Reverse At Market strategy block.

Description:
    Opens a market order in the requested direction, first closing all matching
    opposite positions and verifying their complete closure, matching StrategyQuant
    EnterReverseAtMarket snippet logic.
Purpose:
    FEAT-ORDER-BLOCKS: StrategyQuant donor-faithful order execution blocks.
Key Capabilities:
    - FR-ORDER-ENTER-REVERSE-AT-MARKET: Reverse market position.
Python API Usage:
    from app.extend.blocks.order.open import enter_reverse_at_market
    result = await enter_reverse_at_market(runtime, "EURUSD", 1, 0.1)
CLI Usage:
    uv run pytest tests/extend/blocks/test_order_blocks.py --no-cov
"""

from __future__ import annotations

import math
from dataclasses import replace

from app.core.enums import OrderType, TradeRetcode
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
from app.core.trading.connection.contracts import (
    BridgeError,
    TradeRequest,
    TradeResult,
)
from app.extend.blocks.order._common import (
    close_positions,
    matching_positions,
)
from app.extend.functions.order_functions import TradeFilter

logger = get_logger(__name__)

enter_reverse_at_market_spec = BlockSpec(
    id="order.enter_reverse_at_market",
    name="Enter Reverse At Market",
    description="Close matching opposite positions, confirm closure, then enter.",
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


@block(enter_reverse_at_market_spec)
async def enter_reverse_at_market(
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
    """Close matching opposite positions, confirm closure, then enter.

    Direction is 1 for buy and -1 for sell; None means an entry was skipped.
    Size, stop loss, and target are evaluated values, not strategy formulas.
    """
    logger.debug(
        "FR-ORDER-ENTER-REVERSE-AT-MARKET: Reverse %s dir=%s vol=%s (sl=%s, tp=%s)",
        symbol,
        direction,
        volume,
        sl,
        tp,
    )
    async with context.trade.operation_lock:
        request = await context.trade.prepare_entry_request(
            symbol,
            direction,
            volume,
            OrderType.BUY,
            price=0.0,
            sl=sl,
            tp=tp,
            magic=magic,
            comment=comment,
            expiration=None,
        )
        scope = TradeFilter(symbol, magic=request.magic, comment=comment)
        if not allow_duplicate_trades and await matching_positions(
            context, replace(scope, direction=direction)
        ):
            logger.debug(
                "FR-ORDER-ENTER-REVERSE-AT-MARKET: Skip entry - duplicate disallowed"
            )
            return None
        return await _reverse_entry(
            context, request, scope, allow_duplicate_trades=allow_duplicate_trades
        )


async def _reverse_entry(
    context: TradingRuntime,
    request: TradeRequest,
    scope: TradeFilter,
    *,
    allow_duplicate_trades: bool,
) -> TradeResult | None:
    direction = 1 if request.order_type == OrderType.BUY else -1
    opposite_scope = replace(scope, direction=-direction)
    opposite_positions = await matching_positions(context, opposite_scope)
    logger.debug(
        "FR-ORDER-ENTER-REVERSE-AT-MARKET: Found %d opposite positions to close",
        len(opposite_positions),
    )
    results = await close_positions(context, opposite_positions)
    if results and results[-1].retcode != int(TradeRetcode.DONE):
        return results[-1]
    if await matching_positions(context, opposite_scope):
        raise BridgeError(
            "Opposite position closure is unconfirmed", code="OPERATION_UNCONFIRMED"
        )
    if not allow_duplicate_trades and await matching_positions(
        context, replace(scope, direction=direction)
    ):
        return None
    spec = await context.symbol.SymbolInfo(request.symbol)
    request.price = spec.price.ask if direction == 1 else spec.price.bid
    if not math.isfinite(request.price) or request.price <= 0:
        raise ValueError("reversal requires a positive market quote")
    return await context.trade.send_checked(request)


__all__ = ["enter_reverse_at_market", "enter_reverse_at_market_spec"]
