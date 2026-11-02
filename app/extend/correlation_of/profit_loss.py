"""ProfitLoss correlation metric definition matching SQ CorrelationOf.ProfitLoss.

Description:
    Accumulates closed order profit/loss per period without non-loss period
    filtering.
Purpose:
    FEAT-PORTFOLIO-MASTER: Provide multi-strategy correlation metrics.
Key Capabilities:
    - FR-correlation-profit-loss: Cumulative profit/loss aggregation per period.
Python API Usage:
    from app.extend.correlation_of.profit_loss import ProfitLoss
    pl_metric = ProfitLoss()
    buckets = pl_metric.compute_periods(orders, "DAY")
CLI Usage:
    uv run python -m pytest tests/extend/test_correlation_of.py
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import override

from app.core.host.logging import get_logger
from app.extend.correlation_of.base import (
    DATA_TYPE_PL,
    CorrelationOrderRecord,
    CorrelationPeriod,
    CorrelationType,
    get_period_bucket,
)

logger = get_logger(__name__)


class ProfitLoss(CorrelationType):
    """Profit/Loss correlation metric aggregating signed order P/L per period."""

    def __init__(self) -> None:
        """Initialize Profit/Loss metric with display name and P/L data type."""
        super().__init__(name="Profit/Loss", data_type=DATA_TYPE_PL)

    @override
    def compute_periods(
        self,
        orders: Sequence[CorrelationOrderRecord],
        period: CorrelationPeriod,
        periods: dict[int, float] | None = None,
    ) -> dict[int, float]:
        """Accumulate closed order profit/loss into period buckets.

        Args:
            orders: Sequence of order execution records.
            period: Temporal bucketing granularity.
            periods: Optional existing bucket dictionary to populate.

        Returns:
            Dictionary mapping period start ms to cumulative profit/loss.
        """
        buckets: dict[int, float] = {} if periods is None else periods
        for order in orders:
            if self.is_canceled_order(order):
                continue
            ms = get_period_bucket(order.close_time_ms, period)
            buckets[ms] = buckets.get(ms, 0.0) + order.profit_loss

        logger.debug(
            "ProfitLoss.compute_periods aggregated %d orders into %d buckets"
            " (period=%s)",
            len(orders),
            len(buckets),
            period,
        )
        return buckets
