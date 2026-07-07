# ruff: noqa: ARG001, PLR2004, E501, DTZ006, RUF100
"""Distribution higher moments, outliers, and statistical correction (ANL-NFR-214)."""

from __future__ import annotations

import math
import random
from collections.abc import Sequence
from typing import Any

from app.services.analytics.contracts import MetricConfig, MetricResult
from app.services.analytics.metrics.equity import (
    return_volatility,
)
from app.services.analytics.metrics.ratios import (
    _parse_returns,
)
from app.utils.logger import logger

type ReturnPoint = Any


def skewness(values: Sequence[float]) -> float:
    """Fisher-Pearson coefficient of skewness.

    Args:
        values: Sequence of numeric values.

    Returns:
        Skewness coefficient as a float.
    """
    n = len(values)
    if n < 3:
        logger.debug("skewness: values length < 3, returning 0.0")
        return 0.0
    mean = sum(values) / n
    std = math.sqrt(sum((x - mean) ** 2 for x in values) / (n - 1))
    if std == 0:
        logger.debug("skewness: standard deviation is 0.0, returning 0.0")
        return 0.0
    m3 = sum((x - mean) ** 3 for x in values) / n
    res = m3 / (std**3)
    logger.debug(f"skewness: computed skewness: {res}")
    return res


def kurtosis(values: Sequence[float]) -> float:
    """Excess kurtosis.

    Args:
        values: Sequence of numeric values.

    Returns:
        Excess kurtosis as a float.
    """
    n = len(values)
    if n < 4:
        logger.debug("kurtosis: values length < 4, returning 0.0")
        return 0.0
    mean = sum(values) / n
    std = math.sqrt(sum((x - mean) ** 2 for x in values) / (n - 1))
    if std == 0:
        logger.debug("kurtosis: standard deviation is 0.0, returning 0.0")
        return 0.0
    m4 = sum((x - mean) ** 4 for x in values) / n
    res = m4 / (std**4) - 3.0
    logger.debug(f"kurtosis: computed excess kurtosis: {res}")
    return res


