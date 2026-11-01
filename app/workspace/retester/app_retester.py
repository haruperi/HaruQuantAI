"""Top-level Retester workspace controller and service coordinator.

Description:
    Coordinates candidate strategy selection (SettingsWhatToRetest), market data
    overrides (SettingsAutoRetestData), robustness checks (SettingsCrossChecks),
    task execution (TaskRetestRunner), and workspace UI lifecycle states.

Purpose:
    FEAT-RETESTER-WORKSPACE-SHELL: Retester root API coordinator and state manager.

Key Capabilities:
    - FR-retester-workspace-state: Manage workspace state and transitions
      (IDLE, RUNNING, PAUSED, COMPLETED, STOPPED, FAILED).
    - FR-retester-workspace-lifecycle: Control retest execution via
      start/pause/resume/stop.

Python API Usage:
    from app.workspace.retester.app_retester import AppRetesterService
    service = AppRetesterService()
    state = service.get_state("proj_1")
    res = service.start("proj_1")

CLI Usage:
    python -m app.cli retest state --project proj_1
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.lib.responses import StandardResponse
from app.workspace.home.service import HomeService
from app.workspace.retester.settings_auto_retest_data import AutoRetestDataSettings
from app.workspace.retester.settings_cross_checks import CrossChecksSettingsSnapshot
from app.workspace.retester.settings_what_to_retest import WhatToRetestSettings

logger = get_logger(__name__)

RetesterStatus = str


@dataclass(frozen=True, slots=True)
class RetesterWorkspaceState:
    """Active state of the Retester workspace for a project."""

    project_id: str
    what_to_retest: WhatToRetestSettings = field(default_factory=WhatToRetestSettings)
    data_settings: AutoRetestDataSettings = field(
        default_factory=AutoRetestDataSettings
    )
    cross_checks: CrossChecksSettingsSnapshot = field(
        default_factory=CrossChecksSettingsSnapshot
    )
    status: RetesterStatus = "IDLE"
    progress_pct: float = 0.0
    processed_count: int = 0
    accepted_count: int = 0
    rejected_count: int = 0

    job_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary."""
        return {
            "project_id": self.project_id,
            "job_id": self.job_id,
            "what_to_retest": self.what_to_retest.to_dict(),
            "data_settings": self.data_settings.to_dict(),
            "cross_checks": self.cross_checks.to_dict(),
            "status": self.status,
            "progress_pct": self.progress_pct,
            "processed_count": self.processed_count,
            "accepted_count": self.accepted_count,
            "rejected_count": self.rejected_count,
        }


class AppRetesterService:
    """Workspace service coordinating strategy retests and robustness evaluations."""

    def __init__(self, home_service: HomeService | None = None) -> None:
        self._states: dict[str, RetesterWorkspaceState] = {}
        self._home_service = home_service

    def _get_or_create_state(self, project_id: str) -> RetesterWorkspaceState:
        if project_id not in self._states:
            self._states[project_id] = RetesterWorkspaceState(project_id=project_id)
        return self._states[project_id]

    def get_state(self, project_id: str) -> StandardResponse[dict[str, Any]]:
        """Get current Retester workspace state for a project."""
        if self._home_service is not None:
            return self.get_job_state(project_id)
        state = self._get_or_create_state(project_id)
        logger.info(
            "FR-retester-workspace-state: project %s state is %s",
            project_id,
            state.status,
        )
        return StandardResponse(
            request_id=f"req_state_{project_id}",
            data=state.to_dict(),
        )

    def save_settings(
        self,
        project_id: str,
        what_to_retest: WhatToRetestSettings | None = None,
        data_settings: AutoRetestDataSettings | None = None,
        cross_checks: CrossChecksSettingsSnapshot | None = None,
    ) -> StandardResponse[dict[str, Any]]:
        """Update configured retest settings."""
        curr = self._get_or_create_state(project_id)
        new_state = RetesterWorkspaceState(
            project_id=project_id,
            what_to_retest=what_to_retest or curr.what_to_retest,
            data_settings=data_settings or curr.data_settings,
            cross_checks=cross_checks or curr.cross_checks,
            status=curr.status,
            progress_pct=curr.progress_pct,
            processed_count=curr.processed_count,
            accepted_count=curr.accepted_count,
            rejected_count=curr.rejected_count,
        )
        self._states[project_id] = new_state
        logger.info("FR-retester-workspace-state: updated settings for %s", project_id)
        return StandardResponse(
            request_id=f"req_save_{project_id}",
            data=new_state.to_dict(),
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
    ) -> StandardResponse[dict[str, Any]]:
        """Delegate admission and transitions to the shared lifecycle owner."""
        self._host().engine_action(
            project_id, action, task_id, expected_revision, job_id
        )
        logger.info(
            "FR-retester-lifecycle: delegated %s to shared project authority", action
        )
        return self.get_job_state(project_id, job_id)

    def start(
        self,
        project_id: str,
        *,
        task_id: str | None = None,
        expected_revision: int | None = None,
    ) -> StandardResponse[dict[str, Any]]:
        """Submit the selected saved revision through the shared execution owner."""
        return self._apply_action(project_id, "start", task_id, expected_revision)

    def pause(
        self, project_id: str, *, job_id: str | None = None
    ) -> StandardResponse[dict[str, Any]]:
        """Pause the explicitly selected real job."""
        return self._apply_action(project_id, "pause", job_id=job_id)

    def resume(
        self, project_id: str, *, job_id: str | None = None
    ) -> StandardResponse[dict[str, Any]]:
        """Resume the explicitly selected real job."""
        return self._apply_action(project_id, "resume", job_id=job_id)

    def stop(
        self, project_id: str, *, job_id: str | None = None
    ) -> StandardResponse[dict[str, Any]]:
        """Request cooperative cancellation of the explicitly selected job."""
        return self._apply_action(project_id, "stop", job_id=job_id)

    def get_job_state(
        self,
        project_id: str,
        job_id: str | None = None,
    ) -> StandardResponse[dict[str, Any]]:
        """Project actual job observations and completed evaluation receipts."""
        observation = self._host().get_engine_status(project_id, job_id)
        receipt = observation.get("result") or {}
        current = self._get_or_create_state(project_id)
        state = replace(
            current,
            status=str(observation["status"]),
            job_id=observation["job_id"],
            progress_pct=float(observation["progress"]),
            processed_count=int(receipt.get("candidates_evaluated", 0)),
            accepted_count=int(receipt.get("candidates_accepted", 0)),
            rejected_count=int(receipt.get("candidates_rejected", 0)),
        )
        self._states[project_id] = state
        return StandardResponse(
            request_id=f"retester-job-{project_id}", data=state.to_dict()
        )
