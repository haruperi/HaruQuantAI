"""NumberOfOpenPositions correlation metric matching SQ CorrelationOf.

Description:
    Accumulates directional open positions (+1 for long, -1 for short)
    across all periods overlapping an order's open and close times.
Purpose:
    FEAT-PORTFOLIO-MASTER: Provide multi-strategy correlation metrics.
Key Capabilities:
    - FR-correlation-open-positions: Directional open position counting per period.
Python API Usage:
    from app.extend.correlation_of.number_of_open_positions import (
        NumberOfOpenPositions,
    )
    metric = NumberOfOpenPositions()
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
    next_period_bucket,
)

logger = get_logger(__name__)


class NumberOfOpenPositions(CorrelationType):
    """Correlation metric counting net open positions across overlapping periods."""

    def __init__(self) -> None:
        """Initialize with display name and trades data type."""
        super().__init__(
            name="Number of open positions",
            data_type=DATA_TYPE_TRADES,
        )

    @override
    def compute_periods(
        self,
        orders: Sequence[CorrelationOrderRecord],
        period: CorrelationPeriod,
        periods: dict[int, float] | None = None,
    ) -> dict[int, float]:
        """Accumulate net open position counts (+1 for long, -1 for short).

        Args:
            orders: Sequence of order execution records.
            period: Temporal bucketing granularity.
            periods: Optional existing bucket dictionary to populate.

        Returns:
            Dictionary mapping period start ms to net open position count.
        """
        buckets: dict[int, float] = {} if periods is None else periods
        for order in orders:
            if self.is_canceled_order(order):
                continue

            delta = 1.0 if order.is_long else -1.0
            cur_b = get_period_bucket(order.open_time_ms, period)
            end_b = get_period_bucket(order.close_time_ms, period)

            while cur_b <= end_b:
                nxt_b = next_period_bucket(cur_b, period)
                if cur_b < order.close_time_ms and nxt_b >= order.open_time_ms:
                    buckets[cur_b] = buckets.get(cur_b, 0.0) + delta
                cur_b = nxt_b

        logger.debug(
            "NumberOfOpenPositions.compute_periods aggregated %d orders "
            "into %d buckets (period=%s)",
            len(orders),
            len(buckets),
            period,
        )
        return buckets
