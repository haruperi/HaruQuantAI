"""Cataloged moments, percentiles, tails, histogram, and outlier evidence."""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np

from app.services.analytics.contracts.errors import AnalyticsValidationError
from app.services.analytics.contracts.evidence import build_warning
from app.services.analytics.contracts.models import (
    AnalyticsRunConfig,
    MetricEvidence,
    SectionEvidence,
)
from app.utils import logger

_STDEV_MIN_SAMPLES = 2
_SKEW_MIN_SAMPLES = 3
_KURTOSIS_MIN_SAMPLES = 4


def _metric(metric_key: str, value: object, unit: str = "ratio") -> MetricEvidence:
    """Build calculated distribution evidence.

    Args:
        metric_key: Catalog metric key.
        value: Finite calculated value.
        unit: Catalog unit.

    Returns:
        Calculated metric evidence.
    """
    logger.debug("Building Analytics distribution metric evidence")
    return MetricEvidence(
        metric_key=metric_key,
        status="calculated",
        value=value,
        unit=unit,
    )


def _undefined(metric_key: str, *, config: AnalyticsRunConfig) -> MetricEvidence:
    """Build explicit zero-variance distribution evidence.

    Args:
        metric_key: Catalog metric key.
        config: Required Analytics bounds supplying the warning detail bound.

    Returns:
        Undefined metric evidence.
    """
    logger.debug("Building undefined Analytics distribution evidence")
    warning = build_warning(
        "undefined_zero_variance",
        section="distribution",
        source_context="sample",
        detail={"metric_key": metric_key, "series_name": "values"},
        max_detail_bytes=config.max_warning_detail_bytes,
    )
    return MetricEvidence(
        metric_key=metric_key,
        status="undefined",
        value=None,
        unit="ratio",
        warnings=(warning,),
    )


def _skipped(
    metric_key: str,
    *,
    unit: str,
    config: AnalyticsRunConfig,
) -> MetricEvidence:
    """Build explicit constant-sample skipped evidence.

    Args:
        metric_key: Catalog metric key.
        unit: Catalog unit.
        config: Required Analytics bounds supplying the warning detail bound.

    Returns:
        Skipped metric evidence.
    """
    logger.debug("Building skipped Analytics distribution evidence")
    warning = build_warning(
        "undefined_zero_variance",
        section="distribution",
        source_context="sample",
        detail={"metric_key": metric_key, "series_name": "values"},
        max_detail_bytes=config.max_warning_detail_bytes,
    )
    return MetricEvidence(
        metric_key=metric_key,
        status="skipped",
        value=None,
        unit=unit,
        warnings=(warning,),
    )


def _moments(values: np.ndarray) -> tuple[float | None, float | None]:
    """Calculate bias-corrected G1 skewness and excess G2 kurtosis.

    Args:
        values: Finite sample array.

    Returns:
        Optional skewness and excess kurtosis.
    """
    logger.debug("Calculating Analytics distribution moments")
    count = len(values)
    stdev = float(np.std(values, ddof=1)) if count >= _STDEV_MIN_SAMPLES else 0.0
    if stdev == 0:
        return None, None
    centered = values - float(np.mean(values))
    m2 = float(np.mean(centered**2))
    m3 = float(np.mean(centered**3))
    m4 = float(np.mean(centered**4))
    skew = (
        math.sqrt(count * (count - 1)) / (count - 2) * (m3 / m2**1.5)
        if count >= _SKEW_MIN_SAMPLES
        else None
    )
    kurtosis = (
        ((count - 1) / ((count - 2) * (count - 3)))
        * ((count + 1) * (m4 / m2**2 - 3) + 6)
        if count >= _KURTOSIS_MIN_SAMPLES
        else None
    )
    return skew, kurtosis


def calculate_distribution_evidence(
    values: Sequence[float],
    *,
    config: AnalyticsRunConfig,
) -> SectionEvidence:
    """Calculate the single approved distribution evidence set.

    Args:
        values: Finite numeric observations.
        config: Required Analytics bounds supplying the warning detail bound.

    Returns:
        Ordered distribution section evidence.

    Raises:
        AnalyticsValidationError: If observations are empty or non-finite.
    """
    logger.info("Calculating Analytics distribution evidence")
    array = np.asarray(tuple(values), dtype=np.float64)
    if not len(array) or not np.all(np.isfinite(array)):
        raise AnalyticsValidationError(
            "distribution values must be non-empty and finite"
        )
    mean = float(np.mean(array))
    stdev = float(np.std(array, ddof=1)) if len(array) >= _STDEV_MIN_SAMPLES else None
    skewness, kurtosis = _moments(array)
    quantiles = np.quantile(
        array,
        (0.01, 0.05, 0.10, 0.25, 0.5, 0.75, 0.90, 0.95, 0.99),
        method="linear",
    )
    percentile_values = {
        key: float(value)
        for key, value in zip(
            ("p01", "p05", "p10", "p25", "p50", "p75", "p90", "p95", "p99"),
            quantiles,
            strict=True,
        )
    }
    lower = abs(percentile_values["p05"])
    tail_ratio = percentile_values["p95"] / lower if lower > 0 else None
    if float(np.min(array)) == float(np.max(array)):
        histogram: object | None = None
    else:
        counts, edges = np.histogram(array, bins=50)
        histogram = {
            "edges": tuple(float(item) for item in edges),
            "counts": tuple(int(item) for item in counts),
        }
    q1, q3 = np.quantile(array, (0.25, 0.75), method="linear")
    iqr = float(q3 - q1)
    low_fence = float(q1) - 1.5 * iqr
    high_fence = float(q3) + 1.5 * iqr
    outliers = int(np.count_nonzero((array < low_fence) | (array > high_fence)))
    metrics = (
        _metric("mean", mean),
        _metric("stdev", stdev)
        if stdev is not None
        else _undefined("stdev", config=config),
        _metric("skewness", skewness)
        if skewness is not None
        else _undefined("skewness", config=config),
        _metric("kurtosis", kurtosis)
        if kurtosis is not None
        else _undefined("kurtosis", config=config),
        _metric("percentiles", percentile_values),
        _metric("tail_ratio", tail_ratio)
        if tail_ratio is not None
        else _undefined("tail_ratio", config=config),
        _metric("histogram", histogram, "count")
        if histogram is not None
        else _skipped("histogram", unit="count", config=config),
        _metric("outliers", outliers, "count"),
    )
    warnings = tuple(warning for metric in metrics for warning in metric.warnings)
    return SectionEvidence(
        section_key="distribution",
        criticality="optional",
        metrics=metrics,
        status="degraded" if warnings else "completed",
        warnings=warnings,
    )


__all__ = ["calculate_distribution_evidence"]
