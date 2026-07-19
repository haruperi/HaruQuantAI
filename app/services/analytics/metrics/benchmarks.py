"""UTC-aware benchmark alignment and relative performance evidence."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from decimal import Decimal

import numpy as np

from app.services.analytics.contracts.errors import AnalyticsValidationError
from app.services.analytics.contracts.models import (
    AnalyticsRunConfig,
    AnalyticsWarning,
    MetricEvidence,
    SectionEvidence,
    TradingResult,
)
from app.services.analytics.metrics.trades import (
    ANNUALIZATION_POLICY,
    MIN_METRIC_SAMPLES,
)
from app.utils import logger

_VARIANCE_MIN_SAMPLES = MIN_METRIC_SAMPLES["variance"]
_ALPHA_MIN_SAMPLES = MIN_METRIC_SAMPLES["tail"]


def _point_map(
    points: Sequence[Mapping[str, object]],
) -> tuple[dict[datetime, float], int]:
    """Normalize finite UTC point mappings with deterministic last-wins duplicates.

    Args:
        points: Timestamp/value point mappings.

    Returns:
        Timestamp-value mapping and duplicate count.

    Raises:
        AnalyticsValidationError: If point shape or values are invalid.
    """
    logger.debug("Normalizing Analytics benchmark points")
    normalized: dict[datetime, float] = {}
    duplicates = 0
    for point in points:
        timestamp = point.get("timestamp")
        value = point.get("value")
        if not isinstance(timestamp, datetime):
            raise AnalyticsValidationError("benchmark timestamp must be datetime")
        if timestamp.tzinfo is None or timestamp.utcoffset() != timedelta(0):
            raise AnalyticsValidationError("benchmark timestamp must be UTC")
        if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise AnalyticsValidationError("benchmark value must be finite")
        duplicates += int(timestamp in normalized)
        normalized[timestamp] = float(value)
    return normalized, duplicates


def align_benchmark_series(
    strategy: Sequence[Mapping[str, object]],
    benchmark: Sequence[Mapping[str, object]],
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """Align strategy and benchmark observations on their UTC intersection.

    Args:
        strategy: Strategy timestamp/value observations.
        benchmark: Benchmark timestamp/value observations.

    Returns:
        Aligned strategy and benchmark value tuples.

    Raises:
        AnalyticsValidationError: If timestamps, values, or overlap are invalid.
    """
    logger.info("Aligning Analytics benchmark series")
    strategy_map, _ = _point_map(strategy)
    benchmark_map, _ = _point_map(benchmark)
    intersection = tuple(sorted(set(strategy_map) & set(benchmark_map)))
    if not intersection:
        raise AnalyticsValidationError("benchmark series have no UTC overlap")
    return (
        tuple(strategy_map[timestamp] for timestamp in intersection),
        tuple(benchmark_map[timestamp] for timestamp in intersection),
    )


def _strategy_points(result: TradingResult) -> tuple[Mapping[str, object], ...]:
    """Derive timestamped daily strategy returns.

    Args:
        result: Canonical Analytics input.

    Returns:
        Timestamp/value daily return points.

    Raises:
        AnalyticsValidationError: If a daily equity point has invalid types.
    """
    logger.debug("Deriving Analytics benchmark strategy points")
    previous = result.initial_balance
    points: list[Mapping[str, object]] = []
    for point in result.daily_equity_curve:
        timestamp = point["timestamp"]
        equity = point["equity"]
        if not isinstance(timestamp, datetime) or not isinstance(equity, Decimal):
            raise AnalyticsValidationError("daily equity point is invalid")
        value = float((equity - previous) / previous)
        points.append({"timestamp": timestamp, "value": value})
        previous = equity
    return tuple(points)


def _metric(metric_key: str, value: float | None) -> MetricEvidence:
    """Build calculated or undefined benchmark evidence.

    Args:
        metric_key: Catalog metric key.
        value: Optional calculated ratio.

    Returns:
        Benchmark metric evidence.
    """
    logger.debug("Building Analytics benchmark metric evidence")
    warnings: tuple[AnalyticsWarning, ...] = ()
    if value is None:
        warnings = (
            AnalyticsWarning(
                code="undefined_zero_variance",
                severity="warning",
                affected_section="benchmark",
                source_context="aligned",
                detail={"metric_key": metric_key, "series_name": "benchmark"},
            ),
        )
    return MetricEvidence(
        metric_key=metric_key,
        status="calculated" if value is not None else "undefined",
        value=value,
        unit="ratio",
        warnings=warnings,
        source_context="benchmark",
    )


def calculate_benchmark_evidence(
    result: TradingResult,
    *,
    config: AnalyticsRunConfig,
) -> SectionEvidence:
    """Calculate aligned benchmark-relative evidence.

    Args:
        result: Canonical Analytics input carrying benchmark evidence.
        config: Required risk-free and point bounds.

    Returns:
        Ordered benchmark section evidence.

    Raises:
        AnalyticsValidationError: If benchmark, currency, or risk-free evidence fails.
    """
    logger.info("Calculating Analytics benchmark-relative evidence")
    if result.benchmark is None:
        raise AnalyticsValidationError("benchmark evidence is required")
    if config.risk_free_rate is None:
        raise AnalyticsValidationError("risk-free-rate evidence is required")
    benchmark_currency = result.benchmark.get("currency")
    if benchmark_currency != result.account_currency and result.fx_evidence is None:
        raise AnalyticsValidationError(
            "benchmark currency conversion evidence is missing"
        )
    raw_points = result.benchmark.get("points")
    if not isinstance(raw_points, Sequence) or isinstance(raw_points, (str, bytes)):
        raise AnalyticsValidationError("benchmark points are invalid")
    points = tuple(point for point in raw_points if isinstance(point, Mapping))
    if len(points) != len(raw_points) or len(points) > config.max_benchmark_points:
        raise AnalyticsValidationError("benchmark point shape or bound is invalid")
    strategy_values, benchmark_values = align_benchmark_series(
        _strategy_points(result), points
    )
    strategy_array = np.asarray(strategy_values, dtype=np.float64)
    benchmark_array = np.asarray(benchmark_values, dtype=np.float64)
    variance = (
        float(np.var(benchmark_array, ddof=1))
        if len(benchmark_array) >= _VARIANCE_MIN_SAMPLES
        else 0.0
    )
    beta = (
        float(np.cov(strategy_array, benchmark_array, ddof=1)[0, 1] / variance)
        if variance > 0
        else None
    )
    annualization_days = ANNUALIZATION_POLICY["trading_days"]
    daily_risk_free = float(config.risk_free_rate.rate) / annualization_days
    alpha = (
        float(
            np.mean(strategy_array)
            - daily_risk_free
            - beta * (np.mean(benchmark_array) - daily_risk_free)
        )
        * annualization_days
        if beta is not None and len(strategy_array) >= _ALPHA_MIN_SAMPLES
        else None
    )
    correlation = (
        float(np.corrcoef(strategy_array, benchmark_array)[0, 1])
        if variance > 0 and float(np.var(strategy_array, ddof=1)) > 0
        else None
    )
    active = strategy_array - benchmark_array
    tracking_error = (
        float(np.std(active, ddof=1) * math.sqrt(annualization_days))
        if len(active) >= _VARIANCE_MIN_SAMPLES
        else None
    )
    information_ratio = (
        float(np.mean(active) / np.std(active, ddof=1) * math.sqrt(annualization_days))
        if tracking_error not in {None, 0.0}
        else None
    )
    metrics = tuple(
        _metric(key, value)
        for key, value in (
            ("benchmark_alpha", alpha),
            ("benchmark_beta", beta),
            ("benchmark_correlation", correlation),
            ("tracking_error", tracking_error),
            ("information_ratio", information_ratio),
        )
    )
    warnings = tuple(warning for metric in metrics for warning in metric.warnings)
    return SectionEvidence(
        section_key="benchmark",
        criticality="optional",
        metrics=metrics,
        status="degraded" if warnings else "completed",
        warnings=warnings,
    )


__all__ = ["align_benchmark_series", "calculate_benchmark_evidence"]
