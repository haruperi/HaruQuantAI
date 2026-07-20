"""Optimization Result Data Classes.

Contains result structures for optimization runs.

Classes and functions:
    OptimizationResult: Class. Provides OptimizationResult behavior for optimization workflows.
    OptimizationSummary: Class. Provides OptimizationSummary behavior for optimization workflows.
"""

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

BacktestResult = Any


@dataclass
class OptimizationResult:
    """Result from parameter optimization."""

    parameters: dict[str, Any]
    result: BacktestResult
    metrics: dict[str, float]
    score: float
    rank: int = 0

    def __repr__(self) -> str:
        """Return a concise representation for debugging."""
        return f"OptimizationResult(score={self.score:.4f}, rank={self.rank}, params={self.parameters})"


@dataclass
class OptimizationSummary:
    """Summary of optimization run."""

    best_params: dict[str, Any]
    best_score: float
    best_result: BacktestResult | None
    all_results: list[OptimizationResult] = field(default_factory=list)
    total_combinations: int = 0
    completed: int = 0
    failed: int = 0
    duration_seconds: float = 0.0

    def get_top_n(self, n: int = 10) -> list[OptimizationResult]:
        """Get top N results by score.

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
        sorted_results = sorted(self.all_results, key=lambda x: x.score, reverse=True)
        return sorted_results[:n]

    def to_dataframe(self) -> pd.DataFrame:
        """Convert results to DataFrame for analysis.

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
        rows = []
        for opt_result in self.all_results:
            row = {
                **opt_result.parameters,
                **opt_result.metrics,
                "score": opt_result.score,
                "rank": opt_result.rank,
            }
            rows.append(row)
        return pd.DataFrame(rows)
