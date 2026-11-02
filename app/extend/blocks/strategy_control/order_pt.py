"""Order PT (profit target) strategy block.

Description:
    Returns the take-profit price of the first matching live position (or
    pending order), or -1.0 when absent.
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-ORDER-PT: Query profit target of matched order.
Python API Usage:
    from app.extend.blocks.strategy_control.order_pt import (
        OrderPT,
        order_pt,
    )
    pt = await order_pt(context, scope)
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

order_pt_spec = BlockSpec(
    id="strategy_control.order_pt",
    name="Order Pt",
    description="Return the first matching live profit target, or -1 when absent.",
    category="strategy_control",
    execution_kind=ExecutionKind.EXPRESSION,
    inputs=(InputPort("context", PortType.ANY), InputPort("scope", PortType.ANY)),
    outputs=(OutputPort("result", PortType.NUMBER),),
    required_market_inputs=(),
    is_generation_eligible=False,
    is_deterministic=False,
    is_causal=True,
)


@block(order_pt_spec)
async def order_pt(
    context: TradingRuntime, scope: TradeFilter, *, pending: bool | None = None
) -> float:
    """Return the first matching live profit target, or -1 when absent.

    Args:
        context: Active trading runtime context.
        scope: Filter defining symbol, magic, ticket, or order name.
        pending: True for pending orders only, False for positions only,
            None for either.

    Returns:
        First matching profit target price, or -1.0 if not found.
    """
    logger.debug(
        "FR-STRATEGY-CONTROL-ORDER-PT: Querying order_pt pending=%s",
        pending,
    )
    return await position_value(context, scope, "tp", pending=pending)


# Exact StrategyQuant donor snippet class alias
OrderPT = order_pt

__all__ = ["OrderPT", "order_pt", "order_pt_spec"]
