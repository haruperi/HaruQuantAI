"""Pending order does not exist strategy block.

Description:
    Returns True if no matching pending order exists in the trading runtime,
    or False if one or more matching pending orders exist.
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-PENDING-ORDER-DOESNT-EXIST: Test absence of pending orders.
Python API Usage:
    from app.extend.blocks.strategy_control.pending_order_doesnt_exist import (
        PendingOrderDoesntExist,
        pending_order_doesnt_exist,
    )
    absent = await pending_order_doesnt_exist(context, scope)
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
from app.extend.blocks.strategy_control.pending_order_exists import (
    pending_order_exists,
)
from app.extend.functions.order_functions import (
    TradeFilter,
)

logger = get_logger(__name__)

pending_order_doesnt_exist_spec = BlockSpec(
    id="strategy_control.pending_order_doesnt_exist",
    name="Pending Order Doesnt Exist",
    description="Return whether no matching pending order exists.",
    category="strategy_control",
    execution_kind=ExecutionKind.CONDITION,
    inputs=(InputPort("context", PortType.ANY), InputPort("scope", PortType.ANY)),
    outputs=(OutputPort("result", PortType.BOOLEAN),),
    required_market_inputs=(),
    is_generation_eligible=False,
    is_deterministic=False,
    is_causal=True,
)


@block(pending_order_doesnt_exist_spec)
async def pending_order_doesnt_exist(
    context: TradingRuntime, scope: TradeFilter
) -> bool:
    """Return whether no matching pending order exists.

    Args:
        context: Active trading runtime context.
        scope: Filter defining symbol, magic, ticket, or order name.

    Returns:
        True if no matching pending order exists, False otherwise.
    """
    logger.debug(
        "FR-STRATEGY-CONTROL-PENDING-ORDER-DOESNT-EXIST: Evaluating pending absence"
    )
    return not await pending_order_exists(context, scope)


# Exact StrategyQuant donor snippet class alias
PendingOrderDoesntExist = pending_order_doesnt_exist

__all__ = [
    "PendingOrderDoesntExist",
    "pending_order_doesnt_exist",
    "pending_order_doesnt_exist_spec",
]
