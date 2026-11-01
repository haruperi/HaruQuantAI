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

from dataclasses import dataclass, field
from typing import Any, Literal

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.lib.responses import StandardResponse
from app.workspace.retester.settings_auto_retest_data import AutoRetestDataSettings
from app.workspace.retester.settings_cross_checks import CrossChecksSettingsSnapshot
from app.workspace.retester.settings_what_to_retest import WhatToRetestSettings
from app.workspace.retester.task_retest import TaskRetestRunner

logger = get_logger(__name__)

RetesterStatus = Literal["IDLE", "RUNNING", "PAUSED", "COMPLETED", "STOPPED", "FAILED"]


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

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary."""
        return {
            "project_id": self.project_id,
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

    def __init__(self) -> None:
        self._states: dict[str, RetesterWorkspaceState] = {}
        self._mock_databanks: dict[str, dict[str, list[str]]] = {}

    def _get_or_create_state(self, project_id: str) -> RetesterWorkspaceState:
        if project_id not in self._states:
            self._states[project_id] = RetesterWorkspaceState(project_id=project_id)
        return self._states[project_id]

    def set_mock_databank(
        self, project_id: str, databank_name: str, strategies: list[str]
    ) -> None:
        """Helper to inject databank strategies for integration tests."""
        if project_id not in self._mock_databanks:
            self._mock_databanks[project_id] = {}
        self._mock_databanks[project_id][databank_name] = list(strategies)

    def get_state(self, project_id: str) -> StandardResponse[dict[str, Any]]:
        """Get current Retester workspace state for a project."""
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

    def start(self, project_id: str) -> StandardResponse[dict[str, Any]]:
        """Start or execute strategy retest."""
        curr = self._get_or_create_state(project_id)
        if curr.status == "RUNNING":
            raise DomainError(
                code="RETESTER_ALREADY_RUNNING",
                message=f"Retester for project {project_id} is already running",
            )

        db_strategies = self._mock_databanks.get(project_id, {"Results": ["s1", "s2"]})

        # Transition to RUNNING then COMPLETED
        summary = TaskRetestRunner.execute(
            project_id=project_id,
            what_to_retest=curr.what_to_retest,
            data_settings=curr.data_settings,
            cross_checks=curr.cross_checks,
            databank_strategies=db_strategies,
        )

        final_state = RetesterWorkspaceState(
            project_id=project_id,
            what_to_retest=curr.what_to_retest,
            data_settings=curr.data_settings,
            cross_checks=curr.cross_checks,
            status="COMPLETED",
            progress_pct=100.0,
            processed_count=summary.processed,
            accepted_count=summary.passed,
            rejected_count=summary.failed,
        )
        self._states[project_id] = final_state
        logger.info(
            "FR-retester-workspace-lifecycle: completed retest for %s: %d processed",
            project_id,
            summary.processed,
        )
        return StandardResponse(
            request_id=f"req_start_{project_id}",
            data=final_state.to_dict(),
        )

    def pause(self, project_id: str) -> StandardResponse[dict[str, Any]]:
        """Pause running retest."""
        curr = self._get_or_create_state(project_id)
        new_state = RetesterWorkspaceState(
            project_id=project_id,
            what_to_retest=curr.what_to_retest,
            data_settings=curr.data_settings,
            cross_checks=curr.cross_checks,
            status="PAUSED",
            progress_pct=curr.progress_pct,
            processed_count=curr.processed_count,
            accepted_count=curr.accepted_count,
            rejected_count=curr.rejected_count,
        )
        self._states[project_id] = new_state
        return StandardResponse(
            request_id=f"req_pause_{project_id}", data=new_state.to_dict()
        )

    def resume(self, project_id: str) -> StandardResponse[dict[str, Any]]:
        """Resume paused retest."""
        curr = self._get_or_create_state(project_id)
        new_state = RetesterWorkspaceState(
            project_id=project_id,
            what_to_retest=curr.what_to_retest,
            data_settings=curr.data_settings,
            cross_checks=curr.cross_checks,
            status="RUNNING",
            progress_pct=curr.progress_pct,
            processed_count=curr.processed_count,
            accepted_count=curr.accepted_count,
            rejected_count=curr.rejected_count,
        )
        self._states[project_id] = new_state
        return StandardResponse(
            request_id=f"req_resume_{project_id}", data=new_state.to_dict()
        )

    def stop(self, project_id: str) -> StandardResponse[dict[str, Any]]:
        """Stop active retest."""
        curr = self._get_or_create_state(project_id)
        new_state = RetesterWorkspaceState(
            project_id=project_id,
            what_to_retest=curr.what_to_retest,
            data_settings=curr.data_settings,
            cross_checks=curr.cross_checks,
            status="STOPPED",
            progress_pct=curr.progress_pct,
            processed_count=curr.processed_count,
            accepted_count=curr.accepted_count,
            rejected_count=curr.rejected_count,
        )
        self._states[project_id] = new_state
        return StandardResponse(
            request_id=f"req_stop_{project_id}", data=new_state.to_dict()
        )
