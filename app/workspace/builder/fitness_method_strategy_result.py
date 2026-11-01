"""Single-metric and multi-objective strategy fitness evaluation service.

Description:
    Evaluates candidate strategy backtest performance statistics across
    configurable in-sample/out-of-sample segments, normalizing metrics against
    target thresholds and computing single-metric or weighted multi-objective
    fitness scores in [0.0, 1.0].

Purpose:
    FEAT-BUILDER-FITNESS-EVALUATION: Calculate normalized strategy fitness scores.

Key Capabilities:
    - FR-builder-fitness-criteria: Typed configuration for weighted metrics.
    - FR-builder-fitness-evaluate: Normalized score calculation with direction
      inversion and zero-trade guard.

Python API Usage:
    from app.workspace.builder.fitness_method_strategy_result import (
        FitnessCriterion,
        FitnessMethodStrategyResultConfig,
        FitnessMethodStrategyResultService,
    )
    service = FitnessMethodStrategyResultService()
    score = service.evaluate(stats, FitnessMethodStrategyResultConfig())

CLI Usage:
    python -c "from app.workspace.builder.fitness_method_strategy_result import (
        FitnessMethodStrategyResultService,
    ); print(1)"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError

logger = get_logger(__name__)

_DEFAULT_NORMALIZATION_DIVISOR: float = 10.0
_FITNESS_DECIMALS: int = 6


@dataclass(frozen=True, slots=True)
class FitnessCriterion:
    """Individual metric criterion for strategy fitness evaluation."""

    column_id: str
    weight: float = 1.0
    maximize: bool = True
    target_value: float | None = None
    sample_type: str = "InSample"

    def to_dict(self) -> dict[str, Any]:
        """Convert criterion to dictionary."""
        return {
            "column_id": self.column_id,
            "weight": self.weight,
            "maximize": self.maximize,
            "target_value": self.target_value,
            "sample_type": self.sample_type,
        }


@dataclass(frozen=True, slots=True)
class FitnessMethodStrategyResultConfig:
    """Configuration for single or weighted multi-objective fitness calculation."""

    mode: Literal["SINGLE", "WEIGHTED"] = "SINGLE"
    criteria: tuple[FitnessCriterion, ...] = field(
        default_factory=lambda: (FitnessCriterion(column_id="ReturnDDRatio"),)
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "mode": self.mode,
            "criteria": [c.to_dict() for c in self.criteria],
        }


class FitnessMethodStrategyResultService:
    """Service evaluating normalized strategy fitness against performance stats."""

    def evaluate(
        self,
        stats: Any,
        config: FitnessMethodStrategyResultConfig,
    ) -> float:
        """Calculate weighted fitness score in range [0.0, 1.0].

        Args:
            stats: Strategy performance statistics snapshot (dict or object).
            config: Fitness configuration containing evaluation criteria.

        Returns:
            Normalized fitness score rounded to 6 decimal places.

        Raises:
            DomainError: If criteria list is empty or sum of weights <= 0.
        """
        logger.debug("Evaluating fitness with %d criteria", len(config.criteria))

        if len(config.criteria) == 0:
            raise DomainError(
                code="BUILDER_INVALID_FITNESS_WEIGHTS",
                message="At least one fitness criterion is required",
            )

        total_weight = sum(c.weight for c in config.criteria)
        if total_weight <= 0.0:
            raise DomainError(
                code="BUILDER_INVALID_FITNESS_WEIGHTS",
                message=f"Sum of fitness weights must be > 0.0 (got {total_weight})",
            )

        # Check for zero trades
        num_trades = self.extract_metric(stats, "number_of_trades")
        if num_trades is None:
            num_trades = self.extract_metric(stats, "trades_count")
        if num_trades is not None and num_trades == 0:
            logger.debug("Zero trades recorded; fitness evaluated to 0.0")
            return 0.0

        weighted_sum = 0.0
        for criterion in config.criteria:
            val = self.extract_metric(stats, criterion.column_id)
            raw_val = float(val) if val is not None else 0.0

            # Normalization against target_value or default scaling
            if criterion.target_value is not None:
                if criterion.target_value != 0.0:
                    score = raw_val / criterion.target_value
                else:
                    score = 1.0 if raw_val >= 0.0 else 0.0
            else:
                score = (
                    raw_val / _DEFAULT_NORMALIZATION_DIVISOR if raw_val >= 0.0 else 0.0
                )

            score = max(0.0, min(1.0, score))

            if not criterion.maximize:
                score = 1.0 - score

            weighted_sum += criterion.weight * score

        fitness = round(weighted_sum / total_weight, _FITNESS_DECIMALS)
        clamped_fitness = max(0.0, min(1.0, fitness))
        logger.debug("Evaluated fitness: %f", clamped_fitness)
        return clamped_fitness

    def extract_metric(self, stats: Any, column_id: str) -> float | int | None:
        """Helper to extract metric value from stats object or mapping."""
        norm_target = column_id.replace("_", "").lower()

        if isinstance(stats, dict):
            for k, v in stats.items():
                if k.replace("_", "").lower() == norm_target:
                    return float(v) if isinstance(v, (int, float)) else None
            return None

        # Attribute lookup
        if hasattr(stats, column_id):
            v = getattr(stats, column_id)
            return float(v) if isinstance(v, (int, float)) else None

        # Scan object attributes matching normalized name
        for attr in dir(stats):
            if attr.replace("_", "").lower() == norm_target:
                v = getattr(stats, attr)
                return float(v) if isinstance(v, (int, float)) else None

        return None
