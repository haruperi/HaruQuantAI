"""Deterministic order-flow and depth features."""

from __future__ import annotations

import math
from collections.abc import Mapping

from app.services.indicators.core.errors import (
    IndicatorError,
    IndicatorErrorCode,
    guard_public_boundary,
)
from app.utils import get_logger

logger = get_logger(__name__)


@guard_public_boundary
def measure_order_flow(
    *,
    bid_depth: float,
    ask_depth: float,
    previous_bid_depth: float,
    previous_ask_depth: float,
    aggressive_buy_volume: float,
    aggressive_sell_volume: float,
    sweep_threshold: float,
) -> Mapping[str, object]:
    """Measure bounded pressure, depth change, and sweep evidence.

    Args:
        bid_depth: Current executable bid depth.
        ask_depth: Current executable ask depth.
        previous_bid_depth: Previous executable bid depth.
        previous_ask_depth: Previous executable ask depth.
        aggressive_buy_volume: Supplied aggressive buy volume.
        aggressive_sell_volume: Supplied aggressive sell volume.
        sweep_threshold: Explicit minimum pressure magnitude for a sweep.

    Returns:
        Imbalance, pressure, depth changes, sweep side, and gap state.

    Raises:
        IndicatorError: If supplied values are non-finite or negative.
    """
    logger.info("Measuring deterministic order flow")
    values = (
        bid_depth,
        ask_depth,
        previous_bid_depth,
        previous_ask_depth,
        aggressive_buy_volume,
        aggressive_sell_volume,
        sweep_threshold,
    )
    if any(not math.isfinite(value) or value < 0.0 for value in values):
        raise IndicatorError(
            IndicatorErrorCode.IND_INVALID_PARAMETER,
            "order-flow values must be finite and non-negative",
        )
    depth_total = bid_depth + ask_depth
    flow_total = aggressive_buy_volume + aggressive_sell_volume
    imbalance = 0.0 if depth_total == 0.0 else (bid_depth - ask_depth) / depth_total
    pressure = (
        0.0
        if flow_total == 0.0
        else (aggressive_buy_volume - aggressive_sell_volume) / flow_total
    )
    sweep = "NONE"
    if pressure >= sweep_threshold:
        sweep = "BUY"
    elif pressure <= -sweep_threshold:
        sweep = "SELL"
    return {
        "imbalance": imbalance,
        "pressure": pressure,
        "bid_depth_change": bid_depth - previous_bid_depth,
        "ask_depth_change": ask_depth - previous_ask_depth,
        "sweep": sweep,
        "liquidity_gap": depth_total == 0.0,
    }


__all__ = ["measure_order_flow"]
