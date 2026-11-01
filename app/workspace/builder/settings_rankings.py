"""Strategy rankings, filtering conditions, and databank capacity service.

Description:
    Manages the Strategy Ranking & Filtering conditions configuration tab in the
    Builder workspace, governing target databank capacity limits, multi-objective
    fitness configurations, and automatic acceptance filtering criteria.

Purpose:
    FEAT-BUILDER-SETTINGS-RANKINGS: Candidate filtering and databank capacity control.

Key Capabilities:
    - FR-builder-rankings-config: Typed models for filter conditions and settings.
    - FR-builder-rankings-capacity: Change max records with bounds enforcement.
    - FR-builder-rankings-evaluate: Candidate qualification evaluating fitness and all
      enabled filter conditions.

Python API Usage:
    from app.workspace.builder.settings_rankings import (
        RankingFilterCondition,
        RankingsSettings,
        SettingsRankingsService,
    )
    service = SettingsRankingsService()
    resp = service.change_max_records("proj_1", "Results", 500)

CLI Usage:
    python -c "from app.workspace.builder.settings_rankings import (
        SettingsRankingsService,
    ); print(1)"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.lib.responses import StandardResponse
from app.workspace.builder.common import wrap_response
from app.workspace.builder.fitness_method_strategy_result import (
    FitnessMethodStrategyResultConfig,
    FitnessMethodStrategyResultService,
)

logger = get_logger(__name__)

_MIN_MAX_RECORDS: int = 1
_MAX_MAX_RECORDS: int = 100_000
_EPSILON: float = 1e-9

ComparisonOperator = Literal[">", ">=", "<", "<=", "=="]


@dataclass(frozen=True, slots=True)
class RankingFilterCondition:
    """Individual filter rule applied to candidate strategy performance metrics."""

    column_id: str
    operator: ComparisonOperator
    threshold: float
    sample_type: str = "FullSample"
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert filter condition to dictionary."""
        return {
            "column_id": self.column_id,
            "operator": self.operator,
            "threshold": self.threshold,
            "sample_type": self.sample_type,
            "enabled": self.enabled,
        }


@dataclass(frozen=True, slots=True)
class RankingsSettings:
    """Settings collection for strategy rankings, filtering, and storage limits."""

    target_databank: str = "Results"
    max_records: int = 1000
    stop_when_databank_full: bool = False
    fitness_config: FitnessMethodStrategyResultConfig = field(
        default_factory=FitnessMethodStrategyResultConfig
    )
    conditions: tuple[RankingFilterCondition, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "target_databank": self.target_databank,
            "max_records": self.max_records,
            "stop_when_databank_full": self.stop_when_databank_full,
            "fitness_config": self.fitness_config.to_dict(),
            "conditions": [c.to_dict() for c in self.conditions],
        }


class SettingsRankingsService:
    """Service evaluating candidate strategies and managing ranking settings."""

    def __init__(
        self,
        fitness_service: FitnessMethodStrategyResultService | None = None,
    ) -> None:
        """Initialize rankings service with optional fitness evaluator."""
        self._fitness_service = fitness_service or FitnessMethodStrategyResultService()

    def change_max_records(
        self,
        project_id: str,
        databank_name: str,
        max_records: int,
    ) -> StandardResponse[int]:
        """Configure the maximum number of strategy records stored in a databank.

        Args:
            project_id: Target project identifier.
            databank_name: Target databank name.
            max_records: Maximum strategy capacity.

        Returns:
            StandardResponse containing updated max_records count.

        Raises:
            DomainError: If max_records is not between 1 and 100,000.
        """
        logger.debug(
            "Changing max_records to %d for project=%s, databank=%s",
            max_records,
            project_id,
            databank_name,
        )
        if not (_MIN_MAX_RECORDS <= max_records <= _MAX_MAX_RECORDS):
            raise DomainError(
                code="BUILDER_INVALID_MAX_RECORDS",
                message=(
                    f"max_records must be between 1 and 100,000 (got {max_records})"
                ),
            )

        return wrap_response(
            request_id=f"change-max-records-{project_id}",
            data=max_records,
            json_payload={"max_records": max_records},
        )

    def evaluate_candidate(
        self,
        stats: Any,
        settings: RankingsSettings,
    ) -> tuple[bool, float, tuple[str, ...]]:
        """Evaluate a strategy candidate against fitness config and acceptance filters.

        Args:
            stats: Strategy performance statistics snapshot.
            settings: RankingsSettings instance.

        Returns:
            Tuple of (passed, fitness_score, failed_condition_descriptions).
        """
        logger.debug(
            "Evaluating candidate across %d conditions", len(settings.conditions)
        )
        fitness_score = self._fitness_service.evaluate(stats, settings.fitness_config)

        failed_conditions: list[str] = []
        for cond in settings.conditions:
            if not cond.enabled:
                continue

            val = self._fitness_service.extract_metric(stats, cond.column_id)
            if val is None:
                failed_conditions.append(
                    f"{cond.column_id} {cond.operator} {cond.threshold} "
                    "failed (metric unavailable)"
                )
                continue

            passes = self._compare(val, cond.operator, cond.threshold)
            if not passes:
                failed_conditions.append(
                    f"{cond.column_id} {cond.operator} {cond.threshold} "
                    f"failed (actual: {val})"
                )

        passed = len(failed_conditions) == 0
        return passed, fitness_score, tuple(failed_conditions)

    @staticmethod
    def _compare(actual: float, operator: ComparisonOperator, threshold: float) -> bool:
        """Evaluate numeric comparison operator."""
        if operator == ">":
            return actual > threshold
        if operator == ">=":
            return actual >= threshold
        if operator == "<":
            return actual < threshold
        if operator == "<=":
            return actual <= threshold
        return abs(actual - threshold) < _EPSILON
