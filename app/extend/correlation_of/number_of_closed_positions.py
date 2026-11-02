"""NumberOfClosedPositions correlation metric matching SQ CorrelationOf.

Description:
    Accumulates directional closed positions (+1 for long, -1 for short)
    bucketed by close time.
Purpose:
    FEAT-PORTFOLIO-MASTER: Provide multi-strategy correlation metrics.
Key Capabilities:
    - FR-correlation-closed-positions: Directional closed position counting per period.
Python API Usage:
    from app.extend.correlation_of.number_of_closed_positions import (
        NumberOfClosedPositions,
    )
    metric = NumberOfClosedPositions()
    buckets = metric.compute_periods(orders, "DAY")
CLI Usage:
    uv run python -m pytest tests/extend/test_correlation_of.py
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

from app.core.host.logging import get_logger
from app.extend.correlation_of.base import (
    DATA_TYPE_TRADES,
    CorrelationOrderRecord,
    CorrelationPeriod,
    CorrelationType,
    get_period_bucket,
)

logger = get_logger(__name__)


class NumberOfClosedPositions(CorrelationType):
    """Correlation metric counting net closed positions per period."""

    def __init__(self) -> None:
        """Initialize with display name and trades data type."""
        super().__init__(
            name="Number of closed positions",
            data_type=DATA_TYPE_TRADES,
        )

    @override
    def compute_periods(
        self,
        orders: Sequence[CorrelationOrderRecord],
        period: CorrelationPeriod,
        periods: dict[int, float] | None = None,
    ) -> dict[int, float]:
        """Accumulate net closed position counts (+1 for long, -1 for short).

        Args:
            orders: Sequence of order execution records.
            period: Temporal bucketing granularity.
            periods: Optional existing bucket dictionary to populate.

        Returns:
            Dictionary mapping period start ms to net position count.
        """
        buckets: dict[int, float] = {} if periods is None else periods
        for order in orders:
            if self.is_canceled_order(order):
                continue
            ms = get_period_bucket(order.close_time_ms, period)
            delta = 1.0 if order.is_long else -1.0
            buckets[ms] = buckets.get(ms, 0.0) + delta

        logger.debug(
            "NumberOfClosedPositions.compute_periods aggregated %d orders "
            "into %d buckets (period=%s)",
            len(orders),
            len(buckets),
            period,
        )
        return buckets
