"""Optimizer execution task verifier and runner service.

Description:
    Validates optimizer preconditions and delegates native execution snapshots to
    actual Core grid backtests. Unsupported modes and missing execution inputs
    fail closed; no default database or mock profile rows are constructed.

Purpose:
    FEAT-TASK-OPTIMIZE: Parameter search verification and execution engine.

Key Capabilities:
    - FR-task-optimize-verifier: Enforce strategy presence and WF bounds.
    - FR-task-optimize-runner: Execute optimization sweeps and record best params.

Python API Usage:
    from app.workspace.optimizer.task_optimize import TaskOptimizeRunner
    from app.workspace.optimizer.settings_optimization import (
        OptimizationSettingsSnapshot,
    )
    summary = TaskOptimizeRunner.execute("proj_1", settings)

CLI Usage:
    python -m app.cli optimizer run --strategy-id Strat_01
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.host.logging import get_logger
from app.core.jobs.manager import JobContext
from app.core.lib.errors import DomainError
from app.core.trading.optimization.engine import (
    OptimizationEngine,
)
from app.core.trading.results.store import ResultStore
from app.workspace.home.execution import ExecutionSnapshot, ProjectExecutor
from app.workspace.optimizer.results_optimization_profile import (
    ResultsOptimizationProfileService,
)
from app.workspace.optimizer.settings_optimization import (
    OptimizationSettingsSnapshot,
    SettingsOptimizationService,
)

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class TaskOptimizeSummary:
    """Summary receipt of completed optimization task execution."""

    optimization_type: str
    evaluations_completed: int
    best_parameters: dict[str, float | int | bool]
    best_fitness: float
    stored_strategy_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert task summary to dictionary."""
        return {
            "optimization_type": self.optimization_type,
            "evaluations_completed": self.evaluations_completed,
            "best_parameters": dict(self.best_parameters),
            "best_fitness": self.best_fitness,
            "stored_strategy_ids": list(self.stored_strategy_ids),
        }


class TaskOptimizeVerifier:
    """Validator enforcing preconditions before starting optimization runs."""

    @staticmethod
    def verify(settings: OptimizationSettingsSnapshot) -> None:
        """Verify optimization settings consistency.

        Args:
            settings: Optimization settings to validate.

        Raises:
            DomainError: Code OPTIMIZER_STRATEGY_REQUIRED if strategy_id is None.
            DomainError: Code OPTIMIZER_NO_ENABLED_PARAMETERS if no params enabled.
            DomainError: Code OPTIMIZER_INVALID_WF_GRID if WF bounds inverted.
        """
        if settings.strategy_id is None:
            raise DomainError(
                code="OPTIMIZER_STRATEGY_REQUIRED",
                message="A valid strategy_id is required to perform optimization",
            )

        enabled_optimizable = [
            p
            for p in settings.parameters
            if p.enabled and SettingsOptimizationService.count_parameter_steps(p) > 1
        ]
        if not enabled_optimizable:
            raise DomainError(
                code="OPTIMIZER_NO_ENABLED_PARAMETERS",
                message="At least one enabled parameter with >1 step is required",
            )

        if settings.optimization_type in {"WALK_FORWARD", "WALK_FORWARD_MATRIX"}:
            if settings.param1_stop < settings.param1_start:
                raise DomainError(
                    code="OPTIMIZER_INVALID_WF_GRID",
                    message=(
                        f"WF param1_stop ({settings.param1_stop}) "
                        f"< param1_start ({settings.param1_start})"
                    ),
                )
            if (
                settings.optimization_type == "WALK_FORWARD_MATRIX"
                and settings.param2_stop < settings.param2_start
            ):
                raise DomainError(
                    code="OPTIMIZER_INVALID_WF_GRID",
                    message=(
                        f"WF param2_stop ({settings.param2_stop}) "
                        f"< param2_start ({settings.param2_start})"
                    ),
                )


class TaskOptimizeRunner:
    """Execution runner coordinating parameter evaluation passes."""

    def __init__(
        self,
        engine: OptimizationEngine | None = None,
        store: ResultStore | None = None,
        profile_service: ResultsOptimizationProfileService | None = None,
    ) -> None:
        """Initialize runner with dependencies."""
        self.engine = engine or OptimizationEngine()
        self.store = store
        self.profile_service = profile_service

    @classmethod
    def execute(
        cls,
        project_id: str,
        settings: OptimizationSettingsSnapshot,
        *,
        seed: int = 42,
        execution: ProjectExecutor | None = None,
        snapshot: ExecutionSnapshot | None = None,
        context: JobContext | None = None,
    ) -> TaskOptimizeSummary:
        """Execute complete optimization sweep across configured parameters.

        Args:
            project_id: Project identifier.
            settings: Validated optimization configuration snapshot.
            seed: Legacy seed; execution uses the captured native snapshot.
            execution: Injected Core-backed execution owner.
            snapshot: Validated immutable native task inputs.
            context: Host cooperative lifecycle context.

        Returns:
            TaskOptimizeSummary with evaluations, best parameters, and fitness.
        """
        runner = cls()
        return runner.run_task(
            project_id,
            settings,
            seed=seed,
            execution=execution,
            snapshot=snapshot,
            context=context,
        )

    def run_task(
        self,
        project_id: str,
        settings: OptimizationSettingsSnapshot,
        *,
        seed: int = 42,
        execution: ProjectExecutor | None = None,
        snapshot: ExecutionSnapshot | None = None,
        context: JobContext | None = None,
    ) -> TaskOptimizeSummary:
        """Execute task instance."""
        TaskOptimizeVerifier.verify(settings)
        logger.info(
            "FR-task-optimize-runner: native snapshot supersedes legacy seed %d", seed
        )
        if execution is None or snapshot is None or context is None:
            raise DomainError(
                code="EXECUTION_CONTEXT_REQUIRED",
                message="Optimizer requires a validated native execution snapshot",
            )
        if snapshot.project_id != project_id or settings.optimization_type != "SIMPLE":
            raise DomainError(
                code="UNSUPPORTED_MODE",
                message="Only snapshot-backed grid optimization is available",
            )
        logger.info(
            "FR-task-optimize-runner: evaluating validated snapshot for %s", project_id
        )
        receipt = execution.run(context, snapshot)
        if receipt["best_fitness"] is None:
            raise DomainError(
                code="NO_FINITE_RESULTS", message="All evaluations were rejected"
            )
        return TaskOptimizeSummary(
            optimization_type="SIMPLE",
            evaluations_completed=int(receipt["candidates_evaluated"]),
            best_parameters=dict(receipt["best_parameters"]),
            best_fitness=float(receipt["best_fitness"]),
            stored_strategy_ids=tuple(str(key) for key in receipt["result_ids"]),
        )
