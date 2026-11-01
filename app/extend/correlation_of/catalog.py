"""CorrelationOf catalog, period bucketing, and Pearson correlation.

Description:
    Computes period-bucketed metrics across six definitions (ProfitLoss,
    Loss, NumberOfClosedTrades, NumberOfOpenTrades, NumberOfClosedPositions,
    NumberOfOpenPositions) and performs pairwise Pearson correlation with
    definition-specific skipping logic.
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
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

from app.core.host.logging import get_logger

logger = get_logger(__name__)

CorrelationPeriod = Literal["HOUR", "DAY", "WEEK", "MONTH", "YEAR"]

_SUPPORTED_DEFINITIONS: frozenset[str] = frozenset(
    {
        "ProfitLoss",
        "Loss",
        "NumberOfClosedTrades",
        "NumberOfOpenTrades",
        "NumberOfClosedPositions",
        "NumberOfOpenPositions",
    }
)

_DECEMBER: int = 12
_MIN_CORRELATION_PAIRS: int = 2
_EPSILON: float = 1e-12


@dataclass(frozen=True, slots=True)
class CorrelationOrderRecord:
    """Historical or candidate order execution record for correlation."""

    open_time_ms: int
    close_time_ms: int
    profit_loss: float
    is_canceled: bool = False
    is_open_position: bool = False
    is_long: bool = True


def _get_period_bucket(t_ms: int, period: CorrelationPeriod) -> int:
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


def _next_period_bucket(bucket_ms: int, period: CorrelationPeriod) -> int:
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


class CorrelationOfCatalog:
    """Catalog managing CorrelationOf definitions and correlation logic."""

    @classmethod
    def definitions(cls) -> frozenset[str]:
        """Return registered correlation definition identifiers."""
        return _SUPPORTED_DEFINITIONS

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
        if definition_id not in _SUPPORTED_DEFINITIONS:
            raise ValueError(f"Unknown correlation definition: {definition_id}")

        buckets: dict[int, float] = {}
        for order in orders:
            if order.is_canceled:
                continue

            if definition_id in {
                "ProfitLoss",
                "Loss",
                "NumberOfClosedTrades",
                "NumberOfClosedPositions",
            }:
                cls._accumulate_closed(definition_id, order, period, buckets)
            elif definition_id in {
                "NumberOfOpenTrades",
                "NumberOfOpenPositions",
            }:
                cls._accumulate_open(definition_id, order, period, buckets)

        logger.debug(
            "Computed %d period buckets for definition '%s' (period=%s)",
            len(buckets),
            definition_id,
            period,
        )
        return buckets

    @classmethod
    def _accumulate_closed(
        cls,
        definition_id: str,
        order: CorrelationOrderRecord,
        period: CorrelationPeriod,
        buckets: dict[int, float],
    ) -> None:
        """Accumulate an event based on order close time."""
        b_ms = _get_period_bucket(order.close_time_ms, period)
        current = buckets.get(b_ms, 0.0)

        if definition_id in {"ProfitLoss", "Loss"}:
            buckets[b_ms] = current + order.profit_loss
        elif definition_id == "NumberOfClosedTrades":
            buckets[b_ms] = current + 1.0
        elif definition_id == "NumberOfClosedPositions":
            delta = 1.0 if order.is_long else -1.0
            buckets[b_ms] = current + delta

    @classmethod
    def _accumulate_open(
        cls,
        definition_id: str,
        order: CorrelationOrderRecord,
        period: CorrelationPeriod,
        buckets: dict[int, float],
    ) -> None:
        """Accumulate an event across overlapping active order periods."""
        cur_b = _get_period_bucket(order.open_time_ms, period)
        end_b = _get_period_bucket(order.close_time_ms, period)

        while cur_b <= end_b:
            next_b = _next_period_bucket(cur_b, period)
            # Overlap: cur_b < close_time_ms and next_b >= open_time_ms
            if cur_b < order.close_time_ms and next_b >= order.open_time_ms:
                current = buckets.get(cur_b, 0.0)
                if definition_id == "NumberOfOpenTrades":
                    buckets[cur_b] = current + 1.0
                elif definition_id == "NumberOfOpenPositions":
                    delta = 1.0 if order.is_long else -1.0
                    buckets[cur_b] = current + delta
            cur_b = next_b

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
        all_keys = sorted(set(series_a.keys()) | set(series_b.keys()))
        pairs: list[tuple[float, float]] = []

        for k in all_keys:
            val_a = series_a.get(k, 0.0)
            val_b = series_b.get(k, 0.0)

            # Skip rules per definition
            if definition_id == "Loss" and val_a >= 0.0 and val_b >= 0.0:
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
