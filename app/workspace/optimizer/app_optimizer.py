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

from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.lib.responses import StandardResponse
from app.workspace.home.service import HomeService
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

logger = get_logger(__name__)

OptimizerStatus = str


@dataclass(frozen=True, slots=True)
class OptimizerWorkspaceState:
    """State model of an active Optimizer workspace session."""

    project_id: str
    settings: OptimizationSettingsSnapshot
    status: OptimizerStatus
    progress_pct: float
    evaluations_completed: int
    evaluations_total: int
    best_fitness: float | None
    active_result_tab: str

    job_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary representation."""
        return {
            "project_id": self.project_id,
            "job_id": self.job_id,
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

    def __init__(self, home_service: HomeService | None = None) -> None:
        """Initialize workspace service with attached sub-services."""
        self._states: dict[str, OptimizerWorkspaceState] = {}
        self._home_service = home_service
        self.profile_service = ResultsOptimizationProfileService(
            home_service.result_store if home_service else None
        )
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
        if self._home_service is not None:
            return self.get_job_state(project_id)
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
                best_fitness=None,
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
            best_fitness=None,
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

    def save_native_settings(
        self,
        project_id: str,
        task_id: str,
        settings: Mapping[str, Any],
        expected_revision: int,
    ) -> dict[str, Any]:
        """Persist native configuration through the shared revision owner."""
        return self._host().save_project_settings(
            project_id, task_id, settings, expected_revision
        )

    def _host(self) -> HomeService:
        """Require an injected project/job authority without opening a database."""
        if self._home_service is None:
            raise DomainError(
                code="EXECUTION_CONTEXT_REQUIRED",
                message="Inject the shared Home project and job service",
            )
        return self._home_service

    def _apply_action(
        self,
        project_id: str,
        action: str,
        task_id: str | None = None,
        expected_revision: int | None = None,
        job_id: str | None = None,
    ) -> StandardResponse[OptimizerWorkspaceState]:
        """Delegate admission and transitions to the shared lifecycle owner."""
        self._host().engine_action(
            project_id, action, task_id, expected_revision, job_id
        )
        logger.info(
            "FR-optimizer-lifecycle: delegated %s to shared project authority", action
        )
        return self.get_job_state(project_id, job_id)

    def start(
        self,
        project_id: str,
        *,
        task_id: str | None = None,
        expected_revision: int | None = None,
    ) -> StandardResponse[OptimizerWorkspaceState]:
        """Submit the selected saved revision through the shared execution owner."""
        return self._apply_action(project_id, "start", task_id, expected_revision)

    def pause(
        self, project_id: str, *, job_id: str | None = None
    ) -> StandardResponse[OptimizerWorkspaceState]:
        """Pause the explicitly selected real job."""
        return self._apply_action(project_id, "pause", job_id=job_id)

    def resume(
        self, project_id: str, *, job_id: str | None = None
    ) -> StandardResponse[OptimizerWorkspaceState]:
        """Resume the explicitly selected real job."""
        return self._apply_action(project_id, "resume", job_id=job_id)

    def stop(
        self, project_id: str, *, job_id: str | None = None
    ) -> StandardResponse[OptimizerWorkspaceState]:
        """Request cooperative cancellation of the explicitly selected job."""
        return self._apply_action(project_id, "stop", job_id=job_id)

    def get_job_state(
        self,
        project_id: str,
        job_id: str | None = None,
    ) -> StandardResponse[OptimizerWorkspaceState]:
        """Project actual job observations and completed evaluation receipts."""
        observation = self._host().get_engine_status(project_id, job_id)
        receipt = observation.get("result") or {}
        current = self._states.get(project_id) or OptimizerWorkspaceState(
            project_id,
            OptimizationSettingsSnapshot(),
            "IDLE",
            0,
            0,
            0,
            None,
            "OptimizationProfile",
        )
        state = replace(
            current,
            status=str(observation["status"]),
            job_id=observation["job_id"],
            progress_pct=float(observation["progress"]),
            evaluations_completed=int(receipt.get("candidates_evaluated", 0)),
            best_fitness=receipt.get("best_fitness"),
        )
        self._states[project_id] = state
        return wrap_response(
            request_id=f"optimizer-job-{project_id}",
            data=state,
            json_payload=state.to_dict(),
        )
