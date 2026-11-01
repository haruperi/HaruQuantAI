"""Concrete donor-faithful TradingOptions session and order gate evaluators.

Description:
    Implements all 8 StrategyQuant TradingOptions snippet classes:
    DontTradeOnWeekends, ExitAtEndOfDay, ExitOnFriday, LimitTimeRange,
    MaxDistanceFromMarket, MaxTradesPerDay, MinMaxSLPT, and UseInitialSLPT.
Purpose:
    FEAT-CODE-EDITOR-EXTENSION-COHORTS: Complete the 8-class TradingOptions
    extension cohort under app/extend/trading_options.
Key Capabilities:
    - FR-trading-option-evaluate: Evaluate session entry/exit gates, weekend/Friday
      cutoffs, maximum trades per day, order distance bounds, and SL/PT clamping.
Python API Usage:
    from app.extend.trading_options.options import LimitTimeRange, MinMaxSLPT
CLI Usage:
    uv run pytest tests/workspace/code_editor/test_extension_cohorts.py
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.extend.blocks.bar_time._common import DateTime

logger = logging.getLogger(__name__)


def _parse_hhmm(time_val: int | str) -> int:
    """Convert HH:MM string or packed HHMM integer to packed HHMM (e.g. 1430)."""
    if isinstance(time_val, int):
        return time_val
    cleaned = time_val.strip()
    if ":" in cleaned:
        parts = cleaned.split(":")
        return int(parts[0]) * 100 + int(parts[1])
    return int(cleaned)


def _in_time_window(current_hhmm: int, start_hhmm: int, end_hhmm: int) -> bool:
    """Return whether current_hhmm falls within [start_hhmm, end_hhmm] (inclusive)."""
    if start_hhmm <= end_hhmm:
        return start_hhmm <= current_hhmm <= end_hhmm
    return current_hhmm >= start_hhmm or current_hhmm <= end_hhmm


class BaseTradingOption:
    """Base contract for runtime trading session and order options."""

    name: str = "BaseTradingOption"
    category: str = "TradingOptions"


@dataclass(frozen=True, slots=True)
class DontTradeOnWeekends(BaseTradingOption):
    """Block trading and optionally close positions across weekends."""

    friday_close_time: int | str = 2000
    sunday_open_time: int | str = 2200
    name: str = "DontTradeOnWeekends"

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
        logger.debug("FR-trading-option-evaluate: DontTradeOnWeekends=%s", allowed)
        return allowed


@dataclass(frozen=True, slots=True)
class ExitAtEndOfDay(BaseTradingOption):
    """Trigger position exit at configured end-of-day time (ExitAtEndOfDay.java)."""

    exit_time: int | str = 2300
    name: str = "ExitAtEndOfDay"

    def should_exit(self, time_ms: int) -> bool:
        """Return True when bar/tick time reaches or exceeds exit_time."""
        hhmm = DateTime.get_hhmm(time_ms)
        cutoff = _parse_hhmm(self.exit_time)
        triggered = hhmm >= cutoff
        logger.debug("FR-trading-option-evaluate: ExitAtEndOfDay=%s", triggered)
        return triggered


@dataclass(frozen=True, slots=True)
class ExitOnFriday(BaseTradingOption):
    """Trigger position exit on Friday at configured cutoff time (ExitOnFriday.java)."""

    exit_time: int | str = 2000
    name: str = "ExitOnFriday"

    def should_exit(self, time_ms: int) -> bool:
        """Return True on Friday at or after exit_time."""
        dow = DateTime.get_day_of_week(time_ms)
        hhmm = DateTime.get_hhmm(time_ms)
        cutoff = _parse_hhmm(self.exit_time)
        triggered = dow == DateTime.FRIDAY and hhmm >= cutoff
        logger.debug("FR-trading-option-evaluate: ExitOnFriday=%s", triggered)
        return triggered


@dataclass(frozen=True, slots=True)
class LimitTimeRange(BaseTradingOption):
    """Restrict order entry to a daily time window and optionally exit outside."""

    range_from: int | str = 800
    range_to: int | str = 1700
    exit_at_end_of_range: bool = False
    name: str = "LimitTimeRange"

    def is_entry_allowed(self, time_ms: int) -> bool:
        """Return True when timestamp is inside [range_from, range_to]."""
        hhmm = DateTime.get_hhmm(time_ms)
        allowed = _in_time_window(
            hhmm, _parse_hhmm(self.range_from), _parse_hhmm(self.range_to)
        )
        logger.debug("FR-trading-option-evaluate: LimitTimeRange=%s", allowed)
        return allowed

    def should_exit(self, time_ms: int) -> bool:
        """Return True when exit_at_end_of_range is enabled and outside window."""
        if not self.exit_at_end_of_range:
            return False
        return not self.is_entry_allowed(time_ms)


@dataclass(frozen=True, slots=True)
class MaxDistanceFromMarket(BaseTradingOption):
    """Reject pending orders placed too far from current market price."""

    max_distance_pct: float = 5.0
    name: str = "MaxDistanceFromMarket"

    def is_order_price_valid(self, *, market_price: float, order_price: float) -> bool:
        """Return True when price difference ratio <= max_distance_pct."""
        if market_price <= 0.0 or order_price <= 0.0:
            return False
        if self.max_distance_pct <= 0.0:
            return True
        dist_pct = abs(order_price - market_price) / market_price * 100.0
        valid = dist_pct <= self.max_distance_pct + 1e-9
        logger.debug("FR-trading-option-evaluate: MaxDistanceFromMarket=%s", valid)
        return valid


@dataclass(frozen=True, slots=True)
class MaxTradesPerDay(BaseTradingOption):
    """Enforce maximum opened trades per calendar day (MaxTradesPerDay.java)."""

    max_trades: int = 3
    name: str = "MaxTradesPerDay"

    def is_entry_allowed(self, trades_opened_today: int) -> bool:
        """Return True when trades_opened_today < max_trades (or max_trades <= 0)."""
        if self.max_trades <= 0:
            return True
        allowed = trades_opened_today < self.max_trades
        logger.debug("FR-trading-option-evaluate: MaxTradesPerDay=%s", allowed)
        return allowed


@dataclass(frozen=True, slots=True)
class MinMaxSLPT(BaseTradingOption):
    """Clamp stop-loss and profit-target pip distances to [min, max] bounds."""

    min_sl: float = 10.0
    max_sl: float = 200.0
    min_pt: float = 10.0
    max_pt: float = 300.0
    name: str = "MinMaxSLPT"

    def clamp_sl_pips(self, sl_pips: float) -> float:
        """Clamp stop-loss distance in pips to [min_sl, max_sl]."""
        if sl_pips <= 0.0:
            return 0.0
        val = max(sl_pips, self.min_sl) if self.min_sl > 0.0 else sl_pips
        if self.max_sl > 0.0:
            val = min(val, self.max_sl)
        logger.debug("FR-trading-option-evaluate: MinMaxSLPT.sl=%f", val)
        return val

    def clamp_pt_pips(self, pt_pips: float) -> float:
        """Clamp profit-target distance in pips to [min_pt, max_pt]."""
        if pt_pips <= 0.0:
            return 0.0
        val = max(pt_pips, self.min_pt) if self.min_pt > 0.0 else pt_pips
        if self.max_pt > 0.0:
            val = min(val, self.max_pt)
        logger.debug("FR-trading-option-evaluate: MinMaxSLPT.pt=%f", val)
        return val


@dataclass(frozen=True, slots=True)
class UseInitialSLPT(BaseTradingOption):
    """Enforce initial stop-loss and profit-target placement on order submission."""

    use_initial_sl_pt: bool = True
    name: str = "UseInitialSLPT"

    def should_attach_initial_brackets(self) -> bool:
        """Return whether SL/PT brackets are submitted with the initial entry order."""
        logger.debug(
            "FR-trading-option-evaluate: UseInitialSLPT=%s", self.use_initial_sl_pt
        )
        return self.use_initial_sl_pt


__all__ = [
    "BaseTradingOption",
    "DontTradeOnWeekends",
    "ExitAtEndOfDay",
    "ExitOnFriday",
    "LimitTimeRange",
    "MaxDistanceFromMarket",
    "MaxTradesPerDay",
    "MinMaxSLPT",
    "UseInitialSLPT",
]
