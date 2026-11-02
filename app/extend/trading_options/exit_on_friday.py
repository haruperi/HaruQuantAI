"""Exit on Friday trading option snippet (TradingOptions cohort).

Description:
    Implements ExitOnFriday snippet matching StrategyQuant donor
    SQ/TradingOptions/ExitOnFriday.java.

Purpose:
    FEAT-CODE-EDITOR-EXTENSION-COHORTS: ExitOnFriday trading option.

Key Capabilities:
    - FR-trading-option-exit-on-friday: Close positions on Friday at cutoff time.

Python API Usage:
    from app.extend.trading_options.exit_on_friday import ExitOnFriday

    opt = ExitOnFriday(exit_time="20:00")
    should_exit = opt.should_exit(time_ms)

CLI Usage:
    python -m app.cli extend trading-options --option ExitOnFriday
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.extend.blocks.bar_time._common import DateTime
from app.extend.trading_options.base import BaseTradingOption, _parse_hhmm

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ExitOnFriday(BaseTradingOption):
    """Trigger position exit on Friday at configured cutoff time (ExitOnFriday.java)."""

    exit_time: int | str = 2000
    name: str = "ExitOnFriday"
    category: str = "TradingOptions"

    def should_exit(self, time_ms: int) -> bool:
        """Return True on Friday at or after exit_time."""
        dow = DateTime.get_day_of_week(time_ms)
        hhmm = DateTime.get_hhmm(time_ms)
        cutoff = _parse_hhmm(self.exit_time)
        triggered = dow == DateTime.FRIDAY and hhmm >= cutoff
        logger.debug("FR-trading-option-exit-on-friday: ExitOnFriday=%s", triggered)
        return triggered


__all__ = ["ExitOnFriday"]
