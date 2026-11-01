"""Top-level Optimizer workspace controller and API service.

Description:
    Implements AppOptimizerService coordinating optimization settings, task execution,
    walk-forward fitness evaluation, and result view projections.

Purpose:
    FEAT-APP-OPTIMIZER: Workspace orchestration for strategy parameter search.

Key Capabilities:
    - FR-optimizer-workspace-state: Query and mutate workspace execution state.
    - FR-optimizer-lifecycle: Coordinate optimization execution lifecycles.

Python API Usage:
    from app.workspace.optimizer.app_optimizer import AppOptimizerService
    service = AppOptimizerService()
    state_resp = service.start("proj_1")

CLI Usage:
    python -m app.cli optimizer status --project-id proj_1
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.lib.responses import StandardResponse
from app.workspace.optimizer.common import wrap_response
from app.workspace.optimizer.fitness_method_w_f_result import (
    FitnessMethodWFResultService,
)
from app.workspace.optimizer.results_optimization_profile import (
    ResultsOptimizationProfileService,
)
from app.workspace.optimizer.results_sequential_optimization import (
    ResultsSequentialOptimizationService,
)
from app.workspace.optimizer.results_sys_param_permutation import (
    ResultsSysParamPermutationService,
)
from app.workspace.optimizer.results_walk_forward import ResultsWalkForwardService
from app.workspace.optimizer.settings_optimization import (
    OptimizationSettingsSnapshot,
    SettingsOptimizationService,
)
from app.workspace.optimizer.task_optimize import TaskOptimizeRunner

logger = get_logger(__name__)

OptimizerStatus = Literal[
    "IDLE",
    "RUNNING",
    "PAUSED",
    "COMPLETED",
    "STOPPED",
    "FAILED",
]


@dataclass(frozen=True, slots=True)
class OptimizerWorkspaceState:
    """State model of an active Optimizer workspace session."""

    project_id: str
    settings: OptimizationSettingsSnapshot
    status: OptimizerStatus
    progress_pct: float
    evaluations_completed: int
    evaluations_total: int
    best_fitness: float
    active_result_tab: str

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary representation."""
        return {
            "project_id": self.project_id,
            "settings": self.settings.to_dict(),
            "status": self.status,
            "progress_pct": self.progress_pct,
            "evaluations_completed": self.evaluations_completed,
            "evaluations_total": self.evaluations_total,
            "best_fitness": self.best_fitness,
            "active_result_tab": self.active_result_tab,
        }


