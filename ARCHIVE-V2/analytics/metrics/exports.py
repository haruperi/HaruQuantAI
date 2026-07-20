# ruff: noqa: ARG001, PLR2004, E501, DTZ006, RUF100
"""Compatibility aliases resolving name collisions across modules (ANL-NFR-016)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from app.services.analytics.contracts import MetricConfig, MetricResult
from app.utils.logger import logger

type TradeRecord = dict[str, Any]
type ReturnPoint = Any


def common_avg_loss(
    input_value: object,
    config: MetricConfig,
) -> MetricResult[float]:
    """Expose common-module average-loss behavior without collision (ANL-NFR-016).

    Args:
        input_value (object): Input value or sequence of values.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("common_avg_loss: executed.")
    from app.services.analytics.metrics.trade_outcomes import avg_loss

    trades = input_value if isinstance(input_value, Sequence) else ()
    return avg_loss(trades, config)


def common_get_r_multiples(
    input_value: object,
    config: MetricConfig,
) -> MetricResult[tuple[float, ...]]:
    """Expose common-module R-multiple behavior without collision (ANL-NFR-017).

    Args:
        input_value (object): Input value or sequence of values.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated tuple[float, ... value.
    """
    logger.debug("common_get_r_multiples: executed.")
    from app.services.analytics.metrics.r_multiples import get_r_multiples

    trades = input_value if isinstance(input_value, Sequence) else ()
    res, _ = get_r_multiples(trades, config)
    return MetricResult(value=tuple(res))


def metrics_get_r_multiples(
    input_value: object,
    config: MetricConfig,
) -> MetricResult[tuple[float, ...]]:
    """Expose metrics-module R-multiple behavior without collision (ANL-NFR-020).

    Args:
        input_value (object): Input value or sequence of values.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated tuple[float, ... value.
    """
    logger.debug("metrics_get_r_multiples: executed.")
    return common_get_r_multiples(input_value, config)


def metrics_avg_loss(
    input_value: object,
    config: MetricConfig,
) -> MetricResult[float]:
    """Expose metrics-module average-loss behavior without collision (ANL-NFR-029).

    Args:
        input_value (object): Input value or sequence of values.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("metrics_avg_loss: executed.")
    from app.services.analytics.metrics.trade_outcomes import avg_loss_metric

    trades = input_value if isinstance(input_value, Sequence) else ()
    return avg_loss_metric(trades, config)


def benchmark_information_ratio(
    input_value: object,
    config: MetricConfig,
) -> MetricResult[float]:
    """Expose benchmark information ratio without colliding with ratios module export (ANL-NFR-281).

    Args:
        input_value (object): Input value or sequence of values.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("benchmark_information_ratio: executed.")
    from app.services.analytics.metrics.ratios import information_ratio

    returns = input_value if isinstance(input_value, Sequence) else ()
    return information_ratio(returns, config)


def metrics_win_rate_fraction(
    input_value: object,
    config: MetricConfig,
) -> MetricResult[float]:
    """Expose metrics-module win-rate fraction behavior without ratios collision (ANL-NFR-283).

    Args:
        input_value (object): Input value or sequence of values.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("metrics_win_rate_fraction: executed.")
    from app.services.analytics.metrics.trade_outcomes import win_rate_fraction

    trades = input_value if isinstance(input_value, Sequence) else ()
    return win_rate_fraction(trades, config)


def metrics_expectancy_r(
    input_value: object,
    config: MetricConfig,
) -> MetricResult[float]:
    """Expose metrics-module R-expectancy behavior without ratios collision (ANL-NFR-284).

    Args:
        input_value (object): Input value or sequence of values.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("metrics_expectancy_r: executed.")
    from app.services.analytics.metrics.trade_outcomes import expectancy_r

    trades = input_value if isinstance(input_value, Sequence) else ()
    return expectancy_r(trades, config)


def ratios_information_ratio(
    input_value: object,
    config: MetricConfig,
) -> MetricResult[float]:
    """Expose ratios-module information ratio without benchmark collision (ANL-NFR-288).

    Args:
        input_value (object): Input value or sequence of values.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated float value.
    """
    logger.debug("ratios_information_ratio: executed.")
    return benchmark_information_ratio(input_value, config)


def distributions_r_multiple_distribution(
    input_value: object,
    config: MetricConfig,
) -> MetricResult[dict[str, float]]:
    """Expose distribution-module R-multiple distribution behavior without collision (ANL-NFR-318).

    Args:
        input_value (object): Input value or sequence of values.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated dict[str, float value.
    """
    logger.debug("distributions_r_multiple_distribution: executed.")
    trades = input_value if isinstance(input_value, Sequence) else ()
    from app.services.analytics.metrics.r_multiples import get_r_multiples

    r_multiples, _ = get_r_multiples(trades, config)
    from app.services.analytics.metrics.distribution import distribution_summary

    return distribution_summary(r_multiples, config)


def metrics_r_multiple_distribution(
    input_value: object,
    config: MetricConfig,
) -> MetricResult[dict[str, float]]:
    """Calculate R-multiple distribution statistics (ANL-NFR-339).

    Args:
        input_value (object): Input value or sequence of values.
        config (MetricConfig): Metric configuration.

    Returns:
        MetricResult containing the calculated dict[str, float value.
    """
    logger.debug("metrics_r_multiple_distribution: executed.")
    return distributions_r_multiple_distribution(input_value, config)
