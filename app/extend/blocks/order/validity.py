"""Bar-validity scheduling for pending orders.

Description:
    Translates discrete chart-bar validity counts (e.g., expire after N bars)
    into explicit timezone-aware expiration timestamps compatible with broker
    contracts, matching StrategyQuant BarsValid pending order behavior.
Purpose:
    FEAT-ORDER-BLOCKS: StrategyQuant donor-faithful order execution blocks.
Key Capabilities:
    - FR-ORDER-VALIDITY: Translate bar counts to expiration datetimes.
Python API Usage:
    from app.extend.blocks.order.validity import schedule_bar_validity
    exp = schedule_bar_validity(bar_start, "H1", 3)
CLI Usage:
    uv run pytest tests/extend/blocks/test_order_blocks.py --no-cov
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

from app.core.host.logging import get_logger

logger = get_logger(__name__)

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
        logger.debug(
            "FR-ORDER-VALIDITY: valid_bars=%s -> Good-Till-Cancelled (None)", valid_bars
        )
        return None

    if bar_start.tzinfo is None or bar_start.utcoffset() is None:
        raise ValueError("bar_start must be timezone-aware")

    delta = parse_timeframe_delta(timeframe)
    expiration = bar_start + valid_bars * delta
    logger.debug(
        "FR-ORDER-VALIDITY: Scheduled expiration bar_start=%s + %d * %s -> %s",
        bar_start,
        valid_bars,
        delta,
        expiration,
    )
    return expiration


__all__ = [
    "TIMEFRAME_PATTERNS",
    "parse_timeframe_delta",
    "schedule_bar_validity",
]
