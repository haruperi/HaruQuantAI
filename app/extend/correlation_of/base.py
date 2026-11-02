"""Base classes and types for CorrelationOf snippets.

Description:
    Provides the abstract base CorrelationType, time bucketing helpers,
    and foundational record types matching the StrategyQuant SQ.CorrelationOf
    framework.
Purpose:
    FEAT-PORTFOLIO-MASTER: Provide multi-strategy correlation metrics.
Key Capabilities:
    - FR-correlation-base: Base correlation snippet protocol and temporal bucketing.
Python API Usage:
    from app.extend.correlation_of.base import (
        CorrelationType,
        CorrelationOrderRecord,
        CorrelationPeriod,
        DATA_TYPE_PL,
        DATA_TYPE_TRADES,
    )
CLI Usage:
    uv run python -m pytest tests/extend/test_correlation_of.py
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

from app.core.host.logging import get_logger

logger = get_logger(__name__)

CorrelationPeriod = Literal["HOUR", "DAY", "WEEK", "MONTH", "YEAR"]

DATA_TYPE_PL: str = "PL"
DATA_TYPE_TRADES: str = "TRADES"

_DECEMBER: int = 12


@dataclass(frozen=True, slots=True)
class CorrelationOrderRecord:
    """Historical or candidate order execution record for correlation."""

    open_time_ms: int
    close_time_ms: int
    profit_loss: float
    is_canceled: bool = False
    is_open_position: bool = False
    is_long: bool = True


@dataclass(slots=True)
class TimePeriod:
    """Represents a time period bucket with temporal bounds and metric value."""

    from_ms: int
    to_ms: int
    value: float = 0.0


def get_period_bucket(t_ms: int, period: CorrelationPeriod) -> int:
    """Return UTC period start epoch milliseconds for given timestamp."""
    dt = datetime.fromtimestamp(t_ms / 1000.0, tz=UTC)
    if period == "HOUR":
        b_dt = dt.replace(minute=0, second=0, microsecond=0)
    elif period == "DAY":
        b_dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "WEEK":
        b_dt = (dt - timedelta(days=dt.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    elif period == "MONTH":
        b_dt = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "YEAR":
        b_dt = dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        raise ValueError(f"Unknown correlation period: {period}")
    return int(b_dt.timestamp() * 1000)


def next_period_bucket(bucket_ms: int, period: CorrelationPeriod) -> int:
    """Return next UTC period start epoch milliseconds."""
    dt = datetime.fromtimestamp(bucket_ms / 1000.0, tz=UTC)
    if period == "HOUR":
        n_dt = dt + timedelta(hours=1)
    elif period == "DAY":
        n_dt = dt + timedelta(days=1)
    elif period == "WEEK":
        n_dt = dt + timedelta(weeks=1)
    elif period == "MONTH":
        year = dt.year + (1 if dt.month == _DECEMBER else 0)
        month = 1 if dt.month == _DECEMBER else dt.month + 1
        n_dt = dt.replace(year=year, month=month, day=1)
    elif period == "YEAR":
        n_dt = dt.replace(year=dt.year + 1, month=1, day=1)
    else:
        raise ValueError(f"Unknown correlation period: {period}")
    return int(n_dt.timestamp() * 1000)


class CorrelationType(ABC):
    """Abstract base class for correlation series metrics.

    Matches StrategyQuant SQ CorrelationType.
    """

    def __init__(self, name: str, data_type: str) -> None:
        """Initialize correlation type descriptor with display name and data type."""
        self.name: str = name
        self.data_type: str = data_type
        logger.debug(
            "Initialized CorrelationType name=%s data_type=%s",
            self.name,
            self.data_type,
        )

    def is_canceled_order(self, order: CorrelationOrderRecord) -> bool:
        """Return True if order is canceled and should be skipped."""
        return order.is_canceled

    def should_skip_period(self, value1: float, value2: float) -> bool:
        """Return True if period comparison should be skipped in Pearson correlation."""
        _ = (value1, value2)
        return False

    @abstractmethod
    def compute_periods(
        self,
        orders: Sequence[CorrelationOrderRecord],
        period: CorrelationPeriod,
        periods: dict[int, float] | None = None,
    ) -> dict[int, float]:
        """Aggregate order sequence into period buckets.

        Args:
            orders: Sequence of order records.
            period: Granularity identifier.
            periods: Optional initial dictionary mapping period start ms to float value.

        Returns:
            Dictionary mapping period start epoch ms to aggregated float metric.
        """
        ...
