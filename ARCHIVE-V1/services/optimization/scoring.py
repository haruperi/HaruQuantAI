"""Scoring Functions.

Functions to score backtest results for optimization.

Classes and functions:
    sharpe_score: Function. Provides sharpe_score behavior for optimization workflows.
    sortino_score: Function. Provides sortino_score behavior for optimization workflows.
    calmar_score: Function. Provides calmar_score behavior for optimization workflows.
    profit_factor_score: Function. Provides profit_factor_score behavior for optimization workflows.
    total_return_score: Function. Provides total_return_score behavior for optimization workflows.
    custom_score: Function. Provides custom_score behavior for optimization workflows.
"""

from collections.abc import Callable
from typing import Any

BacktestResult = Any


def sharpe_score(result: BacktestResult) -> float:
    """Score based on Sharpe ratio.

    Purpose:
        Provide deterministic optimization computation, validation, or request packaging as a focused HaruQuant tool.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None unless explicitly documented by the owning workflow.
    """
    return float(result.sharpe_ratio)


def sortino_score(result: BacktestResult) -> float:
    """Score based on Sortino ratio.

    Purpose:
        Provide deterministic optimization computation, validation, or request packaging as a focused HaruQuant tool.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None unless explicitly documented by the owning workflow.
    """
    return float(result.sortino_ratio)


def calmar_score(result: BacktestResult) -> float:
    """Score based on Calmar ratio.

    Purpose:
        Provide deterministic optimization computation, validation, or request packaging as a focused HaruQuant tool.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None unless explicitly documented by the owning workflow.
    """
    return float(result.calmar_ratio)


def profit_factor_score(result: BacktestResult) -> float:
    """Score based on profit factor.

    Purpose:
        Provide deterministic optimization computation, validation, or request packaging as a focused HaruQuant tool.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None unless explicitly documented by the owning workflow.
    """
    pf = result.profit_factor
    return float(pf if pf != float("inf") else 0.0)


def total_return_score(result: BacktestResult) -> float:
    """Score based on total return percentage.

    Purpose:
        Provide deterministic optimization computation, validation, or request packaging as a focused HaruQuant tool.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None unless explicitly documented by the owning workflow.
    """
    return float(result.total_return_pct)


def custom_score(
    result: BacktestResult,
    return_weight: float = 0.3,
    sharpe_weight: float = 0.4,
    dd_weight: float = 0.3,
) -> float:
    """Compute a custom composite score.

    Args:
        result: BacktestResult
        return_weight: Weight for return component
        sharpe_weight: Weight for Sharpe ratio
        dd_weight: Weight for drawdown (penalty)

    Returns:
        Weighted score

    Purpose:
        Provide deterministic optimization computation, validation, or request packaging as a focused HaruQuant tool.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None unless explicitly documented by the owning workflow.
    """
    total_ret = float(result.total_return_pct)
    sharpe = float(result.sharpe_ratio)
    max_dd = float(abs(result.max_drawdown_pct))

    # Normalize and combine
    # Higher return = better
    # Higher Sharpe = better
    # Lower drawdown = better (so we penalize high DD)

    score = (
        (total_ret / 100) * return_weight
        + sharpe * sharpe_weight
        - (max_dd / 100) * dd_weight
    )

    return score


def optimization_get_scoring_func(objective: str) -> Callable[..., float]:
    """Resolve a scoring function by objective name.

    Purpose:
        Provide deterministic scoring function lookup for optimization method
        wrappers.

    Tool class:
        read_only

    Risk level:
        low

    Approval required:
        none

    Side effects:
        None.
    """
    scoring_map = {
        "Sharpe Ratio": sharpe_score,
        "Sortino Ratio": sortino_score,
        "Calmar Ratio": calmar_score,
        "Total Return": total_return_score,
        "Profit Factor": profit_factor_score,
    }
    result: Callable[..., float] = scoring_map.get(objective, sharpe_score)
    return result
