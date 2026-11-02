"""Order scope matching, history order inspection, and price/time calculations.

Description:
    Provides domain types and pure utility functions for trade scope filtering,
    time-series bar offset calculation, pip size determination, and price
    normalization aligned with broker symbol tick increments, conforming to
    StrategyQuant SQ.Functions.OrderFunctions snippet specifications.
Purpose:
    FEAT-FUNCTIONS: StrategyQuant donor-faithful functions and domain utilities.
Key Capabilities:
    - FR-FUNCTIONS-ORDER-FILTER: Precise multi-attribute matching against orders.
    - FR-FUNCTIONS-PRICE-NORM: Tick grid alignment conforming to symbol specs.
    - FR-FUNCTIONS-BARS-SINCE: Count chart bar intervals between events.
Python API Usage:
    from app.extend.functions.order_functions import TradeFilter, normalize_price
CLI Usage:
    uv run pytest tests/extend/blocks/test_order_blocks.py --no-cov
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from itertools import pairwise

from app.core.data.contracts import OrderInfo, PositionInfo, SymbolInfo
from app.core.host.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class TradeFilter:
    """Explicit trading scope; None means any symbol/magic, direction 0 means either.

    Comments match by substring. A magic of zero matches zero exactly.
    Resolve strategy aliases such as Current before constructing this filter.
    """

    symbol: str | None
    direction: int = 0
    magic: int | None = None
    comment: str = ""
    ticket: int | None = None

    def __post_init__(self) -> None:
        """Validate the direction selector."""
        if type(self.direction) is not int or self.direction not in (-1, 0, 1):
            raise ValueError("direction must be -1, 0, or 1")

    def matches(self, item: PositionInfo | OrderInfo) -> bool:
        """Match one canonical position or working order without backend filtering."""
        kind = item.position_type if isinstance(item, PositionInfo) else item.order_type
        direction = 1 if kind in (0, 2, 4, 6) else -1
        return (
            (self.symbol is None or item.symbol == self.symbol)
            and (self.direction in (0, direction))
            and (self.magic is None or item.magic == self.magic)
            and (not self.comment or self.comment in item.comment)
            and (self.ticket is None or item.ticket == self.ticket)
        )


def aware_timestamp(value: datetime) -> float:
    """Validate an explicit evaluation timestamp and return epoch seconds."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("evaluation timestamps must include a timezone")
    return value.timestamp()


def bars_since(timestamp: float, bar_times: Sequence[datetime], as_of: datetime) -> int:
    """Count actual bar starts strictly after an event, bounded by evaluation time.

    Bars must be oldest first and cover the event. Missing history is an error.
    """
    end = aware_timestamp(as_of)
    starts = [aware_timestamp(value) for value in bar_times]
    if not starts or any(a >= b for a, b in pairwise(starts)):
        raise ValueError("bar times must be nonempty and strictly oldest first")
    if starts[-1] > end:
        raise ValueError("bar times must not extend past evaluation time")
    if timestamp > end:
        return -1
    if timestamp < starts[0]:
        raise ValueError("bar history does not cover the trade timestamp")
    count = sum(timestamp < start <= end for start in starts)
    logger.debug(
        "FR-FUNCTIONS-BARS-SINCE: Calculated %d bars since timestamp=%s as_of=%s",
        count,
        timestamp,
        as_of,
    )
    return count


def pip_size(price: float | None, tick_size: float) -> float:
    """Use an explicit pip size, falling back to the instrument tick size."""
    value = tick_size if price is None else price
    if not math.isfinite(value) or value <= 0:
        raise ValueError("pip size must be finite and positive")
    return value


def normalize_price(value: float, spec: SymbolInfo) -> float:
    """Validate a price and align it to the instrument tick grid."""
    if not math.isfinite(value) or value < 0:
        raise ValueError("prices must be finite and nonnegative")
    step = spec.price.tick_step
    if not math.isfinite(step) or step <= 0:
        raise ValueError("symbol tick step must be positive")
    grid = Decimal(str(step))
    rounded = float(round(Decimal(str(value)) / grid) * grid)
    if value > 0 and rounded <= 0:
        raise ValueError("positive price is smaller than the symbol tick step")
    logger.debug(
        "FR-FUNCTIONS-PRICE-NORM: Normalized price %s -> %s (tick_step=%s)",
        value,
        rounded,
        step,
    )
    return rounded


__all__ = [
    "TradeFilter",
    "aware_timestamp",
    "bars_since",
    "normalize_price",
    "pip_size",
]
