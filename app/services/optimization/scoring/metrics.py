"""Objective projection and multiple-testing evidence."""

from __future__ import annotations

import math
from collections.abc import Sequence
from statistics import NormalDist
from typing import TYPE_CHECKING

from app.services.optimization.scoring.contracts import (
    OBJECTIVE_DIRECTIONS,
    CandidateScore,
    ObjectiveName,
)
from app.utils import logger

if TYPE_CHECKING:
    from app.services.analytics import PerformanceReport

_MINIMUM_DSR_SAMPLE_COUNT = 3
_SHA256_HEX_LENGTH = 64
_SCALAR_METRIC_KEYS = frozenset(
    {item.value for item in ObjectiveName} | {"trade_count"}
)


def _metric_values(report: PerformanceReport) -> dict[str, float | None]:
    """Project Analytics metric evidence by canonical key.

    Args:
        report: Analytics-owned performance report.

    Returns:
        Metric values keyed by Analytics metric key.

    Raises:
        TypeError: If a selected objective metric is not numeric.
        ValueError: If duplicate calculated evidence exists.
    """
    logger.debug("Projecting Analytics metrics for Optimization")
    metrics: dict[str, float | None] = {}
    for section in report.sections:
        for metric in section.metrics:
            if (
                metric.metric_key not in _SCALAR_METRIC_KEYS
                or metric.source_context != "all"
            ):
                continue
            if metric.value is not None and not isinstance(metric.value, (int, float)):
                from decimal import Decimal

                if not isinstance(metric.value, Decimal):
                    raise TypeError("Optimization objective metric must be numeric")
            value = None if metric.value is None else float(metric.value)
            if metric.metric_key in metrics and metrics[metric.metric_key] != value:
                raise ValueError(
                    "Analytics report contains conflicting metric evidence"
                )
            metrics[metric.metric_key] = value
    return metrics


def calculate_candidate_score(
    report: PerformanceReport,
    *,
    candidate_hash: str,
    objective: ObjectiveName,
    enabled_objectives: frozenset[ObjectiveName],
) -> CandidateScore:
    """Project one enabled objective from an Analytics report.

    Args:
        report: Analytics-owned performance evidence.
        candidate_hash: Candidate provenance hash.
        objective: Selected objective metric key.
        enabled_objectives: Explicit production whitelist.

    Returns:
        Available or explicitly unavailable candidate score.

    Raises:
        ValueError: If the objective is disabled or report evidence conflicts.
    """
    logger.info("Calculating Optimization candidate score from Analytics evidence")
    if objective not in enabled_objectives:
        raise ValueError("optimization objective is not enabled")
    metrics = _metric_values(report)
    value = metrics.get(objective.value)
    trade_count_value = metrics.get("trade_count")
    trade_count = None if trade_count_value is None else int(trade_count_value)
    caveats = tuple(flag.code for flag in report.quality_flags)
    if value is None:
        caveats = (*caveats, "objective_unavailable")
    return CandidateScore(
        candidate_hash=candidate_hash,
        objective=objective,
        direction=OBJECTIVE_DIRECTIONS[objective],
        value=value,
        available=value is not None,
        trade_count=trade_count,
        metrics=metrics,
        caveats=caveats,
    )


def calculate_deflated_sharpe(
    *,
    sharpe: float,
    variance: float,
    skewness: float,
    kurtosis: float,
    sample_count: int,
    nominal_trials: int,
) -> float | None:
    """Calculate the Bailey-Lopez de Prado Deflated Sharpe probability.

    Args:
        sharpe: Observed Sharpe ratio.
        variance: Cross-trial Sharpe variance estimate.
        skewness: Sample return skewness.
        kurtosis: Sample Pearson kurtosis.
        sample_count: Return observation count.
        nominal_trials: Unique candidate trial count.

    Returns:
        Probability in ``[0, 1]`` or None when evidence is insufficient.

    Raises:
        ValueError: If supplied numeric evidence is non-finite or invalid.
    """
    logger.info("Calculating Optimization Deflated Sharpe evidence")
    values = (sharpe, variance, skewness, kurtosis)
    if any(not math.isfinite(value) for value in values):
        raise ValueError("Deflated Sharpe inputs must be finite")
    if variance < 0 or sample_count < 0 or nominal_trials < 0:
        raise ValueError("Deflated Sharpe counts and variance cannot be negative")
    if sample_count < _MINIMUM_DSR_SAMPLE_COUNT or nominal_trials < 1 or variance == 0:
        return None
    normal = NormalDist()
    euler_gamma = 0.5772156649015329
    trial_count = float(nominal_trials)
    first_probability = 1.0 - (1.0 / trial_count)
    second_probability = 1.0 - (1.0 / (trial_count * math.e))
    if nominal_trials == 1:
        expected_maximum = 0.0
    else:
        expected_maximum = math.sqrt(variance) * (
            (1.0 - euler_gamma) * normal.inv_cdf(first_probability)
            + euler_gamma * normal.inv_cdf(second_probability)
        )
    denominator_squared = (
        1.0 - skewness * sharpe + (((kurtosis - 1.0) / 4.0) * sharpe * sharpe)
    )
    if denominator_squared <= 0:
        return None
    statistic = (
        (sharpe - expected_maximum)
        * math.sqrt(sample_count - 1)
        / math.sqrt(denominator_squared)
    )
    return normal.cdf(statistic)


def count_nominal_trials(candidate_hashes: Sequence[str]) -> int:
    """Count unique well-formed candidate hashes.

    Args:
        candidate_hashes: Candidate digests after rejection and deduplication.

    Returns:
        Unique nominal trial count.

    Raises:
        ValueError: If any hash is malformed.
    """
    logger.info("Counting nominal Optimization trials")
    if any(
        len(item) != _SHA256_HEX_LENGTH
        or any(character not in "0123456789abcdef" for character in item)
        for item in candidate_hashes
    ):
        raise ValueError("candidate trial hash is malformed")
    return len(set(candidate_hashes))


__all__ = [
    "calculate_candidate_score",
    "calculate_deflated_sharpe",
    "count_nominal_trials",
]
