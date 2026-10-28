"""Common internal utilities and numerical helpers for bar and time blocks."""

from __future__ import annotations

import calendar
import time
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import Any

import numpy as np

from app.host.logging import get_logger

__all__ = [
    "EPOCH_MINUTE_THRESHOLD",
    "HHMM_PACKED_SEC_THRESHOLD",
    "MS_THRESHOLD",
    "DateTime",
    "format_timestamp",
    "normalize_timestamps",
    "resolve_bar_count",
    "resolve_current_time_ms",
    "resolve_time_ms",
]

logger = get_logger(__name__)

HHMM_PACKED_SEC_THRESHOLD: int = 10000
EPOCH_MINUTE_THRESHOLD: int = 100_000_000
MS_THRESHOLD: int = 100_000_000_000
_FMT_TOKENS = (
    ("yyyy", "%Y"),
    ("MM", "%m"),
    ("dd", "%d"),
    ("HH", "%H"),
    ("mm", "%M"),
    ("ss", "%S"),
)
_WEEKDAYS = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)


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
            1: DateTime.add_years,
            2: DateTime.add_months,
            3: DateTime.add_weeks,
            5: DateTime.add_days,
            6: DateTime.add_days,
            7: DateTime.add_days,
            10: DateTime.add_hours,
            11: DateTime.add_hours,
            12: DateTime.add_minutes,
            13: DateTime.add_seconds,
        }
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


def _ts_from_sequence(seq: Any, shift: int) -> int:
    """Extract milliseconds from a timestamp sequence at shift."""
    if 0 <= shift < len(seq):
        val = seq[-(1 + shift)]
        if isinstance(val, datetime):
            return int(val.replace(tzinfo=UTC).timestamp() * 1000)
        sec = int(val)
        return sec if sec > MS_THRESHOLD else sec * 1000
    return -1


def _ts_from_scalar(val: Any) -> int:
    """Extract milliseconds from a scalar datetime or numeric epoch value."""
    if isinstance(val, datetime):
        return int(val.replace(tzinfo=UTC).timestamp() * 1000)
    if isinstance(val, (int, float, np.integer, np.floating)):
        sec = int(val)
        return sec if sec > MS_THRESHOLD else sec * 1000
    return -1


def resolve_time_ms(source: Any, shift: int = 0) -> int:
    """Resolve epoch milliseconds at shift from diverse temporal sources."""
    if source is None:
        return -1
    if hasattr(source, "bar_ms") and callable(source.bar_ms):
        return int(source.bar_ms(shift))
    if hasattr(source, "get_timestamp") and callable(source.get_timestamp):
        ts = source.get_timestamp(shift)
        return int(ts * 1000) if ts != -1 else -1
    for attr in ("time", "timestamps"):
        if hasattr(source, attr):
            times = getattr(source, attr)
            if isinstance(times, (np.ndarray, Sequence)):
                return _ts_from_sequence(times, shift)
    if isinstance(source, (np.ndarray, Sequence)) and not isinstance(
        source, (str, bytes)
    ):
        return _ts_from_sequence(source, shift)
    return _ts_from_scalar(source) if shift == 0 else -1


def resolve_current_time_ms(source: Any = None) -> int:
    """Resolve current active broker or system clock in epoch milliseconds."""
    if source is not None:
        if hasattr(source, "current_time_ms") and source.current_time_ms is not None:
            return int(source.current_time_ms)
        ms = resolve_time_ms(source, shift=0)
        if ms != -1:
            return ms
    return DateTime.get_local_current_time_in_ms()


def resolve_bar_count(source: Any) -> int:
    """Resolve total bar count from temporal source."""
    if source is None:
        return 0
    if hasattr(source, "__len__"):
        try:
            return len(source)
        except TypeError, ValueError:
            pass
    if hasattr(source, "timestamps") and hasattr(source.timestamps, "__len__"):
        return len(source.timestamps)
    if hasattr(source, "time") and hasattr(source.time, "__len__"):
        return len(source.time)
    return 0
