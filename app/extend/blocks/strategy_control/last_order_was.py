"""Last order was strategy block.

Description:
    Tests whether the last completed entry direction matches the expected
    direction (1 for long, -1 for short). Pending order cancellations are
    excluded.
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-LAST-ORDER-WAS: Test last completed trade entry direction.
Python API Usage:
    from app.extend.blocks.strategy_control.last_order_was import (
        LastOrderWas,
        last_order_was,
    )
    is_long = await last_order_was(context, scope, direction=1)
CLI Usage:
    uv run pytest tests/extend/blocks/test_strategy_control.py --no-cov
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

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
from app.extend.blocks.strategy_control.history import last_trade
from app.extend.functions.order_functions import (
    TradeFilter,
)

logger = get_logger(__name__)

last_order_was_spec = BlockSpec(
    id="strategy_control.last_order_was",
    name="Last Order Was",
    description=(
        "Test last completed entry direction; pending cancellations are excluded."
    ),
    category="strategy_control",
    execution_kind=ExecutionKind.CONDITION,
    inputs=(
        InputPort("context", PortType.ANY),
        InputPort("scope", PortType.ANY),
        InputPort("direction", PortType.NUMBER),
        InputPort("as_of", PortType.ANY, required=False, default=None),
    ),
    outputs=(OutputPort("result", PortType.BOOLEAN),),
    required_market_inputs=(),
    is_generation_eligible=False,
    is_deterministic=False,
    is_causal=True,
)


@block(last_order_was_spec)
async def last_order_was(
    context: TradingRuntime,
    scope: TradeFilter,
    direction: int,
    *,
    as_of: datetime | None = None,
) -> bool:
    """Test last completed entry direction; pending cancellations are excluded.

    Args:
        context: Active trading runtime context.
        scope: Filter defining symbol, magic, ticket, or order name.
        direction: Expected direction: 1 (long) or -1 (short).
        as_of: Optional cutoff timestamp.

    Returns:
        True if the last completed trade had the given direction, False otherwise.
    """
    logger.debug(
        "FR-STRATEGY-CONTROL-LAST-ORDER-WAS: last_order_was direction=%d",
        direction,
    )
    if type(direction) is not int or direction not in (-1, 1):
        raise ValueError("direction must be 1 or -1")
    trade = await last_trade(context, replace(scope, direction=0), 0, as_of)
    return trade is not None and trade.direction == direction


# Exact StrategyQuant donor snippet class alias
LastOrderWas = last_order_was

__all__ = ["LastOrderWas", "last_order_was", "last_order_was_spec"]
