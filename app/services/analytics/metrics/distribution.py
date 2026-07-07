# ruff: noqa: ARG001, PLR2004, E501, DTZ006, RUF100
"""Distribution higher moments, outliers, and statistical correction (ANL-NFR-214)."""

from __future__ import annotations

import math
import random
from collections.abc import Sequence
from typing import Any

from app.services.analytics.contracts import MetricConfig, MetricResult
from app.services.analytics.metrics.equity_returns import (
    return_volatility,
)
from app.services.analytics.metrics.ratios import (
    _parse_returns,
)

type ReturnPoint = Any


def skewness(values: Sequence[float]) -> float:
    """Fisher-Pearson coefficient of skewness."""
    n = len(values)
    if n < 3:
        return 0.0
    mean = sum(values) / n
    std = math.sqrt(sum((x - mean) ** 2 for x in values) / (n - 1))
    if std == 0:
        return 0.0
    m3 = sum((x - mean) ** 3 for x in values) / n
    return m3 / (std**3)


def kurtosis(values: Sequence[float]) -> float:
    """Excess kurtosis."""
    n = len(values)
    if n < 4:
        return 0.0
    mean = sum(values) / n
    std = math.sqrt(sum((x - mean) ** 2 for x in values) / (n - 1))
    if std == 0:
        return 0.0
    m4 = sum((x - mean) ** 4 for x in values) / n
    return m4 / (std**4) - 3.0


def skewness_metric(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate returns skewness (ANL-NFR-214)."""
    ret_list = _parse_returns(returns)
    val = skewness(ret_list)
    return MetricResult(value=val)


def kurtosis_metric(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate returns excess kurtosis (ANL-NFR-215)."""
    ret_list = _parse_returns(returns)
    val = kurtosis(ret_list)
    return MetricResult(value=val)


def percentile_summary(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[dict[str, float]]:
    """Calculate standard percentile breaks (ANL-NFR-272)."""
    ret_list = _parse_returns(returns)
    if not ret_list:
        return MetricResult(value={})
    sorted_vals = sorted(ret_list)
    n = len(sorted_vals)
    percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    val = {}
    for p in percentiles:
        idx = min(int(n * (p / 100.0)), n - 1)
        val[f"{p}th"] = sorted_vals[idx]
    return MetricResult(value=val)


def upside_downside_summary(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[dict[str, Any]]:
    """Compare properties of gains versus losses (ANL-NFR-273)."""
    ret_list = _parse_returns(returns)
    upside = [x for x in ret_list if x > 0]
    downside = [x for x in ret_list if x < 0]
    avg_up = sum(upside) / len(upside) if upside else 0.0
    avg_down = sum(downside) / len(downside) if downside else 0.0
    val = {
        "upside_count": len(upside),
        "downside_count": len(downside),
        "average_upside": avg_up,
        "average_downside": avg_down,
    }
    return MetricResult(value=val)


def fat_tail_score(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate excess kurtosis as a proxy for tail thickness (ANL-NFR-274)."""
    ret_list = _parse_returns(returns)
    val = kurtosis(ret_list)
    return MetricResult(value=val)


def jarque_bera_test(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[dict[str, float]]:
    """Calculate Jarque-Bera statistic and its chi-squared p-value (ANL-NFR-275)."""
    ret_list = _parse_returns(returns)
    n = len(ret_list)
    if n < 4:
        return MetricResult(value={"jb_stat": 0.0, "p_value": 1.0})
    skew = skewness(ret_list)
    kurt = kurtosis(ret_list)
    jb_stat = (n / 6.0) * (skew**2 + (kurt**2 / 4.0))
    p_value = math.exp(-jb_stat / 2.0)
    val = {"jb_stat": jb_stat, "p_value": p_value}
    return MetricResult(value=val)


def jarque_bera_test_metric(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[dict[str, float]]:
    """Alias for jarque_bera_test (ANL-NFR-276)."""
    return jarque_bera_test(returns, config)


def bootstrap_metric(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Estimate a bootstrapped return metric exceeding a threshold (ANL-NFR-277)."""
    ret_list = _parse_returns(returns)
    if not ret_list:
        return MetricResult(value=0.0)
    threshold = float(config.metadata.get("threshold", 0.0) if config else 0.0)
    seed = int(config.metadata.get("seed", 42) if config else 42)
    rng = random.Random(seed)
    n = len(ret_list)
    success_count = 0
    iterations = int(config.metadata.get("iterations", 1000) if config else 1000)
    for _ in range(iterations):
        sample = [rng.choice(ret_list) for _ in range(n)]
        mean = sum(sample) / n
        if mean > threshold:
            success_count += 1
    val = success_count / iterations
    return MetricResult(value=val)


def false_discovery_rate(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[list[float]]:
    """Apply Benjamini-Hochberg FDR adjustments to p-values (ANL-NFR-278)."""
    p_values = config.metadata.get("p_values", [])
    n = len(p_values)
    if not p_values:
        return MetricResult(value=[])
    sorted_p = sorted(enumerate(p_values), key=lambda x: x[1])
    corrected = [0.0] * n
    for rank, (idx, p) in enumerate(sorted_p, 1):
        corrected[idx] = min(p * n / rank, 1.0)
    return MetricResult(value=corrected)


def distribution_summary(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[dict[str, float]]:
    """Expose general moments and percentile ranges (ANL-NFR-279)."""
    ret_list = _parse_returns(returns)
    if not ret_list:
        return MetricResult(value={})
    n = len(ret_list)
    mean = sum(ret_list) / n
    std = return_volatility(ret_list)
    val = {
        "mean": mean,
        "std": std,
        "skewness": skewness(ret_list),
        "kurtosis": kurtosis(ret_list),
    }
    return MetricResult(value=val)
