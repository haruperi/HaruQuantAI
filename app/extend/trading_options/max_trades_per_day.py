"""Max trades per day trading option snippet (TradingOptions cohort).

Description:
    Implements MaxTradesPerDay snippet matching StrategyQuant donor
    SQ/TradingOptions/MaxTradesPerDay.java.

Purpose:
    FEAT-CODE-EDITOR-EXTENSION-COHORTS: MaxTradesPerDay trading option.

Key Capabilities:
    - FR-trading-option-max-trades: Limit maximum opened trades per day.

Python API Usage:
    from app.extend.trading_options.max_trades_per_day import MaxTradesPerDay

    opt = MaxTradesPerDay(max_trades=3)
    allowed = opt.is_entry_allowed(trades_opened_today=2)

CLI Usage:
    python -m app.cli extend trading-options --option MaxTradesPerDay
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.extend.trading_options.base import BaseTradingOption

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class MaxTradesPerDay(BaseTradingOption):
    """Enforce maximum opened trades per calendar day (MaxTradesPerDay.java)."""

    max_trades: int = 3
    name: str = "MaxTradesPerDay"
    category: str = "TradingOptions"

    def is_entry_allowed(self, trades_opened_today: int) -> bool:
        """Return True when trades_opened_today < max_trades (or max_trades <= 0)."""
        if self.max_trades <= 0:
            return True
        allowed = trades_opened_today < self.max_trades
        logger.debug("FR-trading-option-max-trades: MaxTradesPerDay=%s", allowed)
        return allowed


__all__ = ["MaxTradesPerDay"]
