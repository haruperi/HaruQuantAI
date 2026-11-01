"""Walk-Forward Result fitness evaluation service.

Description:
    Implements FitnessMethodWFResultService evaluating multi-criterion walk-forward
    fitness with column validation, normalization, and weighted aggregation.

Purpose:
    FEAT-FITNESS-METHOD-WF-RESULT: Walk-forward strategy fitness evaluation.

Key Capabilities:
    - FR-optimizer-wf-fitness-evaluation: Evaluate normalized WF fitness.
    - FR-optimizer-wf-metric-validation: Reject unregistered WF columns.

Python API Usage:
    from app.workspace.optimizer.fitness_method_w_f_result import (
        FitnessMethodWFResultConfig,
        FitnessMethodWFResultService,
        WFFitnessCriterion,
    )
    c = WFFitnessCriterion(metric="NetProfit", target_value=500.0)
    config = FitnessMethodWFResultConfig(criteria=(c,))
    fitness = FitnessMethodWFResultService.evaluate(
        [{"NetProfit": 500.0}], config
    )  # 1.0

CLI Usage:
    python -m app.cli optimizer eval-wf-fitness --metric NetProfit --target 500
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.workspace.optimizer.wf_metric import first_wf_metric

logger = get_logger(__name__)

# Canonical registered metrics across Columns/Databanks and Columns/WalkForward
_REGISTERED_WF_METRICS: Final[frozenset[str]] = frozenset(
    {
        "NetProfit",
        "GrossProfit",
        "GrossLoss",
        "ProfitFactor",
        "ReturnDDRatio",
        "SharpeRatio",
        "SortinoRatio",
        "CalmarRatio",
        "Drawdown",
        "DrawdownPct",
        "ActualDD",
        "ActualDrawdownPct",
        "Trades",
        "TotalTrades",
        "WinRate",
        "WinningPct",
        "AvgTrade",
        "WinLossRatio",
        "SQN",
        "SQNScore",
        "Stability",
        "Stagnation",
        "StagnationPct",
        "UlcerIndex",
        "Expectancy",
        "AnnualPctReturn",
        "AHPR",
        "GHPR",
        "MaxConsecLosses",
        "MaxConsecWins",
        "AvgLoss",
        "AvgWin",
        "WFPctOfProfitableRuns",
        "WFScore",
        "WFMaxDDbyRun",
        "WFMaxPctDDbyRun",
        "WFMaxProfitByRun",
        "WFMaxProfitByRunInPct",
        "WFMaxStagnationInPct",
        "WFMinTradesInRun",
        "WFRobustnessRatio",
        "WFAvgProfitByRun",
    }
)


@dataclass(frozen=True, slots=True)
class WFFitnessCriterion:
    """Single walk-forward fitness criterion specification."""

    metric: str
    weight: float = 1.0
    maximize: bool = True
    target_value: float = 100.0

    def to_dict(self) -> dict[str, Any]:
        """Convert criterion to dictionary."""
        return {
            "metric": self.metric,
            "weight": self.weight,
            "maximize": self.maximize,
            "target_value": self.target_value,
        }


@dataclass(frozen=True, slots=True)
class FitnessMethodWFResultConfig:
    """Configuration for walk-forward fitness evaluation."""

    criteria: tuple[WFFitnessCriterion, ...] = (WFFitnessCriterion(metric="NetProfit"),)

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "criteria": [c.to_dict() for c in self.criteria],
        }


class FitnessMethodWFResultService:
    """Service evaluating walk-forward fitness score over result sets."""

    @classmethod
    def evaluate(
        cls,
        wf_results: Sequence[Mapping[str, float]] | None,
        config: FitnessMethodWFResultConfig,
    ) -> float:
        """Evaluate weighted normalized walk-forward fitness score.

        Args:
            wf_results: Walk-forward result mapping sequence, or None.
            config: Fitness criteria and weights.

        Returns:
            Weighted fitness score in [0.0, 1.0], rounded to 6 decimal places.

        Raises:
            DomainError: Code OPTIMIZER_UNKNOWN_WF_METRIC on unknown metric.
        """
        # Validate criteria metrics against registered catalog
        for criterion in config.criteria:
            if criterion.metric not in _REGISTERED_WF_METRICS:
                logger.error("Unknown WF metric requested: %s", criterion.metric)
                raise DomainError(
                    code="OPTIMIZER_UNKNOWN_WF_METRIC",
                    message=f"Unknown WF metric: {criterion.metric}",
                )

        if not wf_results:
            logger.debug("No walk-forward results provided; returning 0.0")
            return 0.0

        total_weight = 0.0
        weighted_score_sum = 0.0

        for criterion in config.criteria:
            raw_val = first_wf_metric(wf_results, criterion.metric)
            if not math.isfinite(raw_val):
                raw_val = 0.0

            if criterion.target_value != 0.0:
                ratio = raw_val / criterion.target_value
                if criterion.maximize:
                    normalized = max(0.0, min(1.0, ratio))
                else:
                    normalized = max(0.0, min(1.0, 1.0 - ratio))
            elif criterion.maximize:
                normalized = 1.0 if raw_val >= 0.0 else 0.0
            else:
                normalized = 1.0 if raw_val <= 0.0 else 0.0

            weight = max(0.0, criterion.weight)
            total_weight += weight
            weighted_score_sum += normalized * weight

        if total_weight <= 0.0:
            return 0.0

        final_fitness = round(weighted_score_sum / total_weight, 6)
        logger.debug(
            "Computed WF fitness %f across %d criteria",
            final_fitness,
            len(config.criteria),
        )
        return final_fitness
