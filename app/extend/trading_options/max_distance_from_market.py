"""Max distance from market trading option snippet (TradingOptions cohort).

Description:
    Implements MaxDistanceFromMarket snippet matching StrategyQuant donor
    SQ/TradingOptions/MaxDistanceFromMarket.java.

Purpose:
    FEAT-CODE-EDITOR-EXTENSION-COHORTS: MaxDistanceFromMarket trading option.

Key Capabilities:
    - FR-trading-option-max-distance: Reject orders placed too far from market.

Python API Usage:
    from app.extend.trading_options.max_distance_from_market import (
        MaxDistanceFromMarket,
    )

    opt = MaxDistanceFromMarket(max_distance_pct=5.0)
    valid = opt.is_order_price_valid(market_price=100.0, order_price=102.0)

CLI Usage:
    python -m app.cli extend trading-options --option MaxDistanceFromMarket
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.extend.trading_options.base import BaseTradingOption

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class MaxDistanceFromMarket(BaseTradingOption):
    """Reject pending orders placed too far from current market price."""

    max_distance_pct: float = 5.0
    name: str = "MaxDistanceFromMarket"
    category: str = "TradingOptions"

    def is_order_price_valid(self, *, market_price: float, order_price: float) -> bool:
        """Return True when price difference ratio <= max_distance_pct."""
        if market_price <= 0.0 or order_price <= 0.0:
            return False
        if self.max_distance_pct <= 0.0:
            return True
        dist_pct = abs(order_price - market_price) / market_price * 100.0
        valid = dist_pct <= self.max_distance_pct + 1e-9
        logger.debug("FR-trading-option-max-distance: MaxDistanceFromMarket=%s", valid)
        return valid


__all__ = ["MaxDistanceFromMarket"]