def skewness_metric(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate returns skewness (ANL-NFR-214).

    Args:
        returns: Sequence of returns.
        config: Metric configuration.

    Returns:
        MetricResult containing skewness.
    """
    logger.debug("skewness_metric: starting metric calculation.")
    ret_list = _parse_returns(returns)
    val = skewness(ret_list)
    logger.debug(f"skewness_metric: finished calculation, value: {val}")
    return MetricResult(value=val)


def kurtosis_metric(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate returns excess kurtosis (ANL-NFR-215).

    Args:
        returns: Sequence of returns.
        config: Metric configuration.

    Returns:
        MetricResult containing excess kurtosis.
    """
    logger.debug("kurtosis_metric: starting metric calculation.")
    ret_list = _parse_returns(returns)
    val = kurtosis(ret_list)
    logger.debug(f"kurtosis_metric: finished calculation, value: {val}")
    return MetricResult(value=val)


def percentile_summary(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[dict[str, float]]:
    """Calculate standard percentile breaks (ANL-NFR-272).

    Args:
        returns: Sequence of returns.
        config: Metric configuration.

    Returns:
        MetricResult containing percentile dictionary.
    """
    logger.debug("percentile_summary: starting metric calculation.")
    ret_list = _parse_returns(returns)
    if not ret_list:
        logger.debug("percentile_summary: empty returns, returning empty dict.")
        return MetricResult(value={})
    sorted_vals = sorted(ret_list)
    n = len(sorted_vals)
    percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    val = {}
    for p in percentiles:
        idx = min(int(n * (p / 100.0)), n - 1)
        val[f"{p}th"] = sorted_vals[idx]
    logger.debug(f"percentile_summary: computed percentiles: {val}")
    return MetricResult(value=val)


def upside_downside_summary(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[dict[str, Any]]:
    """Compare properties of gains versus losses (ANL-NFR-273).

    Args:
        returns: Sequence of returns.
        config: Metric configuration.

    Returns:
        MetricResult containing upside and downside count and average.
    """
    logger.debug("upside_downside_summary: starting metric calculation.")
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
    logger.debug(f"upside_downside_summary: finished calculation, summary: {val}")
    return MetricResult(value=val)


def fat_tail_score(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Calculate excess kurtosis as a proxy for tail thickness (ANL-NFR-274).

    Args:
        returns: Sequence of returns.
        config: Metric configuration.

    Returns:
        MetricResult containing fat tail score.
    """
    logger.debug("fat_tail_score: starting metric calculation.")
    ret_list = _parse_returns(returns)
    val = kurtosis(ret_list)
    logger.debug(f"fat_tail_score: finished calculation, value: {val}")
    return MetricResult(value=val)


def jarque_bera_test(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[dict[str, float]]:
    """Calculate Jarque-Bera statistic and its chi-squared p-value (ANL-NFR-275).

    Args:
        returns: Sequence of returns.
        config: Metric configuration.

    Returns:
        MetricResult containing Jarque-Bera statistic and p-value.
    """
    logger.debug("jarque_bera_test: starting metric calculation.")
    ret_list = _parse_returns(returns)
    n = len(ret_list)
    if n < 4:
        logger.debug("jarque_bera_test: returns count < 4, returning fallback.")
        return MetricResult(value={"jb_stat": 0.0, "p_value": 1.0})
    skew = skewness(ret_list)
    kurt = kurtosis(ret_list)
    jb_stat = (n / 6.0) * (skew**2 + (kurt**2 / 4.0))
    p_value = math.exp(-jb_stat / 2.0)
    val = {"jb_stat": jb_stat, "p_value": p_value}
    logger.debug(f"jarque_bera_test: finished calculation, values: {val}")
    return MetricResult(value=val)


def jarque_bera_test_metric(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[dict[str, float]]:
    """Alias for jarque_bera_test (ANL-NFR-276).

    Args:
        returns: Sequence of returns.
        config: Metric configuration.

    Returns:
        MetricResult containing Jarque-Bera statistic and p-value.
    """
    res = jarque_bera_test(returns, config)
    logger.debug("jarque_bera_test_metric: finished calculation.")
    return res


def bootstrap_metric(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[float]:
    """Estimate a bootstrapped return metric exceeding a threshold (ANL-NFR-277).

    Args:
        returns: Sequence of returns.
        config: Metric configuration.

    Returns:
        MetricResult containing probability.
    """
    logger.debug("bootstrap_metric: starting metric calculation.")
    ret_list = _parse_returns(returns)
    if not ret_list:
        logger.debug("bootstrap_metric: empty returns, returning 0.0.")
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
    logger.debug(f"bootstrap_metric: finished calculation, value: {val}")
    return MetricResult(value=val)


def false_discovery_rate(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[list[float]]:
    """Apply Benjamini-Hochberg FDR adjustments to p-values (ANL-NFR-278).

    Args:
        returns: Sequence of returns (not directly used here, p-values fetched from config metadata).
        config: Metric configuration.

    Returns:
        MetricResult containing list of corrected p-values.
    """
    logger.debug("false_discovery_rate: starting metric calculation.")
    p_values = config.metadata.get("p_values", [])
    n = len(p_values)
    if not p_values:
        logger.debug(
            "false_discovery_rate: no p_values configured, returning empty list."
        )
        return MetricResult(value=[])
    sorted_p = sorted(enumerate(p_values), key=lambda x: x[1])
    corrected = [0.0] * n
    for rank, (idx, p) in enumerate(sorted_p, 1):
        corrected[idx] = min(p * n / rank, 1.0)
    logger.debug(f"false_discovery_rate: computed corrected p-values of length {n}")
    return MetricResult(value=corrected)


def distribution_summary(
    returns: Sequence[ReturnPoint],
    config: MetricConfig,
) -> MetricResult[dict[str, float]]:
    """Expose general moments and percentile ranges (ANL-NFR-279).

    Args:
        returns: Sequence of returns.
        config: Metric configuration.

    Returns:
        MetricResult containing mean, std, skewness, and kurtosis.
    """
    logger.debug("distribution_summary: starting metric calculation.")
    ret_list = _parse_returns(returns)
    if not ret_list:
        logger.debug("distribution_summary: empty returns, returning empty dict.")
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
    logger.debug(f"distribution_summary: finished calculation, summary: {val}")
    return MetricResult(value=val)
