"""Backward-compatible class facades for BarTime and TimeConditions."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime
from typing import Any

import numpy as np

from app.host.logging import get_logger
from app.include.blocks.bar_time._common import (
    HHMM_PACKED_SEC_THRESHOLD,
    DateTime,
    _log_cond,
)
from app.include.contracts import DataframeSeries

__all__ = ["BarTime", "TimeConditions"]

logger = get_logger(__name__)


class BarTime:
    """Temporal feature extractor for bar and broker timestamps via DateTime."""

    def __init__(
        self,
        timestamps: DateTime | np.ndarray[Any, Any] | Sequence[Any],
        *,
        current_time_ms: int | None = None,
    ) -> None:
        """Initialize BarTime with DateTime series or timestamp array."""
        self._series = (
            timestamps if isinstance(timestamps, DateTime) else DateTime(timestamps)
        )
        self._current_time_ms = current_time_ms
        logger.debug("FR-LIBS-BAR-TIME-EXTRACT: Init BarTime (%d)", len(self._series))

    def __len__(self) -> int:
        """Return bar count."""
        return len(self._series)

    @property
    def series(self) -> DateTime:
        """Return underlying DateTime series."""
        return self._series

    @property
    def current_time_ms(self) -> int | None:
        """Return configured broker current time in epoch ms, or None."""
        return self._current_time_ms

    @current_time_ms.setter
    def current_time_ms(self, value: int | None) -> None:
        """Set broker current time in epoch ms."""
        self._current_time_ms = value

    def bar_ms(self, shift: int = 0) -> int:
        """Return epoch milliseconds at shift, or -1 if out of bounds."""
        ts = self._series.get_timestamp(shift)
        return ts * 1000 if ts != -1 else -1

    def _current_ms(self) -> int:
        """Return active current timestamp in epoch ms (broker clock or shift=0)."""
        return (
            self._current_time_ms
            if self._current_time_ms is not None
            else self.bar_ms(0)
        )

    def _extract(self, shift: int, fn: Callable[[int], int], name: str) -> int:
        """Extract bar component at shift via fn and log result."""
        ms = self.bar_ms(shift)
        val = fn(ms) if ms != -1 else -1
        logger.debug("FR-LIBS-BAR-TIME-EXTRACT: %s(%d) = %d", name, shift, val)
        return val

    def _curr(self, fn: Callable[[int], int]) -> int:
        """Extract active current component via fn."""
        ms = self._current_ms()
        return fn(ms) if ms != -1 else -1

    def _series_out(self, fn: Callable[[int], int], name: str) -> DataframeSeries:
        """Export shift-extracted bar series as DataframeSeries."""
        logger.info("FR-LIBS-BAR-TIME-EXTRACT: Exporting %s DataframeSeries", name)
        n = len(self._series)
        return DataframeSeries([fn(n - 1 - i) for i in range(n)], name)

    def get_dt(self, shift: int) -> datetime | None:
        """Retrieve datetime object at shift."""
        res = self._series.get_datetime(shift)
        return res if isinstance(res, datetime) else None

    def bar_hour(self, shift: int = 0) -> int:
        """Get hour of the bar (0-23) at shift."""
        return self._extract(shift, DateTime.get_hour, "bar_hour")

    def bar_minute(self, shift: int = 0) -> int:
        """Get minute of the bar (0-59) at shift."""
        return self._extract(shift, DateTime.get_minute, "bar_minute")

    def bar_day_of_week(self, shift: int = 0) -> int:
        """Get day of week (0=Sunday, 1=Monday ... 6=Saturday) at shift."""
        return self._extract(
            shift, DateTime.get_day_of_week_original, "bar_day_of_week"
        )

    def bar_day_of_month(self, shift: int = 0) -> int:
        """Get day of month (1-31) at shift."""
        return self._extract(shift, DateTime.get_day, "bar_day_of_month")

    def bar_month(self, shift: int = 0) -> int:
        """Get month of year (1-12) at shift."""
        return self._extract(shift, DateTime.get_month, "bar_month")

    def bar_date(self, shift: int = 0) -> int:
        """Get date as YYYYMMDD integer at shift."""
        return self._extract(shift, DateTime.get_ymd, "bar_date")

    def bar_time(self, shift: int = 0) -> int:
        """Get time as packed HHMM integer at shift."""
        return self._extract(shift, DateTime.get_hhmm, "bar_time")

    def bar_week_of_month(self, shift: int = 0) -> int:
        """Get Monday-aligned week of month (1-6) at shift."""
        return self._extract(shift, DateTime.get_week_of_month, "bar_week_of_month")

    def current_bar(self, shift: int = 0) -> int:
        """Get bar index / completed bar count."""
        n = len(self._series)
        val = (n - 1 - shift) if (0 <= shift < n) else -1
        logger.debug("FR-LIBS-BAR-TIME-EXTRACT: current_bar(%d) = %d", shift, val)
        return val

    def current_date(self) -> int:
        """Get current date as YYYYMMDD."""
        return self._curr(DateTime.get_ymd)

    def current_time(self) -> int:
        """Get current time as packed HHMM."""
        return self._curr(DateTime.get_hhmm)

    def current_hour(self) -> int:
        """Get current hour (0-23)."""
        return self._curr(DateTime.get_hour)

    def current_minute(self) -> int:
        """Get current minute (0-59)."""
        return self._curr(DateTime.get_minute)

    def current_day_of_week(self) -> int:
        """Get current day of week (0=Sunday ... 6=Saturday)."""
        return self._curr(DateTime.get_day_of_week_original)

    def current_month(self) -> int:
        """Get current month (1-12)."""
        return self._curr(DateTime.get_month)

    def current_week_of_month(self) -> int:
        """Get current Monday-aligned week of month (1-6)."""
        return self._curr(DateTime.get_week_of_month)

    def hour_series(self) -> DataframeSeries:
        """Export series of bar hours as DataframeSeries."""
        return self._series_out(self.bar_hour, "BarHour")

    def minute_series(self) -> DataframeSeries:
        """Export series of bar minutes as DataframeSeries."""
        return self._series_out(self.bar_minute, "BarMinute")

    def day_of_week_series(self) -> DataframeSeries:
        """Export series of bar day-of-week values as DataframeSeries."""
        return self._series_out(self.bar_day_of_week, "BarDayOfWeek")

    def month_series(self) -> DataframeSeries:
        """Export series of bar months as DataframeSeries."""
        return self._series_out(self.bar_month, "BarMonth")


class TimeConditions:
    """Temporal condition evaluator for rule engines."""

    def __init__(
        self,
        bar_time: BarTime | DateTime | np.ndarray[Any, Any] | Sequence[Any],
        *,
        is_bar_open: bool = True,
    ) -> None:
        """Initialize TimeConditions with BarTime, DateTime, or timestamps."""
        self._bt = bar_time if isinstance(bar_time, BarTime) else BarTime(bar_time)
        self._is_bar_open = is_bar_open
        logger.debug("FR-LIBS-TIME-CONDITIONS: Init (%d bars)", len(self._bt))

    @property
    def bar_time(self) -> BarTime:
        """Return underlying BarTime block."""
        return self._bt

    @staticmethod
    def always_true() -> bool:
        """Always returns True."""
        return _log_cond("always_true", 0, True)

    @staticmethod
    def always_false() -> bool:
        """Always returns False."""
        return _log_cond("always_false", 0, False)

    def is_bar_open(self, is_open: bool | None = None) -> bool:
        """Return True if evaluating at bar open event."""
        res = self._is_bar_open if is_open is None else is_open
        return _log_cond("is_bar_open", int(res), res)

    def bar_hour_is(self, hour: int, shift: int = 0) -> bool:
        """Check if bar hour at shift equals target hour."""
        return _log_cond("bar_hour_is", hour, self._bt.bar_hour(shift) == hour)

    def bar_hour_is_bigger(self, hour: int, shift: int = 0) -> bool:
        """Check if bar hour at shift is greater than target."""
        h = self._bt.bar_hour(shift)
        return _log_cond("bar_hour_is_bigger", hour, h > hour if h != -1 else False)

    def bar_hour_is_smaller(self, hour: int, shift: int = 0) -> bool:
        """Check if bar hour at shift is less than target."""
        h = self._bt.bar_hour(shift)
        return _log_cond("bar_hour_is_smaller", hour, h < hour if h != -1 else False)

    def bar_minute_is(self, minute: int, shift: int = 0) -> bool:
        """Check if bar minute at shift equals target minute."""
        return _log_cond("bar_minute_is", minute, self._bt.bar_minute(shift) == minute)

    def bar_day_of_week_is(self, day: int, shift: int = 0) -> bool:
        """Check if bar day of week (0=Sun..6=Sat; 7 accepted) equals target."""
        target = 0 if day == DateTime.SUNDAY else day
        return _log_cond(
            "bar_day_of_week_is", day, self._bt.bar_day_of_week(shift) == target
        )

    def bar_day_of_week_is_not(self, day: int, shift: int = 0) -> bool:
        """Check if bar day of week (0=Sun..6=Sat) does not equal target."""
        dow = self._bt.bar_day_of_week(shift)
        target = 0 if day == DateTime.SUNDAY else day
        return _log_cond(
            "bar_day_of_week_is_not", day, dow != target if dow != -1 else False
        )

    def bar_month_is(self, month: int, shift: int = 0) -> bool:
        """Check if bar month (1-12) equals target."""
        return _log_cond("bar_month_is", month, self._bt.bar_month(shift) == month)

    def bar_month_is_not(self, month: int, shift: int = 0) -> bool:
        """Check if bar month (1-12) does not equal target."""
        m = self._bt.bar_month(shift)
        return _log_cond("bar_month_is_not", month, m != month if m != -1 else False)

    def bar_time_is(
        self, hour_or_hhmm: int, minute: int | None = None, shift: int = 0
    ) -> bool:
        """Check if bar time matches (hour, minute) or packed HHMM / HHMMSS."""
        if minute is not None:
            res = (
                self._bt.bar_hour(shift) == hour_or_hhmm
                and self._bt.bar_minute(shift) == minute
            )
        else:
            bt = self._bt.bar_time(shift)
            target = (
                hour_or_hhmm // 100
                if hour_or_hhmm >= HHMM_PACKED_SEC_THRESHOLD
                else hour_or_hhmm
            )
            res = bt != -1 and bt == target
        return _log_cond("bar_time_is", hour_or_hhmm, res)

    def current_hour_is(self, hour: int) -> bool:
        """Check if current hour equals target."""
        return self._bt.current_hour() == hour

    def current_minute_is(self, minute: int) -> bool:
        """Check if current minute equals target."""
        return self._bt.current_minute() == minute

    def current_day_of_week_is(self, day: int) -> bool:
        """Check if current day of week (0=Sun..6=Sat; 7 accepted) equals target."""
        return self._bt.current_day_of_week() == (0 if day == DateTime.SUNDAY else day)

    def current_month_is(self, month: int) -> bool:
        """Check if current month equals target."""
        return self._bt.current_month() == month

    def current_time_is(self, hour_or_hhmm: int, minute: int | None = None) -> bool:
        """Check if current time matches (hour, minute) or packed HHMM / HHMMSS."""
        if minute is not None:
            return (
                self._bt.current_hour() == hour_or_hhmm
                and self._bt.current_minute() == minute
            )
        ct = self._bt.current_time()
        target = (
            hour_or_hhmm // 100
            if hour_or_hhmm >= HHMM_PACKED_SEC_THRESHOLD
            else hour_or_hhmm
        )
        return ct != -1 and ct == target

    def first_week_of_month(self, shift: int = 0) -> bool:
        """Check if bar falls within first Monday-aligned week of the month."""
        return _log_cond(
            "first_week_of_month", shift, self._bt.bar_week_of_month(shift) == 1
        )

    def last_week_of_month(self, shift: int = 0) -> bool:
        """Check if bar falls within the last Monday-aligned week of the month."""
        ms = self._bt.bar_ms(shift)
        if ms == -1:
            return False
        last_ms = DateTime.set_day_of_month(ms, DateTime.get_days_in_month(ms))
        res = DateTime.get_week_of_month(ms) == DateTime.get_week_of_month(last_ms)
        return _log_cond("last_week_of_month", shift, res)

    def is_month_first_trading_day(
        self, shift: int = 0, *, include_weekends: bool = False
    ) -> bool:
        """Check if bar falls on the first trading day of the month."""
        cur_ms = self._bt.bar_ms(shift)
        if cur_ms == -1:
            return False
        if not include_weekends and DateTime.get_day_of_week(cur_ms) in (
            DateTime.SATURDAY,
            DateTime.SUNDAY,
        ):
            return False
        cur_ym = (DateTime.get_year(cur_ms), DateTime.get_month(cur_ms))
        cur_day = DateTime.get_day(cur_ms)
        curr_idx = len(self._bt) - 1 - shift
        for prev_idx in range(curr_idx - 1, -1, -1):
            prev_ms = int(self._bt.series.timestamps[prev_idx]) * 1000
            if (DateTime.get_year(prev_ms), DateTime.get_month(prev_ms)) != cur_ym:
                continue
            if not include_weekends and DateTime.get_day_of_week(prev_ms) in (
                DateTime.SATURDAY,
                DateTime.SUNDAY,
            ):
                continue
            if DateTime.get_day(prev_ms) != cur_day:
                return False
        return True

    def is_month_last_trading_day(
        self, shift: int = 0, *, include_weekends: bool = False
    ) -> bool:
        """Check if bar falls on the last calendar trading day of the month."""
        ms = self._bt.bar_ms(shift)
        if ms == -1:
            return False
        last_date = DateTime.set_day_of_month(ms, DateTime.get_days_in_month(ms))
        if not include_weekends:
            dow = DateTime.get_day_of_week(last_date)
            if dow == DateTime.SATURDAY:
                last_date = DateTime.add_days(last_date, -1)
            elif dow == DateTime.SUNDAY:
                last_date = DateTime.add_days(last_date, -2)
        res = DateTime.get_day(ms) == DateTime.get_day(last_date)
        return _log_cond("is_month_last_trading_day", shift, res)
