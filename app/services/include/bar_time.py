"""DateTime, BarTime component extractors, and TimeConditions predicates.

Description:
    Provides consolidated temporal and calendar building blocks:
    - DateTime: High-precision epoch-millisecond scalar calendar/session arithmetic
      and shift-indexed historical timestamp series wrapper.
    - BarTime: Bar and broker-clock feature extractors (bar_hour, bar_minute,
      bar_day_of_week, bar_day_of_month, bar_month, bar_date, bar_time,
      bar_week_of_month, current_bar, and current_* extractors).
    - TimeConditions: Temporal rule predicates and calendar cycle evaluators.

Purpose:
    FEAT-LIBS-BAR-TIME: Temporal calendar arithmetic, extractors, and predicates.

Key Capabilities:
    - FR-LIBS-DATETIME-SERIES-STORAGE: Epoch-ms calendar math and timestamp series.
      Associated: `DateTime.to_long()`, `DateTime.get_timestamp()`,
      `DateTime.get_datetime()`.
      Logging: DEBUG on series initialization and out-of-bounds shift access.
    - FR-LIBS-BAR-TIME-EXTRACT: Calendar and clock component extraction via DateTime.
      Associated: `BarTime.bar_hour()`, `BarTime.bar_day_of_week()`,
      `BarTime.bar_time()`.
      Logging: DEBUG on point evaluation, INFO on series export.
    - FR-LIBS-TIME-CONDITIONS: Temporal rule predicates and calendar conditions.
      Associated: `TimeConditions.bar_hour_is()`, `TimeConditions.bar_time_is()`,
      `TimeConditions.is_month_first_trading_day()`,
      `TimeConditions.is_month_last_trading_day()`.
      Logging: DEBUG on condition evaluations.
    - FR-LIBS-FORMAT-TIMESTAMP: Format and normalize timestamps and datetimes.
      Associated: `format_timestamp()`, `normalize_timestamps()`.
      Logging: Passive formatting; emits no operational log events.

Python API Usage:
    ```python
    from app.services.include.bar_time import BarTime, DateTime, TimeConditions
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_bar_time.py --no-cov
    ```
"""

from __future__ import annotations

import calendar
import time
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import Any

import numpy as np
from app.host.logging import get_logger
from app.services.indicators.base import IndicatorSeries

__all__ = [
    "BarTime", "DateTime", "TimeConditions", "format_timestamp", "normalize_timestamps",
]  # fmt: skip

logger = get_logger(__name__)

HHMM_PACKED_SEC_THRESHOLD: int = 10000
EPOCH_MINUTE_THRESHOLD: int = 100_000_000
MS_THRESHOLD: int = 100_000_000_000
_FMT_TOKENS = (
    ("yyyy", "%Y"), ("MM", "%m"), ("dd", "%d"), ("HH", "%H"), ("mm", "%M"), ("ss", "%S")
)  # fmt: skip
_WEEKDAYS = (
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
)  # fmt: skip


