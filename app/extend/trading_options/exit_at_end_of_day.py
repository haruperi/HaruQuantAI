"""Exit at end of day trading option snippet (TradingOptions cohort).

Description:
    Implements ExitAtEndOfDay snippet matching StrategyQuant donor
    SQ/TradingOptions/ExitAtEndOfDay.java.

Purpose:
    FEAT-CODE-EDITOR-EXTENSION-COHORTS: ExitAtEndOfDay trading option.

Key Capabilities:
    - FR-trading-option-exit-at-end-of-day: Close positions at configured EOD time.

Python API Usage:
    from app.extend.trading_options.exit_at_end_of_day import ExitAtEndOfDay

    opt = ExitAtEndOfDay(exit_time="23:00")
    should_exit = opt.should_exit(time_ms)

CLI Usage:
    python -m app.cli extend trading-options --option ExitAtEndOfDay
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.extend.blocks.bar_time._common import DateTime
from app.extend.trading_options.base import BaseTradingOption, _parse_hhmm

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ExitAtEndOfDay(BaseTradingOption):
    """Trigger position exit at configured end-of-day time (ExitAtEndOfDay.java)."""

    exit_time: int | str = 2300
    name: str = "ExitAtEndOfDay"
    category: str = "TradingOptions"

    def should_exit(self, time_ms: int) -> bool:
        """Return True when bar/tick time reaches or exceeds exit_time."""
        hhmm = DateTime.get_hhmm(time_ms)
        cutoff = _parse_hhmm(self.exit_time)
        triggered = hhmm >= cutoff
        logger.debug(
            "FR-trading-option-exit-at-end-of-day: ExitAtEndOfDay=%s", triggered
        )
        return triggered


__all__ = ["ExitAtEndOfDay"]
