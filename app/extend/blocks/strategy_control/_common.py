"""Shared valuation and live-order selection for state-query blocks."""

from __future__ import annotations

import math
from collections.abc import Mapping

from app.core.data import contracts
from app.extend.blocks.order._common import (
    matching_orders,
    matching_positions,
)
from app.extend.blocks.order.runtime import TradingRuntime
from app.extend.blocks.order.types import (
    TradeFilter,
)


def valuation(
    position: contracts.PositionInfo, prices: Mapping[str, float] | None
) -> float:
    value = position.price_current if prices is None else prices[position.symbol]
    if not math.isfinite(value) or value <= 0:
        raise ValueError("valuation prices must be finite and positive")
    return value


async def position_value(
    context: TradingRuntime,
    scope: TradeFilter,
    field: str,
    *,
    pending: bool | None = None,
) -> float:
    """Select positions first, then pending orders; allow an explicit view."""
    positions = await matching_positions(context, scope) if pending is not True else []
    orders = await matching_orders(context, scope) if pending is not False else []
    items = [*positions, *orders]
    return float(getattr(items[0], field)) if items else -1.0