def normalize_timestamps(timestamps: Any) -> np.ndarray[Any, np.dtype[np.int64]]:
    """Convert sequence of timestamps to POSIX seconds."""
    if isinstance(timestamps, np.ndarray) and np.issubdtype(
        timestamps.dtype, np.integer
    ):
        arr = timestamps.astype(np.int64)
        return arr // 1000 if (len(arr) > 0 and arr[0] > MS_THRESHOLD) else arr
    res: list[int] = []
    for ts in timestamps:
        if isinstance(ts, (int, float, np.integer, np.floating)):
            sec = int(ts)
            res.append(sec // 1000 if sec > MS_THRESHOLD else sec)
        elif isinstance(ts, datetime):
            res.append(int(ts.replace(tzinfo=UTC).timestamp()))
        elif isinstance(ts, (str, np.str_)):
            res.append(int(datetime.fromisoformat(str(ts)).timestamp()))
        else:
            res.append(int(np.datetime64(ts, "s").astype("int64")))
    return np.array(res, dtype=np.int64)


def _parse_timestamp(timestamp: float | datetime) -> datetime:
    """Normalize timestamp or datetime into UTC datetime."""
    if isinstance(timestamp, bool):
        raise TypeError("Unsupported timestamp type: bool")
    if isinstance(timestamp, (int, float)):
        sec = float(timestamp)
        ms = int(sec * 1000) if abs(sec) <= MS_THRESHOLD else int(sec)
        return DateTime.to_date(ms)
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
    """Format a POSIX timestamp or datetime into a standardized string."""
    if timestamp is None:
        return "N/A"
    dt = _parse_timestamp(timestamp)
    if use_local_tz:
        dt = dt.astimezone()
    if fmt.lower() == "iso":
        return dt.isoformat() if include_tz else dt.replace(tzinfo=None).isoformat()
    if precision is not None and ".%f" in fmt:
        frac = dt.strftime("%f")[:precision] if precision > 0 else ""
        base = dt.strftime(fmt.replace(".%f", ""))
        formatted = f"{base}.{frac}" if frac else base
    else:
        formatted = dt.strftime(fmt)
    if not include_tz:
        return formatted
    return f"{formatted} {dt.strftime('%:z') if use_local_tz else 'UTC'}"


def _log_cond(name: str, arg: int, res: bool) -> bool:
    """Log temporal condition evaluation and return boolean result."""
    logger.debug("FR-LIBS-TIME-CONDITIONS: %s(%d)=%s", name, arg, res)
    return res


class DateTime:
    """High-precision financial date/time utilities and timestamp series."""

    DAY_MILLIS: int = 86_400_000
    MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY = 1, 2, 3, 4, 5, 6, 7
    LONG_DATE_FORMAT, SHORT_DATE_FORMAT = "%Y.%m.%d %H:%M:%S", "%Y.%m.%d"

    def __init__(
        self,
        timestamps: np.ndarray[Any, Any] | Sequence[Any],
        name: str = "DateTime",
    ) -> None:
        """Initialize DateTime series with timestamps."""
        self._timestamps = normalize_timestamps(timestamps)
        if len(self._timestamps) == 0:
            raise ValueError("DateTime timestamps array cannot be empty.")
        self._name = name
        logger.debug("FR-LIBS-DATETIME-SERIES-STORAGE: Init '%s' (%d)", name, len(self))

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
        """Get POSIX timestamp in seconds at historical shift."""
        if shift < 0 or shift >= len(self._timestamps):
            logger.debug("FR-LIBS-DATETIME-SERIES-STORAGE: Shift %d OOB", shift)
            return -1
        return int(self._timestamps[-(1 + shift)])

    def get_datetime(self: DateTime | int, shift: int = 0) -> datetime | int | None:
        """Return UTC datetime at shift on a series, or YYYYMMDDHHMM int for ms."""
        if isinstance(self, DateTime):
            ts = self.get_timestamp(shift)
            return None if ts == -1 else DateTime.to_date(ts * 1000)
        dt = DateTime._to_dt(self)
        return (dt.year * 10000 + dt.month * 100 + dt.day) * 10000 + (
            dt.hour * 100 + dt.minute
        )

    @staticmethod
    def _to_dt(ms: int) -> datetime:
        """Convert epoch milliseconds to a UTC datetime."""
        return datetime.fromtimestamp(ms / 1000.0, tz=UTC)

    @staticmethod
    def _to_ms(dt: datetime) -> int:
        """Convert a datetime to epoch milliseconds."""
        return int(dt.timestamp() * 1000)

    @staticmethod
    def get_year(time_ms: int) -> int:
        """Retrieve 4-digit year component from timestamp."""
        return DateTime._to_dt(time_ms).year

    @staticmethod
    def get_month(time_ms: int) -> int:
        """Retrieve 1-based month component (1..12)."""
        return DateTime._to_dt(time_ms).month

    @staticmethod
    def get_month_original(time_ms: int) -> int:
        """Retrieve 0-based month component (0..11)."""
        return DateTime._to_dt(time_ms).month - 1

    @staticmethod
    def get_day(time_ms: int) -> int:
        """Retrieve day-of-month component (1..31)."""
        return DateTime._to_dt(time_ms).day

    @staticmethod
    def get_hour(time_ms: int) -> int:
        """Retrieve hour component (0..23)."""
        return DateTime._to_dt(time_ms).hour

    @staticmethod
    def get_minute(time_ms: int) -> int:
        """Retrieve minute component (0..59)."""
        return DateTime._to_dt(time_ms).minute

    @staticmethod
    def get_second(time_ms: int) -> int:
        """Retrieve second component (0..59)."""
        return DateTime._to_dt(time_ms).second

    @staticmethod
    def get_millis(time_ms: int) -> int:
        """Retrieve millisecond part (0..999)."""
        return time_ms % 1000

    @staticmethod
    def get_day_of_week(time_ms: int) -> int:
        """Retrieve ISO day of week (Monday=1..Sunday=7)."""
        return DateTime._to_dt(time_ms).isoweekday()

    @staticmethod
    def get_day_of_week_original(time_ms: int) -> int:
        """Retrieve day of week starting at Sunday (Sunday=0, Monday=1..Saturday=6)."""
        dow = DateTime._to_dt(time_ms).isoweekday()
        return 0 if dow == DateTime.SUNDAY else dow

    @staticmethod
    def get_day_of_year(time_ms: int) -> int:
        """Retrieve day of year (1..366)."""
        return DateTime._to_dt(time_ms).timetuple().tm_yday

    @staticmethod
    def get_days_in_month(time_ms: int) -> int:
        """Retrieve number of days in the month of the timestamp."""
        dt = DateTime._to_dt(time_ms)
        return calendar.monthrange(dt.year, dt.month)[1]

    @staticmethod
    def get_week_of_year(time_ms: int) -> int:
        """Retrieve ISO week of year (1..53)."""
        return DateTime._to_dt(time_ms).isocalendar().week

    @staticmethod
    def get_week_of_month(time_ms: int) -> int:
        """Retrieve Monday-aligned week of month (1..6)."""
        date_only = DateTime.get_date_in_ms(time_ms)
        first_day = DateTime.set_day_of_month(date_only, 1)
        first_monday = (
            first_day - (DateTime.get_day_of_week(first_day) - 1) * DateTime.DAY_MILLIS
        )
        return ((date_only - first_monday) // DateTime.DAY_MILLIS) // 7 + 1

    @staticmethod
    def get_ymd(arg0: int, arg1: int | None = None, arg2: int | None = None) -> int:
        """Retrieve packed YYYYMMDD from timestamp or (year, month, day)."""
        if arg1 is not None:
            return arg0 * 10000 + arg1 * 100 + (arg2 or 0)
        dt = DateTime._to_dt(arg0)
        return dt.year * 10000 + dt.month * 100 + dt.day

    @staticmethod
    def get_hhmm(arg0: int | str) -> int:
        """Retrieve packed HHMM integer from timestamp or HH:MM string."""
        if isinstance(arg0, str):
            p = arg0.replace(":", " ").split()
            return int(p[0]) * 100 + int(p[1])
        dt = DateTime._to_dt(arg0)
        return dt.hour * 100 + dt.minute

    @staticmethod
    def get_hms(hour: int, minute: int, second: int) -> float:
        """Retrieve fractional hours from hour, minute, and second."""
        return hour + minute / 60.0 + second / 3600.0

    @staticmethod
    def to_hours(time_ms: int) -> int:
        """Convert epoch milliseconds to whole hours."""
        return time_ms // 3_600_000

    @staticmethod
    def get_date_in_ms(time_ms: int) -> int:
        """Retrieve timestamp truncated to start of day (00:00:00.000)."""
        dt = DateTime._to_dt(time_ms)
        return DateTime._to_ms(datetime(dt.year, dt.month, dt.day, tzinfo=UTC))

    @staticmethod
    def correct_day_start(time_ms: int) -> int:
        """Normalize timestamp to the start of the day (00:00:00.000)."""
        return DateTime.get_date_in_ms(time_ms)

    @staticmethod
    def correct_day_end(time_ms: int) -> int:
        """Normalize timestamp to the end of the day (23:59:59.999)."""
        dt = DateTime._to_dt(time_ms)
        return DateTime._to_ms(
            datetime(dt.year, dt.month, dt.day, 23, 59, 59, 999000, tzinfo=UTC)
        )

    @staticmethod
    def correct_day_end_mt(time_ms: int) -> int:
        """Normalize timestamp to terminal bar day end (23:59:00.000)."""
        dt = DateTime._to_dt(time_ms)
        return DateTime._to_ms(datetime(dt.year, dt.month, dt.day, 23, 59, tzinfo=UTC))

    @staticmethod
    def add_years(time_ms: int, years: int) -> int:
        """Add years to timestamp handling leap year bounds."""
        dt = DateTime._to_dt(time_ms)
        yr = dt.year + years
        return DateTime._to_ms(
            dt.replace(year=yr, day=min(dt.day, calendar.monthrange(yr, dt.month)[1]))
        )

    @staticmethod
    def add_months(time_ms: int, months: int) -> int:
        """Add months to timestamp handling month-length bounds."""
        dt = DateTime._to_dt(time_ms)
        total = dt.year * 12 + (dt.month - 1) + months
        yr, mo = total // 12, (total % 12) + 1
        return DateTime._to_ms(
            dt.replace(
                year=yr, month=mo, day=min(dt.day, calendar.monthrange(yr, mo)[1])
            )
        )

    @staticmethod
    def add_weeks(time_ms: int, weeks: int) -> int:
        """Add weeks to timestamp."""
        return time_ms + weeks * 7 * DateTime.DAY_MILLIS

    @staticmethod
    def add_days(time_ms: int, days: int) -> int:
        """Add days to timestamp."""
        return time_ms + days * DateTime.DAY_MILLIS

    @staticmethod
    def add_hours(time_ms: int, hours: int) -> int:
        """Add hours to timestamp."""
        return time_ms + hours * 3_600_000

    @staticmethod
    def add_minutes(time_ms: int, minutes: int) -> int:
        """Add minutes to timestamp."""
        return time_ms + minutes * 60_000

    @staticmethod
    def add_seconds(time_ms: int, seconds: int) -> int:
        """Add seconds to timestamp."""
        return time_ms + seconds * 1_000

    @staticmethod
    def add(time_ms: int, calendar_field: int, amount: int) -> int:
        """Add amount to calendar field (1=Yr, 2=Mo, 3=Wk, 5..7=Day, 10..13=Time)."""
        dispatch: dict[int, Callable[[int, int], int]] = {
            1: DateTime.add_years, 2: DateTime.add_months, 3: DateTime.add_weeks,
            5: DateTime.add_days, 6: DateTime.add_days, 7: DateTime.add_days,
            10: DateTime.add_hours, 11: DateTime.add_hours, 12: DateTime.add_minutes,
            13: DateTime.add_seconds,
        }  # fmt: skip
        fn = dispatch.get(calendar_field)
        return fn(time_ms, amount) if fn is not None else time_ms + amount

    @staticmethod
    def minus(time_ms: int, calendar_field: int, amount: int) -> int:
        """Subtract amount of calendar field from timestamp."""
        return DateTime.add(time_ms, calendar_field, -amount)

    @staticmethod
    def set_hour(time_ms: int, hour: int) -> int:
        """Set hour of timestamp."""
        return DateTime._to_ms(DateTime._to_dt(time_ms).replace(hour=hour))

    @staticmethod
    def set_minute(time_ms: int, minute: int) -> int:
        """Set minute of timestamp."""
        return DateTime._to_ms(DateTime._to_dt(time_ms).replace(minute=minute))

    @staticmethod
    def set_second(time_ms: int, second: int) -> int:
        """Set second of timestamp."""
        return DateTime._to_ms(DateTime._to_dt(time_ms).replace(second=second))

    @staticmethod
    def set_milliseconds(time_ms: int, ms: int) -> int:
        """Set millisecond part of timestamp."""
        return (time_ms // 1000) * 1000 + ms

    @staticmethod
    def set_day_of_month(time_ms: int, day: int) -> int:
        """Set day of month of timestamp."""
        return DateTime._to_ms(DateTime._to_dt(time_ms).replace(day=day))

    @staticmethod
    def set_month_of_year(time_ms: int, month: int) -> int:
        """Set month of year of timestamp."""
        return DateTime._to_ms(DateTime._to_dt(time_ms).replace(month=month))

    @staticmethod
    def set_day_of_week(time_ms: int, dow: int) -> int:
        """Set day of week of timestamp (Monday=1..Sunday=7)."""
        return time_ms + (dow - DateTime.get_day_of_week(time_ms)) * DateTime.DAY_MILLIS

    @staticmethod
    def set_first_day_of_week(time_ms: int) -> int:
        """Set timestamp to start of the week (Monday 00:00:00.000)."""
        return DateTime.correct_day_start(
            DateTime.set_day_of_week(time_ms, DateTime.MONDAY)
        )

    @staticmethod
    def set_hhmm(time_ms: int, hhmm: int) -> int:
        """Set time from packed HHMM integer, zeroing seconds and millis."""
        return DateTime._to_ms(
            DateTime._to_dt(time_ms).replace(
                hour=hhmm // 100, minute=hhmm % 100, second=0, microsecond=0
            )
        )

    @staticmethod
    def set_time(
        time_ms: int, hour: int, minute: int, second: int, millis: int = 0
    ) -> int:
        """Set time components (hour, minute, second, optional millis)."""
        return DateTime._to_ms(
            DateTime._to_dt(time_ms).replace(
                hour=hour, minute=minute, second=second, microsecond=millis * 1000
            )
        )

    @staticmethod
    def get_diff_in_days(t1: int, t2: int) -> int:
        """Calculate absolute whole days between two timestamps."""
        return int(abs(t2 - t1) / DateTime.DAY_MILLIS)

    @staticmethod
    def get_days_between(t1: int, t2: int) -> int:
        """Calculate signed days between two timestamps (t2 - t1)."""
        return int((t2 - t1) / DateTime.DAY_MILLIS)

    @staticmethod
    def get_minutes_between(t1: int, t2: int) -> int:
        """Calculate signed minutes between two timestamps (t2 - t1)."""
        return int((t2 - t1) / 60_000)

    @staticmethod
    def get_weeks_between(t1: int, t2: int) -> int:
        """Calculate signed weeks between two timestamps (t2 - t1)."""
        return int((t2 - t1) / (7 * DateTime.DAY_MILLIS))

    @staticmethod
    def get_months_between(t1: int, t2: int) -> int:
        """Calculate signed calendar months between two timestamps (t2 - t1)."""
        d1, d2 = DateTime._to_dt(t1), DateTime._to_dt(t2)
        return (d2.year - d1.year) * 12 + (d2.month - d1.month)

    @staticmethod
    def get_years_between(t1: int, t2: int) -> int:
        """Calculate signed calendar years between two timestamps (t2 - t1)."""
        return DateTime._to_dt(t2).year - DateTime._to_dt(t1).year

    @staticmethod
    def is_same_day(t1: int, t2: int) -> bool:
        """Check if two timestamps share the same calendar day."""
        return DateTime.get_ymd(t1) == DateTime.get_ymd(t2)

    @staticmethod
    def is_same_month(t1: int, t2: int) -> bool:
        """Check if two timestamps share the same calendar month and year."""
        d1, d2 = DateTime._to_dt(t1), DateTime._to_dt(t2)
        return d1.year == d2.year and d1.month == d2.month

    @staticmethod
    def is_same_week(t1: int, t2: int) -> int:
        """Return 1 if timestamps share same ISO week and year, else 0."""
        d1, d2 = DateTime._to_dt(t1), DateTime._to_dt(t2)
        return 1 if d1.isocalendar()[:2] == d2.isocalendar()[:2] else 0

    @staticmethod
    def _norm_fmt(fmt: str) -> str:
        """Translate Java-style date tokens to strftime directives."""
        for src, dst in _FMT_TOKENS:
            fmt = fmt.replace(src, dst)
        return fmt

    @staticmethod
    def to_string(time_ms: int, fmt: str | None = None) -> str:
        """Format timestamp into string with optional format pattern."""
        return DateTime._to_dt(time_ms).strftime(
            DateTime._norm_fmt(fmt or DateTime.LONG_DATE_FORMAT)
        )

    @staticmethod
    def to_full_datetime_string(time_ms: int) -> str:
        """Format timestamp into 'YYYY.MM.DD HH:MM:SS'."""
        return DateTime.to_string(time_ms, "%Y.%m.%d %H:%M:%S")

    @staticmethod
    def to_date_minute_string(time_ms: int) -> str:
        """Format timestamp into 'YYYY.MM.DD HH:MM'."""
        return DateTime.to_string(time_ms, "%Y.%m.%d %H:%M")

    @staticmethod
    def to_date_string(time_ms: int) -> str:
        """Format timestamp into 'YYYY.MM.DD'."""
        return DateTime.to_string(time_ms, "%Y.%m.%d")

    @staticmethod
    def format_date(time_ms: int, fmt: str | None = None) -> str:
        """Format date component into string."""
        return DateTime.to_string(time_ms, fmt or "%Y.%m.%d")

    @staticmethod
    def format_time(time_ms: int) -> str:
        """Format time component into 'HH:MM:SS'."""
        return DateTime.to_string(time_ms, "%H:%M:%S")

    @staticmethod
    def to_hhmm_string(time_ms: int) -> str:
        """Format time component into 'HH:MM'."""
        return DateTime.to_string(time_ms, "%H:%M")

    @staticmethod
    def to_full_time(time_ms: int) -> str:
        """Format time into 'HH:MM:SS.mmm'."""
        dt = DateTime._to_dt(time_ms)
        return f"{dt.strftime('%H:%M:%S')}.{dt.microsecond // 1000:03d}"

    @staticmethod
    def get_log_time(include_date: bool = True, include_millis: bool = True) -> str:
        """Retrieve current UTC timestamp formatted for logging."""
        dt = datetime.now(UTC)
        d = f"{dt.strftime('%Y-%m-%d')} " if include_date else ""
        m = f".{dt.microsecond // 1000:03d}" if include_millis else ""
        return f"{d}{dt.strftime('%H:%M:%S')}{m}"

    @staticmethod
    def parse_to_millis(date_str: str, fmt: str) -> int:
        """Parse date string into epoch milliseconds using custom format."""
        dt = datetime.strptime(date_str, DateTime._norm_fmt(fmt)).replace(tzinfo=UTC)
        return int(dt.timestamp() * 1000)

    @staticmethod
    def parse_date_to_millis(date_str: str) -> int:
        """Parse standard date/time string into epoch milliseconds."""
        s = date_str.strip().replace("-", ".").replace("/", ".")
        if " " in s:
            date_p, time_p = s.split()[:2]
            t_parts = [int(x) for x in time_p.split(":")]
            h, m, sec = [*t_parts, 0, 0][:3]
        else:
            date_p, h, m, sec = s, 0, 0, 0
        y, mo, d = (int(x) for x in date_p.split(".")[:3])
        return DateTime.to_long(y, mo, d, h, m, sec)

    @staticmethod
    def to_date(time_ms: int) -> datetime:
        """Convert epoch milliseconds to a UTC datetime instance."""
        return DateTime._to_dt(time_ms)

    @staticmethod
    def to_long(  # noqa: PLR0917
        year: int,
        month: int,
        day: int,
        hour: int = 0,
        minute: int = 0,
        second: int = 0,
    ) -> int:
        """Create epoch milliseconds from calendar components."""
        return DateTime._to_ms(
            datetime(year, month, day, hour, minute, second, tzinfo=UTC)
        )

    @staticmethod
    def hhmm_to_minutes(hhmm: int) -> int:
        """Convert packed HHMM integer to minutes of day (e.g. 1430 -> 870)."""
        return (hhmm // 100) * 60 + (hhmm % 100)

    @staticmethod
    def minutes_to_hhmm(minutes: int) -> int:
        """Convert minutes of day to packed HHMM integer (e.g. 870 -> 1430)."""
        return (minutes // 60) * 100 + (minutes % 60)

    @staticmethod
    def get_ts_diff_in_minutes(ts1: int, ts2: int) -> int:
        """Calculate minute difference between two packed HHMM times."""
        return DateTime.hhmm_to_minutes(ts2) - DateTime.hhmm_to_minutes(ts1)

    @staticmethod
    def dow_to_metatrader(dow: int) -> int:
        """Convert ISO DOW (Mon=1..Sun=7) to terminal DOW (Sun=0, Mon=1..Sat=6)."""
        return 0 if dow == DateTime.SUNDAY else dow

    @staticmethod
    def dow_to_string(dow: int) -> str:
        """Convert DOW number to English weekday name."""
        return _WEEKDAYS[dow - 1] if 1 <= dow <= DateTime.SUNDAY else ""

    @staticmethod
    def times_in_same_minute(time1: int, time2: int) -> bool:
        """Check if two timestamps or minute counts belong to the same minute."""
        if time1 > EPOCH_MINUTE_THRESHOLD and time2 > EPOCH_MINUTE_THRESHOLD:
            return time1 // 60_000 == time2 // 60_000
        return time1 == time2

    @staticmethod
    def get_local_current_time_in_ms() -> int:
        """Retrieve current system time in epoch milliseconds."""
        return int(time.time() * 1000)

    @staticmethod
    def get_duration_text(duration_ms: int) -> str:
        """Format duration milliseconds into human-readable string."""
        d, rem = divmod(abs(duration_ms) // 1000, 86400)
        h, rem = divmod(rem, 3600)
        m, s = divmod(rem, 60)
        parts = [f"{d}d"] if d else []
        if h or d:
            parts.append(f"{h}h")
        if m or h or d:
            parts.append(f"{m}m")
        return " ".join([*parts, f"{s}s"])


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

    def _series_out(self, fn: Callable[[int], int], name: str) -> IndicatorSeries:
        """Export shift-extracted bar series as IndicatorSeries."""
        logger.info("FR-LIBS-BAR-TIME-EXTRACT: Exporting %s IndicatorSeries", name)
        n = len(self._series)
        return IndicatorSeries([fn(n - 1 - i) for i in range(n)], name)

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

    def hour_series(self) -> IndicatorSeries:
        """Export series of bar hours as IndicatorSeries."""
        return self._series_out(self.bar_hour, "BarHour")

    def minute_series(self) -> IndicatorSeries:
        """Export series of bar minutes as IndicatorSeries."""
        return self._series_out(self.bar_minute, "BarMinute")

    def day_of_week_series(self) -> IndicatorSeries:
        """Export series of bar day-of-week values as IndicatorSeries."""
        return self._series_out(self.bar_day_of_week, "BarDayOfWeek")

    def month_series(self) -> IndicatorSeries:
        """Export series of bar months as IndicatorSeries."""
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
