"""Set Profit Target strategy block.

Description:
    Sets or moves the profit target on matching orders/positions to a specified
    level, preserving any existing stop loss, matching StrategyQuant
    SetProfitTarget snippet logic.
Purpose:
    FEAT-ORDER-BLOCKS: StrategyQuant donor-faithful order execution blocks.
Key Capabilities:
    - FR-ORDER-SET-PROFIT-TARGET: Modify target price on matching positions.
Python API Usage:
    from app.extend.blocks.order.modify import set_profit_target
    results = await set_profit_target(runtime, scope, price=1.1250)
CLI Usage:
    uv run pytest tests/extend/blocks/test_order_blocks.py --no-cov
"""

from __future__ import annotations

from app.core.data.contracts import TradeResult
from app.core.host.logging import get_logger
from app.core.trading.blocks.runtime import TradingRuntime
from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.order._common import set_protection
from app.extend.functions.order_functions import TradeFilter

logger = get_logger(__name__)

set_profit_target_spec = BlockSpec(
    id="order.set_profit_target",
    name="Set Profit Target",
    description="Set an absolute target on matches, preserving each stop loss.",
    category="order",
    execution_kind=ExecutionKind.ORDER,
    inputs=(
        InputPort("context", PortType.ANY),
        InputPort("scope", PortType.ANY),
        InputPort("price", PortType.NUMBER),
    ),
    outputs=(OutputPort("result", PortType.ANY),),
    required_market_inputs=(),
    is_generation_eligible=False,
    is_deterministic=False,
    is_causal=True,
)


@block(set_profit_target_spec)
async def set_profit_target(
    context: TradingRuntime,
    scope: TradeFilter,
    price: float,
    *,
    include_pending: bool = True,
) -> list[TradeResult]:
    """Set an absolute target on matches, preserving each stop loss.

    Zero removes the target. Set include_pending=False for positions only.
    """
    async with context.trade.operation_lock:
        logger.debug(
            "FR-ORDER-SET-PROFIT-TARGET: PT price=%s scope=%s (pending=%s)",
            price,
            scope,
            include_pending,
        )
        return await set_protection(
            context, scope, tp=price, include_pending=include_pending
        )


__all__ = ["set_profit_target", "set_profit_target_spec"]
