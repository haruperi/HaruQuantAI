"""Set Stop Loss strategy block.

Description:
    Sets or moves the stop loss on matching orders/positions to a specified
    level, preserving any existing profit target, matching StrategyQuant
    SetStopLoss snippet logic.
Purpose:
    FEAT-ORDER-BLOCKS: StrategyQuant donor-faithful order execution blocks.
Key Capabilities:
    - FR-ORDER-SET-STOP-LOSS: Modify stop price with tightening guard.
Python API Usage:
    from app.extend.blocks.order.modify import set_stop_loss
    results = await set_stop_loss(runtime, scope, price=1.0950)
CLI Usage:
    uv run pytest tests/extend/blocks/test_order_blocks.py --no-cov
"""

from __future__ import annotations

from app.core.data.contracts import TradeResult
from app.core.host.logging import get_logger
from app.extend.blocks.base import block
from app.extend.blocks.metadata import (
    BlockSpec,
    ExecutionKind,
    InputPort,
    OutputPort,
    PortType,
)
from app.extend.blocks.order._common import set_protection
from app.extend.blocks.order.runtime import TradingRuntime
from app.extend.blocks.order.types import TradeFilter

logger = get_logger(__name__)

set_stop_loss_spec = BlockSpec(
    id="order.set_stop_loss",
    name="Set Stop Loss",
    description="Set an absolute stop price on matches, preserving each profit target.",
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


@block(set_stop_loss_spec)
async def set_stop_loss(
    context: TradingRuntime,
    scope: TradeFilter,
    price: float,
    *,
    include_pending: bool = True,
    tighten_only: bool = False,
) -> list[TradeResult]:
    """Set an absolute stop price on matches, preserving each profit target.

    Zero removes the stop unless tighten_only=True, which preserves tighter stops.
    Set include_pending=False for positions only.
    """
    async with context.trade.operation_lock:
        logger.debug(
            "FR-ORDER-SET-STOP-LOSS: SL price=%s scope=%s (tighten=%s)",
            price,
            scope,
            tighten_only,
        )
        return await set_protection(
            context,
            scope,
            sl=price,
            include_pending=include_pending,
            tighten_only=tighten_only,
        )


__all__ = ["set_stop_loss", "set_stop_loss_spec"]
