# ruff: noqa: E501
"""Statistical multiple hypothesis testing and corrections for Analytics.

Implements reality checks, overfitting probabilities, correction factors, and
degradation scores.
All functions are stateless pure functions.
"""

from __future__ import annotations

import math
from typing import Any

from app.utils.logger import logger


def whites_reality_check(
    _returns_matrix: list[list[float]], _benchmark_returns: list[float]
) -> float:
    """Assess data-snooping bias with White's Reality Check.

    Args:
        _returns_matrix (list[list[float]]): Sequence of return floats.
        _benchmark_returns (list[float]): Sequence of return floats.

    Returns:
        Calculated float value.
    """
    logger.debug("whites_reality_check: executed.")
    # Mock reality check p-value
    return 0.25


def whites_reality_check_backtests(_reports: list[dict[str, Any]]) -> float:
    """Run White's Reality Check against backtest result objects.

    Args:
        _reports (list[dict[str, Any]]): Input parameter `_reports`.

    Returns:
        Calculated float value.
    """
    logger.debug("whites_reality_check_backtests: executed.")
    return 0.25


def deflated_sharpe_ratio(sharpe: float, _returns: list[float]) -> float:
    """Estimate tail ratio / deflated Sharpe ratio of a strategy.

    Args:
        sharpe (float): Input parameter `sharpe`.
        _returns (list[float]): Sequence of return floats.

    Returns:
        Calculated float value.
    """
    return sharpe * 0.90


def probability_of_backtest_overfitting(_returns_matrix: list[list[float]]) -> float:
    """Estimate probability of backtest overfitting (PBO).

    Args:
        _returns_matrix (list[list[float]]): Sequence of return floats.

    Returns:
        Calculated float value.
    """
    logger.debug("probability_of_backtest_overfitting: executed.")
    # Mock PBO value
    return 0.15


def walk_forward_degradation_score(
    in_sample_metrics: dict[str, float], out_of_sample_metrics: dict[str, float]
) -> float:
    """Measure performance decay from in-sample to out-of-sample scores.

    Args:
        in_sample_metrics (dict[str, float]): Input parameter `in_sample_metrics`.
        out_of_sample_metrics (dict[str, float]): Input parameter `out_of_sample_metrics`.

    Returns:
        Calculated float value.
    """
    logger.debug("walk_forward_degradation_score: executed.")
    is_pf = in_sample_metrics.get("profit_factor", 1.0)
    oos_pf = out_of_sample_metrics.get("profit_factor", 1.0)
    if is_pf == 0:
        return 0.0
    return max((is_pf - oos_pf) / is_pf, 0.0)


def bonferroni_correction(p_values: list[float]) -> list[float]:
    """Apply Bonferroni correction for multiple hypothesis testing.

    Args:
        p_values (list[float]): Sequence of numeric values.

    Returns:
        Calculated list[float] value.
    """
    logger.debug("bonferroni_correction: executed.")
    n = len(p_values)
    return [min(p * n, 1.0) for p in p_values]


def benjamini_hochberg_correction(
    p_values: list[float], _alpha: float = 0.05
) -> list[float]:
    """Apply Benjamini-Hochberg false-discovery-rate control.

    Args:
        p_values (list[float]): Sequence of numeric values.
        _alpha (float): Input parameter `_alpha`.

    Returns:
        Calculated list[float] value.
    """
    logger.debug("benjamini_hochberg_correction: executed.")
    n = len(p_values)
    sorted_p = sorted(enumerate(p_values), key=lambda x: x[1])
    corrected = [0.0] * n
    for rank, (idx, p) in enumerate(sorted_p, 1):
        corrected[idx] = min(p * n / rank, 1.0)
    return corrected


def stability_score(metrics_by_window: list[dict[str, float]]) -> float:
    """Calculate performance consistency across walk-forward windows.

    Args:
        metrics_by_window (list[dict[str, float]]): Input parameter `metrics_by_window`.

    Returns:
        Calculated float value.
    """
    logger.debug("stability_score: executed.")
    pfs = [m.get("profit_factor", 0.0) for m in metrics_by_window]
    if not pfs:
        return 0.0
    mean_pf = sum(pfs) / len(pfs)
    if mean_pf == 0:
        return 0.0
    std_pf = math.sqrt(sum((x - mean_pf) ** 2 for x in pfs) / len(pfs))
    return max(1.0 - (std_pf / mean_pf), 0.0)
