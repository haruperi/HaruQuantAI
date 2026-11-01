"""Portfolio Master existing-portfolio fitness method service.

Description:
    Evaluates candidate portfolios against multi-metric criteria
    (NetProfit, PctStagnation, ReturnDD) using normalized range
    transformations or approximate target matching.
Purpose:
    FEAT-PORTFOLIO-MASTER: Evaluate candidate portfolio fitness.
Key Capabilities:
    - FR-master-fitness-normalize: Synchronize criterion target field state.
    - FR-master-fitness-evaluate: Compute weighted composite fitness in [0, 1].
Python API Usage:
    from app.workspace.portfolio_master.fitness_method_existing_portfolio import (
        ExistingPortfolioCriterion,
        ExistingPortfolioFitnessConfig,
        FitnessMethodExistingPortfolioService,
    )
    score = FitnessMethodExistingPortfolioService.evaluate(stats, config)
CLI Usage:
    uv run python -m pytest tests/workspace/portfolio_master
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal

from app.core.host.logging import get_logger
from app.extend.portfolio_master_fitness.catalog import (
    PortfolioMasterFitnessCatalog,
)
from app.workspace.portfolio_master.fitness_target import (
    FitnessTarget,
    TargetFieldState,
)

logger = get_logger(__name__)

_EPSILON: float = 1e-12
_HALF: float = 0.5


@dataclass(frozen=True, slots=True)
class ExistingPortfolioCriterion:
    """Single ranking criterion with weighting and target configuration."""

    metric_id: Literal["NetProfit", "PctStagnation", "ReturnDD"]
    value_type: int = 1
    approximate_type: int = 2
    weight: float = 1.0
    target: float = 0.0


@dataclass(frozen=True, slots=True)
class ExistingPortfolioFitnessConfig:
    """Configuration holding existing portfolio baseline and active criteria."""

    existing_portfolio_id: str | None = None
    criteria: tuple[ExistingPortfolioCriterion, ...] = field(
        default_factory=lambda: (ExistingPortfolioCriterion(metric_id="ReturnDD"),)
    )


class FitnessMethodExistingPortfolioService:
    """Service evaluating candidate portfolio fitness scores."""

    @classmethod
    def normalize_criterion(
        cls, criterion: ExistingPortfolioCriterion
    ) -> tuple[ExistingPortfolioCriterion, TargetFieldState]:
        """Normalize criterion target and evaluate target field state.

        Args:
            criterion: ExistingPortfolioCriterion instance.

        Returns:
            Tuple of updated ExistingPortfolioCriterion and TargetFieldState.
        """
        target_state = FitnessTarget.apply(
            value_type=criterion.value_type,
            approximate_type=criterion.approximate_type,
            target=criterion.target,
        )

        normalized_criterion = ExistingPortfolioCriterion(
            metric_id=criterion.metric_id,
            value_type=criterion.value_type,
            approximate_type=criterion.approximate_type,
            weight=criterion.weight,
            target=target_state.target,
        )
        return normalized_criterion, target_state

    @classmethod
    def evaluate(
        cls,
        portfolio_stats: Mapping[str, float],
        config: ExistingPortfolioFitnessConfig,
        *,
        existing_stats: Mapping[str, float] | None = None,
    ) -> float:
        """Evaluate candidate portfolio statistics against configured criteria.

        Args:
            portfolio_stats: Read-only mapping of candidate statistics.
            config: ExistingPortfolioFitnessConfig specifying criteria.
            existing_stats: Optional baseline portfolio statistics.

        Returns:
            Composite fitness score in [0.0, 1.0] rounded to 6 decimals.
        """
        if existing_stats is not None:
            logger.debug("Baseline existing stats: %s", existing_stats)

        total_weight = 0.0
        weighted_sum = 0.0

        for criterion in config.criteria:
            if criterion.weight <= 0.0:
                continue

            desc = PortfolioMasterFitnessCatalog.get_descriptor(criterion.metric_id)
            raw_val = PortfolioMasterFitnessCatalog.compute(
                criterion.metric_id, portfolio_stats
            )
            span = desc.range_max - desc.range_min

            if criterion.value_type == criterion.approximate_type:
                score = cls._score_approximate(raw_val, criterion.target, span)
            else:
                score = cls._score_range(raw_val, desc.range_min, span, desc.maximize)

            weighted_sum += criterion.weight * score
            total_weight += criterion.weight

        if total_weight <= 0.0:
            return 0.0

        result = weighted_sum / total_weight
        clamped = max(0.0, min(1.0, result))
        rounded = round(clamped, 6)

        logger.debug(
            "Portfolio fitness evaluated: %f (from %d criteria)",
            rounded,
            len(config.criteria),
        )
        return rounded

    @staticmethod
    def _score_approximate(val: float, target: float, span: float) -> float:
        """Compute fitness score against an approximate target."""
        if span <= _EPSILON:
            return 1.0 if abs(val - target) <= _EPSILON else 0.0
        diff = abs(val - target)
        return max(0.0, min(1.0, 1.0 - diff / span))

    @staticmethod
    def _score_range(
        val: float, range_min: float, span: float, maximize: bool
    ) -> float:
        """Compute fitness score normalized across min/max range."""
        if span <= _EPSILON:
            return _HALF
        norm = (val - range_min) / span
        if not maximize:
            norm = 1.0 - norm
        return max(0.0, min(1.0, norm))
