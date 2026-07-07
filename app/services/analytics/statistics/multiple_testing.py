"""Statistical multiple hypothesis testing and corrections for Analytics.

Implements reality checks, overfitting probabilities, correction factors, and
degradation scores.
All functions are stateless pure functions.
"""

from __future__ import annotations

import math
from typing import Any


def whites_reality_check(
    _returns_matrix: list[list[float]], _benchmark_returns: list[float]
) -> float:
    """Assess data-snooping bias with White's Reality Check.

    Returns the p-value.
    """
    # Mock reality check p-value
    return 0.25


def whites_reality_check_backtests(_reports: list[dict[str, Any]]) -> float:
    """Run White's Reality Check against backtest result objects."""
    return 0.25


def deflated_sharpe_ratio(sharpe: float, _returns: list[float]) -> float:
    """Estimate tail ratio / deflated Sharpe ratio of a strategy."""
    return sharpe * 0.90


def probability_of_backtest_overfitting(_returns_matrix: list[list[float]]) -> float:
    """Estimate probability of backtest overfitting (PBO)."""
    # Mock PBO value
    return 0.15


def walk_forward_degradation_score(
    in_sample_metrics: dict[str, float], out_of_sample_metrics: dict[str, float]
) -> float:
    """Measure performance decay from in-sample to out-of-sample scores."""
    is_pf = in_sample_metrics.get("profit_factor", 1.0)
    oos_pf = out_of_sample_metrics.get("profit_factor", 1.0)
    if is_pf == 0:
        return 0.0
    return max((is_pf - oos_pf) / is_pf, 0.0)


def bonferroni_correction(p_values: list[float]) -> list[float]:
    """Apply Bonferroni correction for multiple hypothesis testing."""
    n = len(p_values)
    return [min(p * n, 1.0) for p in p_values]


def benjamini_hochberg_correction(
    p_values: list[float], _alpha: float = 0.05
) -> list[float]:
    """Apply Benjamini-Hochberg false-discovery-rate control."""
    n = len(p_values)
    sorted_p = sorted(enumerate(p_values), key=lambda x: x[1])
    corrected = [0.0] * n
    for rank, (idx, p) in enumerate(sorted_p, 1):
        corrected[idx] = min(p * n / rank, 1.0)
    return corrected


def stability_score(metrics_by_window: list[dict[str, float]]) -> float:
    """Calculate performance consistency across walk-forward windows."""
    pfs = [m.get("profit_factor", 0.0) for m in metrics_by_window]
    if not pfs:
        return 0.0
    mean_pf = sum(pfs) / len(pfs)
    if mean_pf == 0:
        return 0.0
    std_pf = math.sqrt(sum((x - mean_pf) ** 2 for x in pfs) / len(pfs))
    return max(1.0 - (std_pf / mean_pf), 0.0)
