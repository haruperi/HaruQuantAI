"""Don't trade on weekends trading option snippet (TradingOptions cohort).

Description:
    Implements DontTradeOnWeekends snippet matching StrategyQuant donor
    SQ/TradingOptions/DontTradeOnWeekends.java.

Purpose:
    FEAT-CODE-EDITOR-EXTENSION-COHORTS: DontTradeOnWeekends trading option.

Key Capabilities:
    - FR-trading-option-dont-trade-on-weekends: Block trading during weekend blackout.

Python API Usage:
    from app.extend.trading_options.dont_trade_on_weekends import (
        DontTradeOnWeekends,
    )

    opt = DontTradeOnWeekends(friday_close_time="20:00", sunday_open_time="22:00")
    allowed = opt.is_trading_allowed(time_ms)

CLI Usage:
    python -m app.cli extend trading-options --option DontTradeOnWeekends
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.extend.blocks.bar_time._common import DateTime
from app.extend.trading_options.base import BaseTradingOption, _parse_hhmm

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DontTradeOnWeekends(BaseTradingOption):
    """Block trading and optionally close positions across weekends."""

    friday_close_time: int | str = 2000
    sunday_open_time: int | str = 2200
    name: str = "DontTradeOnWeekends"
    category: str = "TradingOptions"

    def is_trading_allowed(self, time_ms: int) -> bool:
        """Return False during the weekend blackout window."""
        dow = DateTime.get_day_of_week(time_ms)
        hhmm = DateTime.get_hhmm(time_ms)
        fri_cutoff = _parse_hhmm(self.friday_close_time)
        sun_open = _parse_hhmm(self.sunday_open_time)
        blackout = (
            dow == DateTime.SATURDAY
            or (dow == DateTime.FRIDAY and hhmm >= fri_cutoff)
            or (dow == DateTime.SUNDAY and hhmm < sun_open)
        )
        allowed = not blackout
        logger.debug(
            "FR-trading-option-dont-trade-on-weekends: DontTradeOnWeekends=%s",
            allowed,
        )
        return allowed


__all__ = ["DontTradeOnWeekends"]
