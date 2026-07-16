"""Expose injectable clocks and canonical UTC timestamp operations.

All accepted cross-domain datetimes are aware and use a zero UTC offset.
"""

from app.utils.time.clocks import Clock, SystemClock, utc_now
from app.utils.time.timestamps import (
    age_seconds,
    format_utc_timestamp,
    is_fresh,
    parse_utc_timestamp,
)

__all__ = (
    "Clock",
    "SystemClock",
    "age_seconds",
    "format_utc_timestamp",
    "is_fresh",
    "parse_utc_timestamp",
    "utc_now",
)
