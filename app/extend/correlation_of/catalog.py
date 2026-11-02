"""CorrelationOf catalog, period bucketing, and Pearson correlation.

Description:
    Manages registered CorrelationType definitions (ProfitLoss, Loss,
    NumberOfClosedTrades, NumberOfOpenTrades, NumberOfClosedPositions,
    NumberOfOpenPositions), dispatches period bucketing, and performs
    pairwise Pearson correlation with definition-specific skip rules.
Purpose:
    FEAT-PORTFOLIO-MASTER: Provide multi-strategy correlation metrics.
Key Capabilities:
    - FR-master-correlation-periods: Bucket order sequences into UTC periods.
    - FR-master-correlation-pearson: Compute filtered Pearson correlation.
Python API Usage:
    from app.extend.correlation_of.catalog import (
        CorrelationOfCatalog,
        CorrelationOrderRecord,
    )
    periods = CorrelationOfCatalog.compute_periods("ProfitLoss", orders)
    r = CorrelationOfCatalog.pearson("ProfitLoss", series_a, series_b)
CLI Usage:
    uv run python -m pytest tests/extend/test_correlation_of.py
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from app.core.host.logging import get_logger
from app.extend.correlation_of.base import (
    CorrelationOrderRecord,
    CorrelationPeriod,
    CorrelationType,
    get_period_bucket,
    next_period_bucket,
)
from app.extend.correlation_of.loss import Loss
from app.extend.correlation_of.number_of_closed_positions import (
    NumberOfClosedPositions,
)
from app.extend.correlation_of.number_of_closed_trades import (
    NumberOfClosedTrades,
)
from app.extend.correlation_of.number_of_open_positions import (
    NumberOfOpenPositions,
)
from app.extend.correlation_of.number_of_open_trades import (
    NumberOfOpenTrades,
)
from app.extend.correlation_of.profit_loss import ProfitLoss

logger = get_logger(__name__)

# Maintain internal aliases for backward compatibility
_get_period_bucket = get_period_bucket
_next_period_bucket = next_period_bucket

_MIN_CORRELATION_PAIRS: int = 2
_EPSILON: float = 1e-12

_INSTANCES: dict[str, CorrelationType] = {
    "ProfitLoss": ProfitLoss(),
    "Loss": Loss(),
    "NumberOfClosedTrades": NumberOfClosedTrades(),
    "NumberOfOpenTrades": NumberOfOpenTrades(),
    "NumberOfClosedPositions": NumberOfClosedPositions(),
    "NumberOfOpenPositions": NumberOfOpenPositions(),
}

_SUPPORTED_DEFINITIONS: frozenset[str] = frozenset(_INSTANCES.keys())


class CorrelationOfCatalog:
    """Catalog managing CorrelationOf definitions and correlation logic."""

    @classmethod
    def definitions(cls) -> frozenset[str]:
        """Return registered correlation definition identifiers."""
        return _SUPPORTED_DEFINITIONS

    @classmethod
    def get_type(cls, definition_id: str) -> CorrelationType:
        """Resolve a CorrelationType instance by definition identifier.

        Args:
            definition_id: Identifier corresponding to the correlation metric.

        Returns:
            Resolved CorrelationType instance.

        Raises:
            ValueError: If definition_id is not registered.
        """
        instance = _INSTANCES.get(definition_id)
        if instance is None:
            raise ValueError(f"Unknown correlation definition: {definition_id}")
        return instance

    @classmethod
    def compute_periods(
        cls,
        definition_id: str,
        orders: Sequence[CorrelationOrderRecord],
        *,
        period: CorrelationPeriod = "DAY",
    ) -> dict[int, float]:
        """Bucket order sequences into UTC periods by definition rules.

        Args:
            definition_id: One of the six registered definitions.
            orders: Sequence of candidate order records.
            period: Temporal bucketing granularity.

        Returns:
            Dictionary mapping period start epoch ms to aggregated float metric.

        Raises:
            ValueError: If definition_id is unknown.
        """
        metric = cls.get_type(definition_id)
        buckets = metric.compute_periods(orders, period=period)
        logger.debug(
            "Computed %d period buckets for definition '%s' (period=%s)",
            len(buckets),
            definition_id,
            period,
        )
        return buckets

    @classmethod
    def pearson(
        cls,
        definition_id: str,
        series_a: Mapping[int, float],
        series_b: Mapping[int, float],
        *,
        allow_empty_periods: bool = False,
    ) -> float:
        """Compute Pearson correlation with definition-specific skip rules.

        Args:
            definition_id: Method identifier governing skip rules.
            series_a: First series mapping bucket start ms to metric float.
            series_b: Second series mapping bucket start ms to metric float.
            allow_empty_periods: Whether (0.0, 0.0) periods are retained.

        Returns:
            Pearson correlation in [-1.0, 1.0] rounded to 4 decimals (or 0.0).
        """
        metric = cls.get_type(definition_id)
        all_keys = sorted(set(series_a.keys()) | set(series_b.keys()))
        pairs: list[tuple[float, float]] = []

        for k in all_keys:
            val_a = series_a.get(k, 0.0)
            val_b = series_b.get(k, 0.0)

            # Skip rules per definition
            if metric.should_skip_period(val_a, val_b):
                continue
            if not allow_empty_periods and val_a == 0.0 and val_b == 0.0:
                continue

            pairs.append((val_a, val_b))

        if len(pairs) < _MIN_CORRELATION_PAIRS:
            return 0.0

        n = len(pairs)
        sum_a = sum(p[0] for p in pairs)
        sum_b = sum(p[1] for p in pairs)
        mean_a = sum_a / n
        mean_b = sum_b / n

        cov = sum((p[0] - mean_a) * (p[1] - mean_b) for p in pairs)
        var_a = sum((p[0] - mean_a) ** 2 for p in pairs)
        var_b = sum((p[1] - mean_b) ** 2 for p in pairs)

        if var_a <= _EPSILON or var_b <= _EPSILON:
            return 0.0

        denom = math.sqrt(var_a * var_b)
        r = cov / denom
        r_clamped = max(-1.0, min(1.0, r))
        res = round(r_clamped, 4)
        return 0.0 if res == -0.0 else res
