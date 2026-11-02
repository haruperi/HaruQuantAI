"""Order SL (stop loss) strategy block.

Description:
    Returns the stop-loss price of the first matching live position (or
    pending order), or -1.0 when absent.
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-ORDER-SL: Query stop loss of matched order.
Python API Usage:
    from app.extend.blocks.strategy_control.order_sl import (
        OrderSL,
        order_sl,
    )
    sl = await order_sl(context, scope)
CLI Usage:
    uv run pytest tests/extend/blocks/test_strategy_control.py --no-cov
"""

from __future__ import annotations

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
from app.extend.blocks.strategy_control._common import position_value
from app.extend.functions.order_functions import (
    TradeFilter,
)

logger = get_logger(__name__)

order_sl_spec = BlockSpec(
    id="strategy_control.order_sl",
    name="Order Sl",
    description="Return the first matching live stop loss, or -1 when absent.",
    category="strategy_control",
    execution_kind=ExecutionKind.EXPRESSION,
    inputs=(InputPort("context", PortType.ANY), InputPort("scope", PortType.ANY)),
    outputs=(OutputPort("result", PortType.NUMBER),),
    required_market_inputs=(),
    is_generation_eligible=False,
    is_deterministic=False,
    is_causal=True,
)


@block(order_sl_spec)
async def order_sl(
    context: TradingRuntime, scope: TradeFilter, *, pending: bool | None = None
) -> float:
    """Return the first matching live stop loss, or -1 when absent.

    Args:
        context: Active trading runtime context.
        scope: Filter defining symbol, magic, ticket, or order name.
        pending: True for pending orders only, False for positions only,
            None for either.

    Returns:
        First matching stop loss price, or -1.0 if not found.
    """
    logger.debug(
        "FR-STRATEGY-CONTROL-ORDER-SL: Querying order_sl pending=%s",
        pending,
    )
    return await position_value(context, scope, "sl", pending=pending)


# Exact StrategyQuant donor snippet class alias
OrderSL = order_sl

__all__ = ["OrderSL", "order_sl", "order_sl_spec"]
