"""Builder execution job runner, indicator calibration, and genetic evolution engine.

Description:
    Delegates validated native execution snapshots to Core-backed random generation,
    actual market-bar evaluation and result persistence. Legacy calls without
    execution inputs fail closed. Genetic/template modes remain unavailable.

Purpose:
    FEAT-BUILDER-TASK-BUILD: Core candidate generation and qualification runner.

Key Capabilities:
    - FR-builder-calibrate: Indicator dynamic range calibration across market bars.
    - FR-builder-execute-gp: Multi-island GP candidate evolution & backtest evaluation.
    - FR-builder-candidate-filter: Acceptance filtering and databank record limits.

Python API Usage:
    from app.workspace.builder.task_build import TaskBuildRunner, TaskBuildSummary
    summary = TaskBuildRunner.execute(
        project_id="proj_1",
        what_to_build=what_to_build,
        genetic_options=genetic_options,
        blocks=blocks,
        parts_to_improve=parts,
        rankings=rankings,
        seed=42,
    )

CLI Usage:
    python -c "from app.workspace.builder.task_build import TaskBuildRunner; print(1)"
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger
from app.core.jobs.manager import JobContext
from app.core.lib.errors import DomainError
from app.workspace.builder.genetic_defaults import GeneticOptionsDefaults
from app.workspace.builder.settings_blocks import BlocksSelectionSettings
from app.workspace.builder.settings_parts_to_improve import PartsToImproveSettings
from app.workspace.builder.settings_rankings import (
    RankingsSettings,
)
from app.workspace.builder.settings_what_to_build import WhatToBuildSettings
from app.workspace.home.execution import ExecutionSnapshot, ProjectExecutor

logger = get_logger(__name__)

_DEFAULT_PERCENT_DIVISOR: float = 100.0


@dataclass(frozen=True, slots=True)
class BarRecord:
    """Historical OHLCV bar representation for indicator calibration."""

    time: int | float
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


@dataclass(frozen=True, slots=True)
class TaskBuildSummary:
    """Execution receipt summarizing a completed builder run."""

    build_mode: str
    generations_completed: int
    candidates_evaluated: int
    candidates_accepted: int
    candidates_rejected: int
    best_fitness: float
    accepted_strategy_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert summary to dictionary."""
        return {
            "build_mode": self.build_mode,
            "generations_completed": self.generations_completed,
            "candidates_evaluated": self.candidates_evaluated,
            "candidates_accepted": self.candidates_accepted,
            "candidates_rejected": self.candidates_rejected,
            "best_fitness": self.best_fitness,
            "accepted_strategy_ids": list(self.accepted_strategy_ids),
        }


class TaskBuildRunner:
    """Orchestrates candidate generation, indicator calibration, and qualification."""

    @classmethod
    def calibrate_indicators(
        cls,
        blocks: BlocksSelectionSettings,
        bars: Sequence[Any],
    ) -> dict[str, tuple[float, float]]:
        """Compute observed output ranges (min, max) for enabled indicator blocks.

        Args:
            blocks: Active block selections and parameters.
            bars: Chronological sequence of historical bars.

        Returns:
            Dictionary mapping block_id to observed (min_value, max_value) tuple.
        """
        logger.debug(
            "Calibrating indicators across %d blocks and %d bars",
            len(blocks.selections),
            len(bars),
        )
        ranges: dict[str, tuple[float, float]] = {}

        high_vals = [
            float(
                getattr(b, "high", b.get("high", 0.0) if isinstance(b, dict) else 0.0)
            )
            for b in bars
        ] or [1.0]
        low_vals = [
            float(getattr(b, "low", b.get("low", 0.0) if isinstance(b, dict) else 0.0))
            for b in bars
        ] or [0.0]
        min_price = min(low_vals)
        max_price = max(high_vals)

        for sel in blocks.selections:
            if not sel.enabled:
                continue

            bid = sel.block_id
            if "rsi" in bid or "stochastic" in bid or "mfi" in bid:
                ranges[bid] = (0.0, 100.0)
            elif "cci" in bid:
                ranges[bid] = (-200.0, 200.0)
            elif "macd" in bid or "momentum" in bid:
                ranges[bid] = (-0.05, 0.05)
            else:
                ranges[bid] = (round(min_price, 4), round(max_price, 4))

        return ranges

    @classmethod
    def execute(  # noqa: PLR0917
        cls,
        project_id: str,
        what_to_build: WhatToBuildSettings,
        genetic_options: GeneticOptionsDefaults,
        blocks: BlocksSelectionSettings,
        parts_to_improve: PartsToImproveSettings,
        rankings: RankingsSettings,
        *,
        seed: int = 42,
        execution: ProjectExecutor | None = None,
        snapshot: ExecutionSnapshot | None = None,
        context: JobContext | None = None,
    ) -> TaskBuildSummary:
        """Execute candidate strategy generation, backtesting, and databank storage.

        Args:
            project_id: Target project identifier.
            what_to_build: What to build configuration.
            genetic_options: Genetic algorithm configuration parameters.
            blocks: Selected building blocks and weights.
            parts_to_improve: Improvement rules for template mutation.
            rankings: Strategy ranking and acceptance filtering conditions.
            seed: Legacy seed; execution uses the captured native snapshot.
            execution: Injected Core-backed execution owner.
            snapshot: Validated immutable native task inputs.
            context: Host cooperative lifecycle context.

        Returns:
            TaskBuildSummary containing execution metrics.
        """
        logger.info(
            "FR-builder-execute-gp: native snapshot supersedes legacy form inputs "
            "(population=%d, blocks=%d, improvements=%d, limit=%d, seed=%d)",
            genetic_options.population_size,
            len(blocks.selections),
            len(parts_to_improve.rules),
            rankings.max_records,
            seed,
        )
        if execution is None or snapshot is None or context is None:
            raise DomainError(
                code="EXECUTION_CONTEXT_REQUIRED",
                message="Builder requires a validated native execution snapshot",
            )
        if snapshot.project_id != project_id or what_to_build.build_mode != "RANDOM":
            raise DomainError(
                code="UNSUPPORTED_MODE",
                message="Only snapshot-backed random generation is available",
            )
        logger.info(
            "FR-builder-execute-gp: evaluating validated snapshot for %s", project_id
        )
        receipt = execution.run(context, snapshot)
        if receipt["best_fitness"] is None:
            raise DomainError(
                code="NO_FINITE_RESULTS", message="All evaluations were rejected"
            )
        return TaskBuildSummary(
            build_mode="RANDOM",
            generations_completed=1,
            candidates_evaluated=int(receipt["candidates_evaluated"]),
            candidates_accepted=int(receipt["candidates_accepted"]),
            candidates_rejected=int(receipt["candidates_rejected"]),
            best_fitness=float(receipt["best_fitness"]),
            accepted_strategy_ids=tuple(str(key) for key in receipt["result_ids"]),
        )
