"""Cross-Check: Sequential Optimization.

Description:
    Optimizes strategy parameters one-by-one in sequence rather than full Cartesian
    grid product, locking in each optimal parameter before sweeping the next.

Purpose:
    FEAT-RETESTER-CROSS-CHECKS: Sequential parameter optimization cross-check.

Key Capabilities:
    - FR-cross-check-sequential-opt: Coordinate-wise parameter tuning.

Python API Usage:
    from app.workspace.retester.cross_check_sequential_optimization import (
        CrossCheckSequentialOptimizationService,
        SequentialOptConfig,
        SequentialOptParameterRange,
    )
    result = CrossCheckSequentialOptimizationService.run(strat, bars, config)

CLI Usage:
    python -m app.cli retest cross-check-sequential-opt --params FastPeriod:10:20:5
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from app.core.data.contracts import MarketBar
from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.trading.strategy.hsl.models import HSLStrategyDocument
from app.workspace.retester.settings_cross_checks import CrossCheckCondition

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class SequentialOptParameterRange:
    """Sweep range for a single strategy parameter."""

    name: str
    start: float
    stop: float
    step: float

    def values(self) -> list[float]:
        """Generate list of discrete sweep values."""
        if self.step <= 0:
            return [self.start]
        vals: list[float] = []
        curr = self.start
        while curr <= self.stop + 1e-9:
            vals.append(round(curr, 6))
            curr += self.step
        return vals or [self.start]

    def to_dict(self) -> dict[str, Any]:
        """Convert range to dictionary."""
        return {
            "name": self.name,
            "start": self.start,
            "stop": self.stop,
            "step": self.step,
        }


@dataclass(frozen=True, slots=True)
class SequentialOptConfig:
    """Configuration for Sequential Optimization cross-check."""

    enabled: bool = False
    parameters: tuple[SequentialOptParameterRange, ...] = ()
    steps_default: int = 10
    fitness_metric: str = "NetProfit"
    acceptance_conditions: tuple[CrossCheckCondition, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "enabled": self.enabled,
            "parameters": [p.to_dict() for p in self.parameters],
            "steps_default": self.steps_default,
            "fitness_metric": self.fitness_metric,
            "acceptance_conditions": [c.to_dict() for c in self.acceptance_conditions],
        }


@dataclass(frozen=True, slots=True)
class SequentialOptCheckResult:
    """Result of Sequential Optimization evaluation."""

    best_parameters: dict[str, float]
    per_parameter_evaluations: dict[str, int]
    total_evaluations: int
    best_fitness: float
    passed: bool
    failure_reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "best_parameters": dict(self.best_parameters),
            "per_parameter_evaluations": dict(self.per_parameter_evaluations),
            "total_evaluations": self.total_evaluations,
            "best_fitness": self.best_fitness,
            "passed": self.passed,
            "failure_reasons": list(self.failure_reasons),
        }


class CrossCheckSequentialOptimizationService:
    """Service evaluating coordinate-wise sequential parameter tuning."""

    @staticmethod
    def _fitness(
        evaluator: Callable[[dict[str, float]], float], parameters: dict[str, float]
    ) -> float:
        """Require an actual finite result from the supplied evaluator."""
        value = evaluator(parameters)
        if not math.isfinite(value):
            raise DomainError(
                code="HSL_RETEST_EVIDENCE_INVALID",
                message="Optimization fitness must be finite",
            )
        return value

    @classmethod
    def run(
        cls,
        strategy: HSLStrategyDocument,
        bars: Sequence[MarketBar],
        config: SequentialOptConfig,
        eval_fn: Callable[[dict[str, float]], float] | None = None,
    ) -> SequentialOptCheckResult:
        """Run sequential optimization across parameter ranges in declaration order.

        Args:
            strategy: Strategy document candidate.
            bars: Input market bars.
            config: Sequential optimization parameters and ranges.
            eval_fn: Optional custom fitness evaluation function(parameters) -> float.

        Returns:
            SequentialOptCheckResult with best parameters and total evaluation counts.
        """
        if eval_fn is None:
            raise DomainError(
                code="HSL_RETEST_EVALUATOR_REQUIRED",
                message="This retest requires completed real evaluation results",
            )
        del bars
        # Initialize nominal parameters
        current_best_params: dict[str, float] = {}
        for k, p_spec in strategy.strategy.parameters.items():
            current_best_params[k] = float(p_spec.default)

        fitness_evaluator = eval_fn

        best_fitness = cls._fitness(fitness_evaluator, current_best_params)
        evaluations_per_param: dict[str, int] = {}
        total_evals = 0

        for param_range in config.parameters:
            values = param_range.values()
            evaluations_per_param[param_range.name] = len(values)
            total_evals += len(values)

            best_val_for_param = current_best_params.get(
                param_range.name, param_range.start
            )
            local_best_fitness = float("-inf")

            for v in values:
                candidate = dict(current_best_params)
                candidate[param_range.name] = v
                fit = cls._fitness(fitness_evaluator, candidate)
                if fit > local_best_fitness:
                    local_best_fitness = fit
                    best_val_for_param = v

            current_best_params[param_range.name] = best_val_for_param
            best_fitness = local_best_fitness

        failure_reasons: list[str] = []
        metrics = {
            "NetProfit": best_fitness,
            "TotalEvaluations": float(total_evals),
        }

        for cond in config.acceptance_conditions:
            val = metrics.get(cond.metric, 0.0)
            if not cond.evaluate(val):
                failure_reasons.append(
                    f"Sequential Opt Condition '{cond.name}' failed: "
                    f"{cond.metric}={val} {cond.operator} {cond.threshold}"
                )

        passed = len(failure_reasons) == 0
        logger.info(
            "FR-cross-check-sequential-opt: executed %d evals across %d params, "
            "best_fitness=%.2f, passed=%s",
            total_evals,
            len(config.parameters),
            best_fitness,
            passed,
        )

        return SequentialOptCheckResult(
            best_parameters=current_best_params,
            per_parameter_evaluations=evaluations_per_param,
            total_evaluations=total_evals,
            best_fitness=best_fitness,
            passed=passed,
            failure_reasons=tuple(failure_reasons),
        )
