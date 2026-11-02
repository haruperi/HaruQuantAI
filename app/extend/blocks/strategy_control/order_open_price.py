"""Order open price strategy block.

Description:
    Returns the entry price of the first matching live position (or pending
    order), or -1.0 when absent.
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-ORDER-OPEN-PRICE: Query open price of matched order.
Python API Usage:
    from app.extend.blocks.strategy_control.order_open_price import (
        OrderOpenPrice,
        order_open_price,
    )
    price = await order_open_price(context, scope)
CLI Usage:
    uv run pytest tests/extend/blocks/test_strategy_control.py --no-cov
"""

from __future__ import annotations

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
from app.extend.blocks.strategy_control._common import position_value
from app.extend.functions.order_functions import (
    TradeFilter,
)

logger = get_logger(__name__)

order_open_price_spec = BlockSpec(
    id="strategy_control.order_open_price",
    name="Order Open Price",
    description="Return the first matching live entry price, or -1 when absent.",
    category="strategy_control",
    execution_kind=ExecutionKind.EXPRESSION,
    inputs=(InputPort("context", PortType.ANY), InputPort("scope", PortType.ANY)),
    outputs=(OutputPort("result", PortType.NUMBER),),
    required_market_inputs=(),
    is_generation_eligible=False,
    is_deterministic=False,
    is_causal=True,
)


@block(order_open_price_spec)
async def order_open_price(
    context: TradingRuntime, scope: TradeFilter, *, pending: bool | None = None
) -> float:
    """Return the first matching live entry price, or -1 when absent.

    Args:
        context: Active trading runtime context.
        scope: Filter defining symbol, magic, ticket, or order name.
        pending: True for pending orders only, False for positions only,
            None for either.

    Returns:
        First matching entry price, or -1.0 if not found.
    """
    logger.debug(
        "FR-STRATEGY-CONTROL-ORDER-OPEN-PRICE: Querying order_open_price pending=%s",
        pending,
    )
    return await position_value(context, scope, "price_open", pending=pending)


# Exact StrategyQuant donor snippet class alias
OrderOpenPrice = order_open_price

__all__ = [
    "OrderOpenPrice",
    "order_open_price",
    "order_open_price_spec",
]
