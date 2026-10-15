# ruff: noqa: PLR0911, PLR0917, PLR2004, E501
"""High-precision financial timestamp and calendar arithmetic.

Description:
    Provides HQTime, a high-precision temporal utility class for financial applications.
    Delivers zero-dependency, high-throughput epoch-millisecond date, time,
    session-boundary, and market calendar conversions.

Purpose:
    FEAT-LIBS-TIME: High-precision temporal and epoch-millisecond calendar arithmetic.

Key Capabilities:
    - FR-LIBS-TIME-CALENDAR-EXTRACTION: Extract calendar and clock components.
      Associated: `HQTime.get_year()`, `HQTime.get_month()`, `HQTime.get_day()`,
      `HQTime.get_hour()`, `HQTime.get_minute()`, `HQTime.get_second()`, `HQTime.get_ymd()`.
      Logging: Pure in-memory arithmetic with zero side effects.
    - FR-LIBS-TIME-CALENDAR-MUTATION: Calendar offsets, boundaries, and setters.
      Associated: `HQTime.add_days()`, `HQTime.add_hours()`, `HQTime.set_hhmm()`,
      `HQTime.correct_day_start()`, `HQTime.correct_day_end_mt()`.
      Logging: Pure in-memory arithmetic with zero side effects.
    - FR-LIBS-TIME-FORMATTING-PARSING: Serialize and deserialize timestamps.
      Associated: `HQTime.to_string()`, `HQTime.format_date()`,
      `HQTime.parse_date_to_millis()`, `HQTime.to_long()`.
      Logging: Pure in-memory arithmetic with zero side effects.

Python API Usage:
    ```python
    from app.services.libs.time import HQTime

    ms = HQTime.to_long(2026, 10, 14, 15, 30, 0)
    ymd = HQTime.get_ymd(ms)  # 20261014
    hhmm = HQTime.get_hhmm(ms)  # 1530
    next_day = HQTime.add_days(ms, 1)
    ```

CLI Usage:
    ```bash
    uv run pytest tests/unit/services/test_hq_time.py --no-cov
    ```
"""

from __future__ import annotations

import calendar
import time
from datetime import UTC, datetime

__all__ = ["HQTime"]


