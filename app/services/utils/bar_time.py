"""DateTimeSeries, BarTime component extractors, and TimeConditions predicates.

Description:
    Provides consolidated temporal building blocks matching StrategyQuant X:
    - DateTimeSeries: Shift-indexed POSIX timestamp series wrapper.
    - BarTime: 16 calendar and clock feature extractors (BarHour, BarMinute,
      BarDayOfWeek, BarDayOfMonth, BarMonth, BarDate, BarTime, BarWeekOfMonth,
      CurrentBar, CurrentDate, CurrentTime, etc.) and vectorized IndicatorSeries.
    - TimeConditions: 21 temporal condition predicates for rule engines
      (BarHourIs, BarHourIsBigger/Smaller, BarMinuteIs, BarDayOfWeekIs/IsNot,
      BarMonthIs/IsNot, BarTimeIs, First/LastWeekOfMonth, IsMonthFirst/LastTradingDay,
      IsBarOpen, AlwaysTrue/False).

Purpose:
    FEAT-SERVICES-BAR-TIME: Temporal feature extractors and rule condition predicates.

Key Capabilities:
    - FR-SERVICES-DATETIME-SERIES-STORAGE: Shift-indexed datetime series storage.
      Associated: `DateTimeSeries.get_timestamp()`, `DateTimeSeries.get_datetime()`.
      Logging: DEBUG on series initialization and point queries.
    - FR-SERVICES-BAR-TIME-EXTRACT: Calendar and clock component extraction.
      Associated: `BarTime.bar_hour()`, `BarTime.bar_minute()`,
      `BarTime.bar_day_of_week()`, `BarTime.bar_day_of_month()`,
      `BarTime.bar_month()`, `BarTime.bar_date()`, `BarTime.bar_time()`,
      `BarTime.bar_week_of_month()`, `BarTime.current_bar()`, and current-bar aliases.
      Logging: DEBUG on point evaluation, INFO on series export.
    - FR-SERVICES-TIME-CONDITIONS: Temporal rule predicates and calendar conditions.
      Associated: `TimeConditions.bar_hour_is()`,
      `TimeConditions.bar_day_of_week_is()`,
      `TimeConditions.is_month_first_trading_day()`, `TimeConditions.always_true()`.
      Logging: DEBUG on condition evaluations.
    - FR-SERVICES-FORMAT-TIMESTAMP: Format POSIX timestamps and datetimes
      into UTC or local offset strings.
      Associated: `format_timestamp()`.
      Logging: Passive string formatting; emits no operational log events.

Python API Usage:
    ```python
    from app.services.utils.bar_time import BarTime, DateTimeSeries, format_timestamp

    ts = [1704110400, 1704153600]
    bt = BarTime(ts)
    h = bt.bar_hour(shift=0)
    formatted = format_timestamp(ts[0], use_local_tz=True)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_time.py --no-cov
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

import numpy as np

from app.host.logging import get_logger
from app.services.indicators.base import IndicatorSeries

logger = get_logger(__name__)

DAYS_IN_WEEK: int = 7
TIME_DIVISOR_100: int = 100
LAST_WEEK_DAY_THRESHOLD: int = 25
HHMM_THRESHOLD: int = 10000
MS_THRESHOLD: int = 100_000_000_000


def normalize_timestamps(timestamps: Any) -> np.ndarray[Any, np.dtype[np.int64]]:
    """Convert sequence of timestamps to POSIX seconds."""
    if isinstance(timestamps, np.ndarray) and np.issubdtype(
        timestamps.dtype, np.integer
    ):
        arr = timestamps.astype(np.int64)
        if len(arr) > 0 and arr[0] > MS_THRESHOLD:
            return arr // 1000
        return arr

    res: list[int] = []
    for ts in timestamps:
        if isinstance(ts, (int, float, np.integer, np.floating)):
            sec = int(ts)
            if sec > MS_THRESHOLD:
                sec //= 1000
            res.append(sec)
        elif isinstance(ts, datetime):
            res.append(int(ts.replace(tzinfo=UTC).timestamp()))
        elif isinstance(ts, (str, np.str_)):
            dt = datetime.fromisoformat(str(ts))
            res.append(int(dt.timestamp()))
        else:
            dt_64 = np.datetime64(ts, "s").astype("int64")
            res.append(int(dt_64))
    return np.array(res, dtype=np.int64)


def _parse_timestamp(timestamp: float | datetime) -> datetime:
    """Normalize POSIX timestamp or datetime into UTC datetime."""
    if isinstance(timestamp, bool):
        raise TypeError("Unsupported timestamp type: bool")
    if isinstance(timestamp, (int, float)):
        sec = float(timestamp)
        if abs(sec) > MS_THRESHOLD:
            sec /= 1000.0
        return datetime.fromtimestamp(sec, tz=UTC)
    if isinstance(timestamp, datetime):
        dt = (
            timestamp if timestamp.tzinfo is not None else timestamp.replace(tzinfo=UTC)
        )
        return dt.astimezone(UTC)
    raise TypeError(f"Unsupported timestamp type: {type(timestamp).__name__}")


def format_timestamp(
    timestamp: float | datetime | None,
    *,
    fmt: str = "%Y-%m-%d %H:%M:%S.%f",
    include_tz: bool = True,
    use_local_tz: bool = False,
    precision: int | None = 3,
) -> str:
    """Format a POSIX timestamp or datetime into a standardized string.

    Args:
        timestamp: POSIX seconds or milliseconds (float/int), datetime, or None.
        fmt: strftime format string (default "%Y-%m-%d %H:%M:%S.%f") or 'iso'.
        include_tz: Whether to append timezone suffix or offset (default True).
        use_local_tz: Whether to convert time to current local timezone and display
            its offset rather than UTC (default False).
        precision: Fractional second precision (default 3 for milliseconds).
            Pass None to keep all 6 digits of %f.

    Returns:
        Formatted timestamp string, or 'N/A' if timestamp is None.

    Raises:
        TypeError: If timestamp is not a float, int, datetime, or None.
    """
    if timestamp is None:
        return "N/A"

    dt = _parse_timestamp(timestamp)
    if use_local_tz:
        dt = dt.astimezone()

    if fmt.lower() == "iso":
        return dt.isoformat() if include_tz else dt.replace(tzinfo=None).isoformat()

    if precision is not None and ".%f" in fmt:
        micro = dt.strftime("%f")
        frac = micro[:precision] if precision > 0 else ""
        base = dt.strftime(fmt.replace(".%f", ""))
        formatted = f"{base}.{frac}" if frac else base
    else:
        formatted = dt.strftime(fmt)

    if not include_tz:
        return formatted

    suffix = dt.strftime("%:z") if use_local_tz else "UTC"
    return f"{formatted} {suffix}"


class DateTimeSeries:
    """Historical timestamp series wrapper with shift-based indexing."""

    def __init__(
        self,
        timestamps: np.ndarray[Any, Any] | Sequence[Any],
        name: str = "DateTime",
    ) -> None:
        """Initialize DateTimeSeries with timestamps.

        Args:
            timestamps: Array or sequence of timestamps, datetimes, or ISO strings.
            name: Optional descriptive series name.

        Raises:
            ValueError: If timestamps sequence is empty.
        """
        self._timestamps: np.ndarray[Any, np.dtype[np.int64]] = normalize_timestamps(
            timestamps
        )
        if len(self._timestamps) == 0:
            raise ValueError("DateTimeSeries timestamps array cannot be empty.")

        self._name = name
        logger.debug(
            "FR-SERVICES-DATETIME-SERIES-STORAGE: Init DateTimeSeries '%s' (%d bars)",
            self._name,
            len(self._timestamps),
        )

    @property
    def name(self) -> str:
        """Return series identifier."""
        return self._name

    @property
    def timestamps(self) -> np.ndarray[Any, np.dtype[np.int64]]:
        """Return underlying POSIX timestamp array in seconds."""
        return self._timestamps

    def __len__(self) -> int:
        """Return total bar count."""
        return len(self._timestamps)

    def get_timestamp(self, shift: int = 0) -> int:
        """Get POSIX timestamp in seconds at historical shift.

        Args:
            shift: Historical offset where 0 is newest bar, 1 is 1 bar ago.

        Returns:
            Integer POSIX seconds, or -1 if shift out of bounds.
        """
        if shift < 0 or shift >= len(self._timestamps):
            logger.debug(
                "FR-SERVICES-DATETIME-SERIES-STORAGE: Shift %d out of bounds (len=%d)",
                shift,
                len(self._timestamps),
            )
            return -1
        return int(self._timestamps[-(1 + shift)])

    def get_datetime(self, shift: int = 0) -> datetime | None:
        """Get UTC datetime object at historical shift.

        Args:
            shift: Historical offset where 0 is newest bar.

        Returns:
            UTC datetime object or None if out of bounds.
        """
        ts = self.get_timestamp(shift)
        if ts == -1:
            return None
        return datetime.fromtimestamp(ts, tz=UTC)


class BarTime:
    """Temporal feature extractor for bar timestamps."""

    def __init__(
        self,
        timestamps: DateTimeSeries | np.ndarray[Any, Any] | Sequence[Any],
    ) -> None:
        """Initialize BarTime with DateTimeSeries or timestamp array.

        Args:
            timestamps: DateTimeSeries or raw timestamp sequence.
        """
        if isinstance(timestamps, DateTimeSeries):
            self._series = timestamps
        else:
            self._series = DateTimeSeries(timestamps)

        logger.debug(
            "FR-SERVICES-BAR-TIME-EXTRACT: Initialized BarTime with %d bars",
            len(self._series),
        )

    def __len__(self) -> int:
        """Return bar count."""
        return len(self._series)

    @property
    def series(self) -> DateTimeSeries:
        """Return underlying DateTimeSeries."""
        return self._series

    def get_dt(self, shift: int) -> datetime | None:
        """Retrieve datetime object at shift."""
        return self._series.get_datetime(shift)

    # --- Shift-Indexed Temporal Extractors ---

    def bar_hour(self, shift: int = 0) -> int:
        """Get hour of the bar (0-23) at shift (BarHour)."""
        dt = self.get_dt(shift)
        val = dt.hour if dt is not None else -1
        logger.debug(
            "FR-SERVICES-BAR-TIME-EXTRACT: bar_hour(shift=%d) = %d", shift, val
        )
        return val

    def bar_minute(self, shift: int = 0) -> int:
        """Get minute of the bar (0-59) at shift (BarMinute)."""
        dt = self.get_dt(shift)
        val = dt.minute if dt is not None else -1
        logger.debug(
            "FR-SERVICES-BAR-TIME-EXTRACT: bar_minute(shift=%d) = %d", shift, val
        )
        return val

    def bar_day_of_week(self, shift: int = 0) -> int:
        """Get day of week (1=Monday ... 7=Sunday) at shift (BarDayOfWeek)."""
        dt = self.get_dt(shift)
        val = dt.isoweekday() if dt is not None else -1
        logger.debug(
            "FR-SERVICES-BAR-TIME-EXTRACT: bar_day_of_week(shift=%d) = %d",
            shift,
            val,
        )
        return val

    def bar_day_of_month(self, shift: int = 0) -> int:
        """Get day of month (1-31) at shift (BarDayOfMonth)."""
        dt = self.get_dt(shift)
        val = dt.day if dt is not None else -1
        logger.debug(
            "FR-SERVICES-BAR-TIME-EXTRACT: bar_day_of_month(shift=%d) = %d",
            shift,
            val,
        )
        return val

    def bar_month(self, shift: int = 0) -> int:
        """Get month of year (1-12) at shift (BarMonth)."""
        dt = self.get_dt(shift)
        val = dt.month if dt is not None else -1
        logger.debug(
            "FR-SERVICES-BAR-TIME-EXTRACT: bar_month(shift=%d) = %d", shift, val
        )
        return val

    def bar_date(self, shift: int = 0) -> int:
        """Get date as YYYYMMDD integer at shift (BarDate)."""
        dt = self.get_dt(shift)
        val = (dt.year * 10000 + dt.month * 100 + dt.day) if dt is not None else -1
        logger.debug(
            "FR-SERVICES-BAR-TIME-EXTRACT: bar_date(shift=%d) = %d", shift, val
        )
        return val

    def bar_time(self, shift: int = 0) -> int:
        """Get time as HHMMSS integer at shift (BarTime)."""
        dt = self.get_dt(shift)
        val = (dt.hour * 10000 + dt.minute * 100 + dt.second) if dt is not None else -1
        logger.debug(
            "FR-SERVICES-BAR-TIME-EXTRACT: bar_time(shift=%d) = %d", shift, val
        )
        return val

    def bar_week_of_month(self, shift: int = 0) -> int:
        """Get week of month (1-5) at shift (BarWeekOfMonth)."""
        dt = self.get_dt(shift)
        val = ((dt.day - 1) // DAYS_IN_WEEK + 1) if dt is not None else -1
        logger.debug(
            "FR-SERVICES-BAR-TIME-EXTRACT: bar_week_of_month(shift=%d) = %d",
            shift,
            val,
        )
        return val

    def current_bar(self, shift: int = 0) -> int:
        """Get bar index / completed bar count (CurrentBar)."""
        n = len(self._series)
        val = (n - 1 - shift) if (0 <= shift < n) else -1
        logger.debug(
            "FR-SERVICES-BAR-TIME-EXTRACT: current_bar(shift=%d) = %d", shift, val
        )
        return val

    # --- Current Bar Convenience Aliases (shift=0) ---

    def current_date(self) -> int:
        """Get CurrentDate (bar_date at shift=0)."""
        return self.bar_date(shift=0)

    def current_time(self) -> int:
        """Get CurrentTime (bar_time at shift=0)."""
        return self.bar_time(shift=0)

    def current_hour(self) -> int:
        """Get CurrentHour (bar_hour at shift=0)."""
        return self.bar_hour(shift=0)

    def current_minute(self) -> int:
        """Get CurrentMinute (bar_minute at shift=0)."""
        return self.bar_minute(shift=0)

    def current_day_of_week(self) -> int:
        """Get CurrentDayOfWeek (bar_day_of_week at shift=0)."""
        return self.bar_day_of_week(shift=0)

    def current_month(self) -> int:
        """Get CurrentMonth (bar_month at shift=0)."""
        return self.bar_month(shift=0)

    def current_week_of_month(self) -> int:
        """Get CurrentWeekOfMonth (bar_week_of_month at shift=0)."""
        return self.bar_week_of_month(shift=0)

    # --- Vectorized IndicatorSeries Generation ---

    def hour_series(self) -> IndicatorSeries:
        """Export series of bar hours as IndicatorSeries."""
        logger.info("FR-SERVICES-BAR-TIME-EXTRACT: Exporting hour IndicatorSeries")
        n = len(self._series)
        hours = [self.bar_hour(n - 1 - i) for i in range(n)]
        return IndicatorSeries(hours, name="BarHour")

    def minute_series(self) -> IndicatorSeries:
        """Export series of bar minutes as IndicatorSeries."""
        logger.info("FR-SERVICES-BAR-TIME-EXTRACT: Exporting minute IndicatorSeries")
        n = len(self._series)
        mins = [self.bar_minute(n - 1 - i) for i in range(n)]
        return IndicatorSeries(mins, name="BarMinute")

    def day_of_week_series(self) -> IndicatorSeries:
        """Export series of bar day-of-week values as IndicatorSeries."""
        logger.info("FR-SERVICES-BAR-TIME-EXTRACT: Exporting day-of-week series")
        n = len(self._series)
        dows = [self.bar_day_of_week(n - 1 - i) for i in range(n)]
        return IndicatorSeries(dows, name="BarDayOfWeek")

    def month_series(self) -> IndicatorSeries:
        """Export series of bar months as IndicatorSeries."""
        logger.info("FR-SERVICES-BAR-TIME-EXTRACT: Exporting month series")
        n = len(self._series)
        months = [self.bar_month(n - 1 - i) for i in range(n)]
        return IndicatorSeries(months, name="BarMonth")


class TimeConditions:
    """Temporal condition evaluator matching SQX BarAndTime condition blocks."""

    def __init__(
        self,
        bar_time: BarTime | DateTimeSeries | np.ndarray[Any, Any] | Sequence[Any],
    ) -> None:
        """Initialize TimeConditions with BarTime or timestamps.

        Args:
            bar_time: BarTime instance, DateTimeSeries, or raw timestamp array.
        """
        if isinstance(bar_time, BarTime):
            self._bt = bar_time
        elif isinstance(bar_time, DateTimeSeries):
            self._bt = BarTime(bar_time)
        else:
            self._bt = BarTime(DateTimeSeries(bar_time))

        logger.debug(
            "FR-SERVICES-TIME-CONDITIONS: Init TimeConditions (%d bars)",
            len(self._bt),
        )

    @property
    def bar_time(self) -> BarTime:
        """Return underlying BarTime block."""
        return self._bt

    @staticmethod
    def always_true() -> bool:
        """Always returns True (AlwaysTrue)."""
        logger.debug("FR-SERVICES-TIME-CONDITIONS: always_true() = True")
        return True

    @staticmethod
    def always_false() -> bool:
        """Always returns False (AlwaysFalse)."""
        logger.debug("FR-SERVICES-TIME-CONDITIONS: always_false() = False")
        return False

    @staticmethod
    def is_bar_open() -> bool:
        """Return True if evaluating at bar open (IsBarOpen)."""
        logger.debug("FR-SERVICES-TIME-CONDITIONS: is_bar_open() = True")
        return True

    def bar_hour_is(self, hour: int, shift: int = 0) -> bool:
        """Check if bar hour at shift equals target hour (BarHourIs)."""
        res = self._bt.bar_hour(shift) == hour
        logger.debug(
            "FR-SERVICES-TIME-CONDITIONS: bar_hour_is(%d, %d) = %s",
            hour,
            shift,
            res,
        )
        return res

    def bar_hour_is_bigger(self, hour: int, shift: int = 0) -> bool:
        """Check if bar hour at shift is greater than target (BarHourIsBigger)."""
        h = self._bt.bar_hour(shift)
        res = h > hour if h != -1 else False
        logger.debug(
            "FR-SERVICES-TIME-CONDITIONS: bar_hour_is_bigger(%d, %d) = %s",
            hour,
            shift,
            res,
        )
        return res

    def bar_hour_is_smaller(self, hour: int, shift: int = 0) -> bool:
        """Check if bar hour at shift is less than target (BarHourIsSmaller)."""
        h = self._bt.bar_hour(shift)
        res = h < hour if h != -1 else False
        logger.debug(
            "FR-SERVICES-TIME-CONDITIONS: bar_hour_is_smaller(%d, %d) = %s",
            hour,
            shift,
            res,
        )
        return res

    def bar_minute_is(self, minute: int, shift: int = 0) -> bool:
        """Check if bar minute at shift equals target minute (BarMinuteIs)."""
        res = self._bt.bar_minute(shift) == minute
        logger.debug(
            "FR-SERVICES-TIME-CONDITIONS: bar_minute_is(%d, %d) = %s",
            minute,
            shift,
            res,
        )
        return res

    def bar_day_of_week_is(self, day: int, shift: int = 0) -> bool:
        """Check if bar day of week (1=Mon..7=Sun) equals target (BarDayOfWeekIs)."""
        res = self._bt.bar_day_of_week(shift) == day
        logger.debug(
            "FR-SERVICES-TIME-CONDITIONS: bar_day_of_week_is(%d, %d) = %s",
            day,
            shift,
            res,
        )
        return res

    def bar_day_of_week_is_not(self, day: int, shift: int = 0) -> bool:
        """Check if bar day of week does not equal target (BarDayOfWeekIsNot)."""
        dow = self._bt.bar_day_of_week(shift)
        res = dow != day if dow != -1 else False
        logger.debug(
            "FR-SERVICES-TIME-CONDITIONS: bar_day_of_week_is_not(%d, %d) = %s",
            day,
            shift,
            res,
        )
        return res

    def bar_month_is(self, month: int, shift: int = 0) -> bool:
        """Check if bar month (1-12) equals target (BarMonthIs)."""
        res = self._bt.bar_month(shift) == month
        logger.debug(
            "FR-SERVICES-TIME-CONDITIONS: bar_month_is(%d, %d) = %s",
            month,
            shift,
            res,
        )
        return res

    def bar_month_is_not(self, month: int, shift: int = 0) -> bool:
        """Check if bar month (1-12) does not equal target (BarMonthIsNot)."""
        m = self._bt.bar_month(shift)
        res = m != month if m != -1 else False
        logger.debug(
            "FR-SERVICES-TIME-CONDITIONS: bar_month_is_not(%d, %d) = %s",
            month,
            shift,
            res,
        )
        return res

    def bar_time_is(self, time_val: int, shift: int = 0) -> bool:
        """Check if bar time matches target time (BarTimeIs).

        Accepts either HHMM (e.g. 1430) or HHMMSS (e.g. 143000).
        """
        bt = self._bt.bar_time(shift)
        if bt == -1:
            return False
        res = (
            (bt // TIME_DIVISOR_100) == time_val
            if time_val < HHMM_THRESHOLD
            else bt == time_val
        )
        logger.debug(
            "FR-SERVICES-TIME-CONDITIONS: bar_time_is(%d, %d) = %s",
            time_val,
            shift,
            res,
        )
        return res

    # --- Current Bar Convenience Aliases ---

    def current_hour_is(self, hour: int) -> bool:
        """Check if CurrentHour equals target (CurrentHourIs)."""
        return self.bar_hour_is(hour, shift=0)

    def current_minute_is(self, minute: int) -> bool:
        """Check if CurrentMinute equals target (CurrentMinuteIs)."""
        return self.bar_minute_is(minute, shift=0)

    def current_day_of_week_is(self, day: int) -> bool:
        """Check if CurrentDayOfWeek equals target (CurrentDayOfWeekIs)."""
        return self.bar_day_of_week_is(day, shift=0)

    def current_month_is(self, month: int) -> bool:
        """Check if CurrentMonth equals target (CurrentMonthIs)."""
        return self.bar_month_is(month, shift=0)

    def current_time_is(self, time_val: int) -> bool:
        """Check if CurrentTime equals target (CurrentTimeIs)."""
        return self.bar_time_is(time_val, shift=0)

    # --- Calendar Cycle Predicates ---

    def first_week_of_month(self, shift: int = 0) -> bool:
        """Check if bar falls within first week of the month (FirstWeekOfMonth)."""
        w = self._bt.bar_week_of_month(shift)
        res = w == 1
        logger.debug(
            "FR-SERVICES-TIME-CONDITIONS: first_week_of_month(%d) = %s",
            shift,
            res,
        )
        return res

    def last_week_of_month(self, shift: int = 0) -> bool:
        """Check if bar falls within the last 7 days of the month (LastWeekOfMonth)."""
        dt = self._bt.get_dt(shift)
        if dt is None:
            return False
        # Last week of month if day >= threshold (covering 28-31 day months)
        res = dt.day >= LAST_WEEK_DAY_THRESHOLD
        logger.debug(
            "FR-SERVICES-TIME-CONDITIONS: last_week_of_month(%d) = %s",
            shift,
            res,
        )
        return res

    def is_month_first_trading_day(self, shift: int = 0) -> bool:
        """Check if bar is first trading day of month (IsMonthFirstTradingDay)."""
        dt = self._bt.get_dt(shift)
        if dt is None:
            return False
        # Scan backward in series for earlier bar in the same month
        n = len(self._bt)
        curr_idx = n - 1 - shift
        for prev_idx in range(curr_idx - 1, -1, -1):
            prev_dt = self._bt.get_dt(n - 1 - prev_idx)
            if (
                prev_dt is not None
                and prev_dt.month == dt.month
                and prev_dt.year == dt.year
                and prev_dt.day != dt.day
            ):
                return False
        return True

    def is_month_last_trading_day(self, shift: int = 0) -> bool:
        """Check if bar is last trading day of month (IsMonthLastTradingDay)."""
        dt = self._bt.get_dt(shift)
        if dt is None:
            return False
        # Scan forward in series for later bar in the same month
        n = len(self._bt)
        curr_idx = n - 1 - shift
        for next_idx in range(curr_idx + 1, n):
            next_dt = self._bt.get_dt(n - 1 - next_idx)
            if (
                next_dt is not None
                and next_dt.month == dt.month
                and next_dt.year == dt.year
                and next_dt.day != dt.day
            ):
                return False
        return True


__all__ = [
    "BarTime",
    "DateTimeSeries",
    "TimeConditions",
    "format_timestamp",
    "normalize_timestamps",
]
