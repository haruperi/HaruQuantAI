"""Shared valuation and live-order selection for strategy control blocks.

Description:
    Provides internal helper utilities for valuation mark calculations and
    live position / pending order field retrieval across strategy control blocks.
Purpose:
    FEAT-STRATEGY-CONTROL-BLOCKS: StrategyQuant donor-faithful strategy control blocks.
Key Capabilities:
    - FR-STRATEGY-CONTROL-COMMON: Shared valuation and order-selection helpers.
Python API Usage:
    from app.extend.blocks.strategy_control._common import (
        position_value,
        valuation,
    )
    val = valuation(position, prices)
CLI Usage:
    uv run pytest tests/extend/blocks/test_strategy_control.py --no-cov
"""

from __future__ import annotations

import math
from collections.abc import Mapping

from app.core.host.logging import get_logger
from app.core.trading.blocks.runtime import TradingRuntime
from app.core.trading.connection.contracts import PositionInfo
from app.extend.blocks.order._common import (
    matching_orders,
    matching_positions,
)
from app.extend.functions.order_functions import (
    TradeFilter,
)

logger = get_logger(__name__)


def valuation(position: PositionInfo, prices: Mapping[str, float] | None) -> float:
    """Return effective mark valuation price for position.

    Args:
        position: Active position record.
        prices: Optional symbol-to-price mapping.

    Returns:
        Valuation price as float.
    """
    logger.debug(
        "FR-STRATEGY-CONTROL-COMMON: valuation for symbol=%s",
        position.symbol,
    )
    value = position.price_current if prices is None else prices[position.symbol]
    if not math.isfinite(value) or value <= 0:
        raise ValueError("valuation prices must be finite and positive")
    return float(value)


async def position_value(
    context: TradingRuntime,
    scope: TradeFilter,
    field: str,
    *,
    pending: bool | None = None,
) -> float:
    """Select positions first, then pending orders; allow an explicit view.

    Args:
        context: Active trading runtime context.
        scope: Filter defining symbol, magic, ticket, or order name.
        field: Name of attribute to read from the matching order/position.
        pending: True for pending orders only, False for positions only,
            None for either.

    Returns:
        Float value of specified attribute, or -1.0 if not found.
    """
    logger.debug(
        "FR-STRATEGY-CONTROL-COMMON: position_value field=%s pending=%s",
        field,
        pending,
    )
    positions = await matching_positions(context, scope) if pending is not True else []
    orders = await matching_orders(context, scope) if pending is not False else []
    items = [*positions, *orders]
    return float(getattr(items[0], field)) if items else -1.0


__all__ = ["position_value", "valuation"]
