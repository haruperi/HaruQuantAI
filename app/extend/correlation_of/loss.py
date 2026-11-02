"""Loss correlation metric definition matching SQ CorrelationOf.Loss.

Description:
    Accumulates closed order profit/loss per period and skips periods where
    neither strategy experienced a loss (both values >= 0.0).
Purpose:
    FEAT-PORTFOLIO-MASTER: Provide multi-strategy correlation metrics.
Key Capabilities:
    - FR-correlation-loss: Loss metric accumulation and no-loss period filtering.
Python API Usage:
    from app.extend.correlation_of.loss import Loss
    loss_metric = Loss()
    buckets = loss_metric.compute_periods(orders, "DAY")
    skip = loss_metric.should_skip_period(10.0, 20.0)
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


class Loss(CorrelationType):
    """Loss correlation metric aggregating P/L and filtering non-loss periods."""

    def __init__(self) -> None:
        """Initialize Loss metric with display name and P/L data type."""
        super().__init__(name="Loss", data_type=DATA_TYPE_PL)

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
            "Loss.compute_periods aggregated %d orders into %d buckets (period=%s)",
            len(orders),
            len(buckets),
            period,
        )
        return buckets

    @override
    def should_skip_period(self, value1: float, value2: float) -> bool:
        """Skip periods where both strategies had no losses (both values >= 0.0)."""
        return value1 >= 0.0 and value2 >= 0.0