class AppOptimizerService:
    """Top-level workspace service coordinating optimizer workflows."""

    def __init__(self) -> None:
        """Initialize workspace service with attached sub-services."""
        self._states: dict[str, OptimizerWorkspaceState] = {}
        self.profile_service = ResultsOptimizationProfileService()
        self.sequential_service = ResultsSequentialOptimizationService()
        self.spp_service = ResultsSysParamPermutationService()
        self.wf_service = ResultsWalkForwardService()
        self.wf_fitness_service = FitnessMethodWFResultService()

    def get_state(self, project_id: str) -> StandardResponse[OptimizerWorkspaceState]:
        """Retrieve current workspace state for project.

        Args:
            project_id: Project identifier.

        Returns:
            StandardResponse containing OptimizerWorkspaceState.
        """
        state = self._states.get(project_id)
        if state is None:
            default_settings = OptimizationSettingsSnapshot()
            state = OptimizerWorkspaceState(
                project_id=project_id,
                settings=default_settings,
                status="IDLE",
                progress_pct=0.0,
                evaluations_completed=0,
                evaluations_total=0,
                best_fitness=0.0,
                active_result_tab="OptimizationProfile",
            )
            self._states[project_id] = state

        logger.debug(
            "Retrieved workspace state for %s: status=%s", project_id, state.status
        )
        return wrap_response(
            request_id=f"req_{project_id}_get_state",
            data=state,
            json_payload=state.to_dict(),
        )

    def save_settings(
        self, project_id: str, settings: OptimizationSettingsSnapshot
    ) -> StandardResponse[OptimizerWorkspaceState]:
        """Update and save optimization settings for project.

        Args:
            project_id: Project identifier.
            settings: Optimization settings snapshot.

        Returns:
            StandardResponse containing updated OptimizerWorkspaceState.
        """
        tests_info = SettingsOptimizationService.get_number_of_tests(settings)
        evals_total = int(tests_info["evaluations_total"])

        current_state = self._states.get(project_id)
        current_status = current_state.status if current_state else "IDLE"
        tab = (
            current_state.active_result_tab if current_state else "OptimizationProfile"
        )

        new_state = OptimizerWorkspaceState(
            project_id=project_id,
            settings=settings,
            status=current_status,
            progress_pct=0.0,
            evaluations_completed=0,
            evaluations_total=evals_total,
            best_fitness=0.0,
            active_result_tab=tab,
        )
        self._states[project_id] = new_state
        logger.info(
            "Saved settings for %s with %d total evaluations", project_id, evals_total
        )

        return wrap_response(
            request_id=f"req_{project_id}_save_settings",
            data=new_state,
            json_payload=new_state.to_dict(),
        )

    def start(self, project_id: str) -> StandardResponse[OptimizerWorkspaceState]:
        """Start optimization execution for project.

        Args:
            project_id: Project identifier.

        Returns:
            StandardResponse containing updated OptimizerWorkspaceState.
        """
        state_resp = self.get_state(project_id)
        current_state = state_resp.data
        settings = current_state.settings

        logger.info(
            "Starting optimization run for %s (%s)",
            project_id,
            settings.optimization_type,
        )

        # Transition to RUNNING
        running_state = OptimizerWorkspaceState(
            project_id=project_id,
            settings=settings,
            status="RUNNING",
            progress_pct=10.0,
            evaluations_completed=0,
            evaluations_total=current_state.evaluations_total,
            best_fitness=0.0,
            active_result_tab=current_state.active_result_tab,
        )
        self._states[project_id] = running_state

        try:
            summary = TaskOptimizeRunner.execute(project_id, settings)
            completed_state = OptimizerWorkspaceState(
                project_id=project_id,
                settings=settings,
                status="COMPLETED",
                progress_pct=100.0,
                evaluations_completed=summary.evaluations_completed,
                evaluations_total=summary.evaluations_completed,
                best_fitness=summary.best_fitness,
                active_result_tab=current_state.active_result_tab,
            )
            self._states[project_id] = completed_state
            logger.info(
                "Optimization COMPLETED for %s: %d evals",
                project_id,
                summary.evaluations_completed,
            )
            return wrap_response(
                request_id=f"req_{project_id}_start",
                data=completed_state,
                json_payload=completed_state.to_dict(),
            )
        except DomainError as err:
            logger.exception("Optimization failed for %s: %s", project_id, err.message)
            failed_state = OptimizerWorkspaceState(
                project_id=project_id,
                settings=settings,
                status="FAILED",
                progress_pct=0.0,
                evaluations_completed=0,
                evaluations_total=current_state.evaluations_total,
                best_fitness=0.0,
                active_result_tab=current_state.active_result_tab,
            )
            self._states[project_id] = failed_state
            raise

    def pause(self, project_id: str) -> StandardResponse[OptimizerWorkspaceState]:
        """Pause active optimization session."""
        state = self.get_state(project_id).data
        if state.status != "RUNNING":
            raise DomainError(
                code="OPTIMIZER_CANNOT_PAUSE",
                message=f"Cannot pause optimizer in status: {state.status}",
            )
        paused_state = OptimizerWorkspaceState(
            project_id=project_id,
            settings=state.settings,
            status="PAUSED",
            progress_pct=state.progress_pct,
            evaluations_completed=state.evaluations_completed,
            evaluations_total=state.evaluations_total,
            best_fitness=state.best_fitness,
            active_result_tab=state.active_result_tab,
        )
        self._states[project_id] = paused_state
        return wrap_response(
            request_id=f"req_{project_id}_pause",
            data=paused_state,
            json_payload=paused_state.to_dict(),
        )

    def resume(self, project_id: str) -> StandardResponse[OptimizerWorkspaceState]:
        """Resume paused optimization session."""
        state = self.get_state(project_id).data
        if state.status != "PAUSED":
            raise DomainError(
                code="OPTIMIZER_CANNOT_RESUME",
                message=f"Cannot resume optimizer in status: {state.status}",
            )
        resumed_state = OptimizerWorkspaceState(
            project_id=project_id,
            settings=state.settings,
            status="RUNNING",
            progress_pct=state.progress_pct,
            evaluations_completed=state.evaluations_completed,
            evaluations_total=state.evaluations_total,
            best_fitness=state.best_fitness,
            active_result_tab=state.active_result_tab,
        )
        self._states[project_id] = resumed_state
        return wrap_response(
            request_id=f"req_{project_id}_resume",
            data=resumed_state,
            json_payload=resumed_state.to_dict(),
        )

    def stop(self, project_id: str) -> StandardResponse[OptimizerWorkspaceState]:
        """Stop optimization session."""
        state = self.get_state(project_id).data
        stopped_state = OptimizerWorkspaceState(
            project_id=project_id,
            settings=state.settings,
            status="STOPPED",
            progress_pct=state.progress_pct,
            evaluations_completed=state.evaluations_completed,
            evaluations_total=state.evaluations_total,
            best_fitness=state.best_fitness,
            active_result_tab=state.active_result_tab,
        )
        self._states[project_id] = stopped_state
        return wrap_response(
            request_id=f"req_{project_id}_stop",
            data=stopped_state,
            json_payload=stopped_state.to_dict(),
        )