class HQTime:
    """High-precision financial timestamp manipulation and temporal arithmetic."""

    DAY_MILLIS: int = 86_400_000
    MONDAY: int = 1
    TUESDAY: int = 2
    WEDNESDAY: int = 3
    THURSDAY: int = 4
    FRIDAY: int = 5
    SATURDAY: int = 6
    SUNDAY: int = 7
    LONG_DATE_FORMAT: str = "%Y.%m.%d %H:%M:%S"
    SHORT_DATE_FORMAT: str = "%Y.%m.%d"

    # --- Internal Helpers ---
    @staticmethod
    def _to_dt(ms: int) -> datetime:
        """Convert epoch milliseconds to a UTC datetime."""
        return datetime.fromtimestamp(ms / 1000.0, tz=UTC)

    @staticmethod
    def _to_ms(dt: datetime) -> int:
        """Convert a datetime to epoch milliseconds."""
        return int(dt.timestamp() * 1000)

    # --- Lifecycle ---
    @staticmethod
    def init() -> None:
        """Initialize HQTime resources."""

    # --- Component Extractors ---
    @staticmethod
    def get_year(time_ms: int) -> int:
        """Retrieve year component from timestamp."""
        return HQTime._to_dt(time_ms).year

    @staticmethod
    def get_full_year(time_ms: int) -> int:
        """Retrieve full 4-digit year component."""
        return HQTime._to_dt(time_ms).year

    @staticmethod
    def get_month(time_ms: int) -> int:
        """Retrieve 1-based month component (1..12)."""
        return HQTime._to_dt(time_ms).month

    @staticmethod
    def get_month_original(time_ms: int) -> int:
        """Retrieve 0-based month component (0..11)."""
        return HQTime._to_dt(time_ms).month - 1

    @staticmethod
    def get_day(time_ms: int) -> int:
        """Retrieve day-of-month component (1..31)."""
        return HQTime._to_dt(time_ms).day

    @staticmethod
    def get_hour(time_ms: int) -> int:
        """Retrieve hour component (0..23)."""
        return HQTime._to_dt(time_ms).hour

    @staticmethod
    def get_minute(time_ms: int) -> int:
        """Retrieve minute component (0..59)."""
        return HQTime._to_dt(time_ms).minute

    @staticmethod
    def get_second(time_ms: int) -> int:
        """Retrieve second component (0..59)."""
        return HQTime._to_dt(time_ms).second

    @staticmethod
    def get_millis(time_ms: int) -> int:
        """Retrieve millisecond part (0..999)."""
        return time_ms % 1000

    @staticmethod
    def get_millisecond(time_ms: int) -> int:
        """Retrieve millisecond part (0..999)."""
        return time_ms % 1000

    @staticmethod
    def get_day_of_week(time_ms: int) -> int:
        """Retrieve ISO day of week (Monday=1..Sunday=7)."""
        return HQTime._to_dt(time_ms).isoweekday()

    @staticmethod
    def get_day_of_week_original(time_ms: int) -> int:
        """Retrieve calendar day of week starting at Sunday (Sunday=1..Saturday=7)."""
        dow = HQTime._to_dt(time_ms).isoweekday()
        return 1 if dow == 7 else dow + 1

    @staticmethod
    def get_day_of_year(time_ms: int) -> int:
        """Retrieve day of year (1..366)."""
        return HQTime._to_dt(time_ms).timetuple().tm_yday

    @staticmethod
    def get_days_in_month(time_ms: int) -> int:
        """Retrieve number of days in the month of the timestamp."""
        dt = HQTime._to_dt(time_ms)
        return calendar.monthrange(dt.year, dt.month)[1]

    @staticmethod
    def get_week_of_year(time_ms: int) -> int:
        """Retrieve ISO week of year (1..53)."""
        return HQTime._to_dt(time_ms).isocalendar().week

    @staticmethod
    def get_week_of_month(time_ms: int) -> int:
        """Retrieve week of month (1..5)."""
        return (HQTime._to_dt(time_ms).day - 1) // 7 + 1

    @staticmethod
    def get_ymd(arg0: int, arg1: int | None = None, arg2: int | None = None) -> int:
        """Retrieve packed YYYYMMDD from timestamp or (year, month, day)."""
        if arg1 is not None:
            return arg0 * 10000 + arg1 * 100 + (arg2 or 0)
        dt = HQTime._to_dt(arg0)
        return dt.year * 10000 + dt.month * 100 + dt.day

    @staticmethod
    def get_hhmm(arg0: int | str) -> int:
        """Retrieve packed HHMM integer from timestamp or HH:MM string."""
        if isinstance(arg0, str):
            p = arg0.replace(":", " ").split()
            return int(p[0]) * 100 + int(p[1])
        dt = HQTime._to_dt(arg0)
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
        dt = HQTime._to_dt(time_ms)
        return HQTime._to_ms(datetime(dt.year, dt.month, dt.day, tzinfo=UTC))

    @staticmethod
    def correct_day_start(time_ms: int) -> int:
        """Normalize timestamp to the start of the day (00:00:00.000)."""
        return HQTime.get_date_in_ms(time_ms)

    @staticmethod
    def correct_day_end(time_ms: int) -> int:
        """Normalize timestamp to the end of the day (23:59:59.999)."""
        dt = HQTime._to_dt(time_ms)
        return HQTime._to_ms(
            datetime(dt.year, dt.month, dt.day, 23, 59, 59, 999000, tzinfo=UTC)
        )

    @staticmethod
    def correct_day_end_mt(time_ms: int) -> int:
        """Normalize timestamp to terminal bar day end (23:59:00.000)."""
        dt = HQTime._to_dt(time_ms)
        return HQTime._to_ms(
            datetime(dt.year, dt.month, dt.day, 23, 59, 0, 0, tzinfo=UTC)
        )

    # --- Calendar Arithmetic (Add / Minus) ---
    @staticmethod
    def add_years(time_ms: int, years: int) -> int:
        """Add years to timestamp handling leap year bounds."""
        dt = HQTime._to_dt(time_ms)
        target_year = dt.year + years
        day = min(dt.day, calendar.monthrange(target_year, dt.month)[1])
        return HQTime._to_ms(dt.replace(year=target_year, day=day))

    @staticmethod
    def add_months(time_ms: int, months: int) -> int:
        """Add months to timestamp handling month-length bounds."""
        dt = HQTime._to_dt(time_ms)
        total_months = dt.year * 12 + (dt.month - 1) + months
        target_year = total_months // 12
        target_month = (total_months % 12) + 1
        day = min(dt.day, calendar.monthrange(target_year, target_month)[1])
        return HQTime._to_ms(dt.replace(year=target_year, month=target_month, day=day))

    @staticmethod
    def add_weeks(time_ms: int, weeks: int) -> int:
        """Add weeks to timestamp."""
        return time_ms + weeks * 7 * HQTime.DAY_MILLIS

    @staticmethod
    def add_days(time_ms: int, days: int) -> int:
        """Add days to timestamp."""
        return time_ms + days * HQTime.DAY_MILLIS

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
        """Add amount to calendar field (1=Year, 2=Month, 3=Week, 5=Day, 10/11=Hour, 12=Minute, 13=Second)."""
        if calendar_field == 1:
            return HQTime.add_years(time_ms, amount)
        if calendar_field == 2:
            return HQTime.add_months(time_ms, amount)
        if calendar_field == 3:
            return HQTime.add_weeks(time_ms, amount)
        if calendar_field in (5, 6, 7):
            return HQTime.add_days(time_ms, amount)
        if calendar_field in (10, 11):
            return HQTime.add_hours(time_ms, amount)
        if calendar_field == 12:
            return HQTime.add_minutes(time_ms, amount)
        if calendar_field == 13:
            return HQTime.add_seconds(time_ms, amount)
        return time_ms + amount

    @staticmethod
    def minus(time_ms: int, calendar_field: int, amount: int) -> int:
        """Subtract amount of calendar field from timestamp."""
        return HQTime.add(time_ms, calendar_field, -amount)

    # --- Component Setters ---
    @staticmethod
    def set_hour(time_ms: int, hour: int) -> int:
        """Set hour of timestamp."""
        return HQTime._to_ms(HQTime._to_dt(time_ms).replace(hour=hour))

    @staticmethod
    def set_minute(time_ms: int, minute: int) -> int:
        """Set minute of timestamp."""
        return HQTime._to_ms(HQTime._to_dt(time_ms).replace(minute=minute))

    @staticmethod
    def set_second(time_ms: int, second: int) -> int:
        """Set second of timestamp."""
        return HQTime._to_ms(HQTime._to_dt(time_ms).replace(second=second))

    @staticmethod
    def set_milliseconds(time_ms: int, ms: int) -> int:
        """Set millisecond part of timestamp."""
        return (time_ms // 1000) * 1000 + ms

    @staticmethod
    def set_day_of_month(time_ms: int, day: int) -> int:
        """Set day of month of timestamp."""
        return HQTime._to_ms(HQTime._to_dt(time_ms).replace(day=day))

    @staticmethod
    def set_month_of_year(time_ms: int, month: int) -> int:
        """Set month of year of timestamp."""
        return HQTime._to_ms(HQTime._to_dt(time_ms).replace(month=month))

    @staticmethod
    def set_day_of_week(time_ms: int, dow: int) -> int:
        """Set day of week of timestamp (Monday=1..Sunday=7)."""
        return time_ms + (dow - HQTime.get_day_of_week(time_ms)) * HQTime.DAY_MILLIS

    @staticmethod
    def set_first_day_of_week(time_ms: int) -> int:
        """Set timestamp to start of the week (Monday 00:00:00.000)."""
        return HQTime.correct_day_start(HQTime.set_day_of_week(time_ms, HQTime.MONDAY))

    @staticmethod
    def set_hhmm(time_ms: int, hhmm: int) -> int:
        """Set time from packed HHMM integer, zeroing seconds and millis."""
        return HQTime._to_ms(
            HQTime._to_dt(time_ms).replace(
                hour=hhmm // 100, minute=hhmm % 100, second=0, microsecond=0
            )
        )

    @staticmethod
    def set_time_to_ts_time(time_ms: int, ts_time: int) -> int:
        """Set time from packed HHMM time."""
        return HQTime.set_hhmm(time_ms, ts_time)

    @staticmethod
    def set_time(
        time_ms: int,
        hour: int,
        minute: int,
        second: int,
        millis: int = 0,
    ) -> int:
        """Set time components (hour, minute, second, optional millis)."""
        return HQTime._to_ms(
            HQTime._to_dt(time_ms).replace(
                hour=hour, minute=minute, second=second, microsecond=millis * 1000
            )
        )

    # --- Comparisons & Differences ---
    @staticmethod
    def get_diff_in_days(t1: int, t2: int) -> int:
        """Calculate absolute whole days between two timestamps."""
        return int(abs(t2 - t1) / HQTime.DAY_MILLIS)

    @staticmethod
    def get_days_between(t1: int, t2: int) -> int:
        """Calculate signed days between two timestamps (t2 - t1)."""
        return int((t2 - t1) / HQTime.DAY_MILLIS)

    @staticmethod
    def get_minutes_between(t1: int, t2: int) -> int:
        """Calculate signed minutes between two timestamps (t2 - t1)."""
        return int((t2 - t1) / 60_000)

    @staticmethod
    def get_weeks_between(t1: int, t2: int) -> int:
        """Calculate signed weeks between two timestamps (t2 - t1)."""
        return int((t2 - t1) / (7 * HQTime.DAY_MILLIS))

    @staticmethod
    def get_months_between(t1: int, t2: int) -> int:
        """Calculate signed calendar months between two timestamps (t2 - t1)."""
        d1, d2 = HQTime._to_dt(t1), HQTime._to_dt(t2)
        return (d2.year - d1.year) * 12 + (d2.month - d1.month)

    @staticmethod
    def get_years_between(t1: int, t2: int) -> int:
        """Calculate signed calendar years between two timestamps (t2 - t1)."""
        return HQTime._to_dt(t2).year - HQTime._to_dt(t1).year

    @staticmethod
    def is_same_day(t1: int, t2: int) -> bool:
        """Check if two timestamps share the same calendar day."""
        return HQTime.get_ymd(t1) == HQTime.get_ymd(t2)

    @staticmethod
    def is_same_month(t1: int, t2: int) -> bool:
        """Check if two timestamps share the same calendar month and year."""
        d1, d2 = HQTime._to_dt(t1), HQTime._to_dt(t2)
        return d1.year == d2.year and d1.month == d2.month

    @staticmethod
    def is_same_week(t1: int, t2: int) -> int:
        """Return 1 if timestamps share same ISO week and year, else 0."""
        d1, d2 = HQTime._to_dt(t1), HQTime._to_dt(t2)
        return 1 if d1.isocalendar()[:2] == d2.isocalendar()[:2] else 0

    # --- Formatting & String Conversions ---
    @staticmethod
    def to_string(time_ms: int, fmt: str | None = None) -> str:
        """Format timestamp into string with optional format pattern."""
        f = (
            (fmt or HQTime.LONG_DATE_FORMAT)
            .replace("yyyy", "%Y")
            .replace("MM", "%m")
            .replace("dd", "%d")
            .replace("HH", "%H")
            .replace("mm", "%M")
            .replace("ss", "%S")
        )
        return HQTime._to_dt(time_ms).strftime(f)

    @staticmethod
    def to_full_datetime_string(time_ms: int) -> str:
        """Format timestamp into 'YYYY.MM.DD HH:MM:SS'."""
        return HQTime.to_string(time_ms, "%Y.%m.%d %H:%M:%S")

    @staticmethod
    def to_full_date_minute_string(time_ms: int) -> str:
        """Format timestamp into 'YYYY.MM.DD HH:MM'."""
        return HQTime.to_string(time_ms, "%Y.%m.%d %H:%M")

    @staticmethod
    def to_date_minute_string(time_ms: int) -> str:
        """Format timestamp into 'YYYY.MM.DD HH:MM'."""
        return HQTime.to_string(time_ms, "%Y.%m.%d %H:%M")

    @staticmethod
    def to_date_string(time_ms: int) -> str:
        """Format timestamp into 'YYYY.MM.DD'."""
        return HQTime.to_string(time_ms, "%Y.%m.%d")

    @staticmethod
    def to_ui_date_string(time_ms: int) -> str:
        """Format timestamp into UI date string 'YYYY.MM.DD'."""
        return HQTime.to_string(time_ms, "%Y.%m.%d")

    @staticmethod
    def format_date(time_ms: int, fmt: str | None = None) -> str:
        """Format date component into string."""
        return HQTime.to_string(time_ms, fmt or "%Y.%m.%d")

    @staticmethod
    def format_date_quick(time_ms: int) -> str:
        """Format date into 'YYYY.MM.DD' quickly."""
        return HQTime.to_string(time_ms, "%Y.%m.%d")

    @staticmethod
    def format_datetime(time_ms: int) -> str:
        """Format datetime into standard string."""
        return HQTime.to_full_datetime_string(time_ms)

    @staticmethod
    def format_time(time_ms: int) -> str:
        """Format time component into 'HH:MM:SS'."""
        return HQTime.to_string(time_ms, "%H:%M:%S")

    @staticmethod
    def to_hhmm_string(time_ms: int) -> str:
        """Format time component into 'HH:MM'."""
        return HQTime.to_string(time_ms, "%H:%M")

    @staticmethod
    def to_full_time(time_ms: int) -> str:
        """Format time into 'HH:MM:SS.mmm'."""
        dt = HQTime._to_dt(time_ms)
        return f"{dt.strftime('%H:%M:%S')}.{dt.microsecond // 1000:03d}"

    @staticmethod
    def get_log_time(include_date: bool = True, include_millis: bool = True) -> str:
        """Retrieve current UTC timestamp formatted for logging."""
        dt = datetime.now(UTC)
        d = f"{dt.strftime('%Y-%m-%d')} " if include_date else ""
        m = f".{dt.microsecond // 1000:03d}" if include_millis else ""
        return f"{d}{dt.strftime('%H:%M:%S')}{m}"

    # --- Parsing ---
    @staticmethod
    def parse_to_millis(date_str: str, fmt: str) -> int:
        """Parse date string into epoch milliseconds using custom format."""
        f = (
            fmt.replace("yyyy", "%Y")
            .replace("MM", "%m")
            .replace("dd", "%d")
            .replace("HH", "%H")
            .replace("mm", "%M")
            .replace("ss", "%S")
        )
        return int(
            datetime.strptime(date_str, f).replace(tzinfo=UTC).timestamp() * 1000
        )

    @staticmethod
    def parse_date_to_millis(date_str: str) -> int:
        """Parse standard date/time string into epoch milliseconds."""
        s = date_str.strip().replace("-", ".").replace("/", ".")
        if " " in s:
            parts = s.split()
            date_p, time_p = parts[0], parts[1]
            t_parts = time_p.split(":")
            h = int(t_parts[0])
            m = int(t_parts[1]) if len(t_parts) > 1 else 0
            sec = int(t_parts[2]) if len(t_parts) > 2 else 0
        else:
            date_p, h, m, sec = s, 0, 0, 0
        d_parts = [int(x) for x in date_p.split(".")]
        return HQTime.to_long(d_parts[0], d_parts[1], d_parts[2], h, m, sec)

    @staticmethod
    def to_time(time_ms: int) -> datetime:
        """Convert epoch milliseconds to a UTC datetime instance."""
        return HQTime._to_dt(time_ms)

    @staticmethod
    def to_date(time_ms: int) -> datetime:
        """Convert epoch milliseconds to a UTC datetime instance."""
        return HQTime._to_dt(time_ms)

    @staticmethod
    def to_long(
        year: int,
        month: int,
        day: int,
        hour: int = 0,
        minute: int = 0,
        second: int = 0,
    ) -> int:
        """Create epoch milliseconds from calendar components."""
        return HQTime._to_ms(
            datetime(year, month, day, hour, minute, second, tzinfo=UTC)
        )

    # --- Specialized Temporal Conversions ---
    @staticmethod
    def hhmm_to_minutes(hhmm: int) -> int:
        """Convert packed HHMM integer to minutes of day (e.g. 1430 -> 870)."""
        return (hhmm // 100) * 60 + (hhmm % 100)

    @staticmethod
    def minutes_to_hhmm(minutes: int) -> int:
        """Convert minutes of day to packed HHMM integer (e.g. 870 -> 1430)."""
        return (minutes // 60) * 100 + (minutes % 60)

    @staticmethod
    def get_time_as_ts_time(time_ms: int) -> int:
        """Retrieve packed HHMM integer timestamp."""
        return HQTime.get_hhmm(time_ms)

    @staticmethod
    def get_ts_diff_in_minutes(ts1: int, ts2: int) -> int:
        """Calculate minute difference between two packed HHMM times."""
        return HQTime.hhmm_to_minutes(ts2) - HQTime.hhmm_to_minutes(ts1)

    @staticmethod
    def dow_to_metatrader(dow: int) -> int:
        """Convert ISO DOW (Mon=1..Sun=7) to terminal DOW (Sun=0, Mon=1..Sat=6)."""
        return 0 if dow == 7 else dow

    @staticmethod
    def dow_to_string(dow: int) -> str:
        """Convert DOW number to English weekday name."""
        names = {
            1: "Monday",
            2: "Tuesday",
            3: "Wednesday",
            4: "Thursday",
            5: "Friday",
            6: "Saturday",
            7: "Sunday",
        }
        return names.get(dow, "")

    @staticmethod
    def times_in_same_minute(time1: int, time2: int) -> bool:
        """Check if two timestamps or minute counts belong to the same minute."""
        if time1 > 100_000_000 and time2 > 100_000_000:
            return time1 // 60_000 == time2 // 60_000
        return time1 == time2

    @staticmethod
    def to_number_time(time_ms: int) -> int:
        """Retrieve numeric time representation (HHMM)."""
        return HQTime.get_hhmm(time_ms)

    @staticmethod
    def get_datetime(time_ms: int) -> int:
        """Retrieve packed YYYYMMDDHHMM integer."""
        dt = HQTime._to_dt(time_ms)
        return (dt.year * 10000 + dt.month * 100 + dt.day) * 10000 + (
            dt.hour * 100 + dt.minute
        )

    @staticmethod
    def get_local_current_time_in_ms() -> int:
        """Retrieve current system time in epoch milliseconds."""
        return int(time.time() * 1000)

    @staticmethod
    def get_duration_text(duration_ms: int) -> str:
        """Format duration milliseconds into human-readable string."""
        total_seconds = abs(duration_ms) // 1000
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        parts: list[str] = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0 or days > 0:
            parts.append(f"{hours}h")
        if minutes > 0 or hours > 0 or days > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")
        return " ".join(parts)
