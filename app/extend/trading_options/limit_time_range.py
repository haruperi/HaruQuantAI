"""Limit time range trading option snippet (TradingOptions cohort).

Description:
    Implements LimitTimeRange snippet matching StrategyQuant donor
    SQ/TradingOptions/LimitTimeRange.java.

Purpose:
    FEAT-CODE-EDITOR-EXTENSION-COHORTS: LimitTimeRange trading option.

Key Capabilities:
    - FR-trading-option-limit-time-range: Restrict entry signals to time window.

Python API Usage:
    from app.extend.trading_options.limit_time_range import LimitTimeRange

    opt = LimitTimeRange(range_from="08:00", range_to="16:00")
    allowed = opt.is_entry_allowed(time_ms)

CLI Usage:
    python -m app.cli extend trading-options --option LimitTimeRange
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.extend.blocks.bar_time._common import DateTime
from app.extend.trading_options.base import (
    BaseTradingOption,
    _in_time_window,
    _parse_hhmm,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class LimitTimeRange(BaseTradingOption):
    """Restrict order entry to a daily time window and optionally exit outside."""

    range_from: int | str = 800
    range_to: int | str = 1700
    exit_at_end_of_range: bool = False
    order_type_to_exit: int = 0
    name: str = "LimitTimeRange"
    category: str = "TradingOptions"

    def is_entry_allowed(self, time_ms: int) -> bool:
        """Return True when timestamp is inside [range_from, range_to]."""
        hhmm = DateTime.get_hhmm(time_ms)
        allowed = _in_time_window(
            hhmm, _parse_hhmm(self.range_from), _parse_hhmm(self.range_to)
        )
        logger.debug("FR-trading-option-limit-time-range: LimitTimeRange=%s", allowed)
        return allowed

    def should_exit(self, time_ms: int) -> bool:
        """Return True when exit_at_end_of_range is enabled and outside window."""
        if not self.exit_at_end_of_range:
            return False
        return not self.is_entry_allowed(time_ms)


__all__ = ["LimitTimeRange"]
