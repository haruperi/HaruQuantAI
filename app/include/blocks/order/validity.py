"""Bar-validity scheduling for pending orders.

Translates discrete chart-bar validity counts (e.g., expire after 3 H1 bars)
into explicit timezone-aware expiration timestamps compatible with broker contracts.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

TIMEFRAME_PATTERNS = {
    "M": lambda n: timedelta(minutes=n),
    "H": lambda n: timedelta(hours=n),
    "D": lambda n: timedelta(days=n),
    "W": lambda n: timedelta(weeks=n),
}


def parse_timeframe_delta(timeframe: str) -> timedelta:
    """Parse timeframe string into standard timedelta duration."""
    tf = timeframe.strip().upper()
    if tf == "DAILY":
        return timedelta(days=1)
    if tf == "WEEKLY":
        return timedelta(weeks=1)

    match = re.fullmatch(r"([MHDW])(\d+)", tf)
    if not match:
        raise ValueError(
            f"Unsupported timeframe '{timeframe}'. Use standard formats (M1, H1, D1)."
        )
    unit, count_str = match.groups()
    count = int(count_str)
    if count <= 0:
        raise ValueError("Timeframe multiplier must be positive")
    return TIMEFRAME_PATTERNS[unit](count)


def schedule_bar_validity(
    bar_start: datetime,
    timeframe: str,
    valid_bars: int,
) -> datetime | None:
    """Calculate pending order expiration datetime from discrete bar count.

    If valid_bars <= 0, the order is Good-Till-Cancelled (GTC) and None is returned.
    If valid_bars > 0, the expiration is bar_start + (valid_bars * timeframe_delta).
    Raises ValueError if bar_start is naive (lacks tzinfo).
    """
    if valid_bars <= 0:
        return None

    if bar_start.tzinfo is None or bar_start.utcoffset() is None:
        raise ValueError("bar_start must be timezone-aware")

    delta = parse_timeframe_delta(timeframe)
    return bar_start + valid_bars * delta
