"""Builder workspace orchestrator, state manager, and service lifecycle.

Description:
    Coordinates the complete Builder workspace state and lifecycle, maintaining
    project configuration, genetic settings, block selections, ranking conditions,
    and runtime execution status (IDLE, RUNNING, PAUSED, COMPLETED, STOPPED, FAILED)
    while updating strategy generation progress metrics.

Purpose:
    FEAT-BUILDER-APP-SERVICE: Top-level workspace controller and state lifecycle.

Key Capabilities:
    - FR-builder-state-model: Typed dataclass tracking comprehensive configuration.
    - FR-builder-lifecycle: State transitions for start, pause, resume, and stop.
    - FR-builder-persistence: Save settings and synchronize with underlying jobs.

Python API Usage:
    from app.workspace.builder.app_builder import AppBuilderService
    service = AppBuilderService()
    state = service.get_state("proj_1")

CLI Usage:
    python -c "from app.workspace.builder.app_builder import (
        AppBuilderService,
    ); print(1)"
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import Any

from app.core.host.logging import get_logger
from app.core.lib.errors import DomainError
from app.core.lib.responses import StandardResponse
from app.workspace.builder.common import wrap_response
from app.workspace.builder.genetic_defaults import (
    GeneticOptions,
    GeneticOptionsDefaults,
)
from app.workspace.builder.settings_blocks import BlocksSelectionSettings
from app.workspace.builder.settings_parts_to_improve import PartsToImproveSettings
from app.workspace.builder.settings_rankings import RankingsSettings
from app.workspace.builder.settings_what_to_build import WhatToBuildSettings
from app.workspace.home.service import HomeService

logger = get_logger(__name__)

BuilderStatus = str


@dataclass(frozen=True, slots=True)
class BuilderWorkspaceState:
    """Complete snapshot of Builder workspace state for a project."""

    project_id: str
    what_to_build: WhatToBuildSettings = field(default_factory=WhatToBuildSettings)
    genetic_options: GeneticOptionsDefaults = field(
        default_factory=lambda: GeneticOptions.defaults(in_sample_type=1)
    )
    blocks: BlocksSelectionSettings = field(default_factory=BlocksSelectionSettings)
    parts_to_improve: PartsToImproveSettings = field(
        default_factory=PartsToImproveSettings
    )
    rankings: RankingsSettings = field(default_factory=RankingsSettings)
    status: BuilderStatus = "IDLE"
    generated_count: int = 0
    accepted_count: int = 0
    rejected_count: int = 0
    generations_completed: int = 0

    job_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert state snapshot to dictionary."""
        return {
            "project_id": self.project_id,
            "job_id": self.job_id,
            "what_to_build": self.what_to_build.to_dict(),
            "genetic_options": {
                "population_size": self.genetic_options.population_size,
                "max_generations": self.genetic_options.max_generations,
                "crossover_probability": self.genetic_options.crossover_probability,
                "mutation_probability": (self.genetic_options.mutation_probability),
                "islands": self.genetic_options.islands,
                "evo_fitness_restart_type": (
                    self.genetic_options.evo_fitness_restart_type
                ),
            },
            "blocks": self.blocks.to_dict(),
            "parts_to_improve": self.parts_to_improve.to_dict(),
            "rankings": self.rankings.to_dict(),
            "status": self.status,
            "generated_count": self.generated_count,
            "accepted_count": self.accepted_count,
            "rejected_count": self.rejected_count,
            "generations_completed": self.generations_completed,
        }


class AppBuilderService:
    """Service managing project Builder workspaces and execution transitions."""

    def __init__(self, home_service: HomeService | None = None) -> None:
        """Initialize service with memory state store."""
        self._states: dict[str, BuilderWorkspaceState] = {}
        self._home_service = home_service

    def get_state(self, project_id: str) -> StandardResponse[BuilderWorkspaceState]:
        """Retrieve or initialize the Builder workspace state for a project.

        Args:
            project_id: Project identifier.

        Returns:
            StandardResponse containing BuilderWorkspaceState.
        """
        if self._home_service is not None:
            return self.get_job_state(project_id)
        logger.debug("Retrieving Builder state for project=%s", project_id)
        if project_id not in self._states:
            self._states[project_id] = BuilderWorkspaceState(project_id=project_id)

        state = self._states[project_id]
        return wrap_response(
            request_id=f"builder-state-{project_id}",
            data=state,
            json_payload=state.to_dict(),
        )

    def save_settings(  # noqa: PLR0917
        self,
        project_id: str,
        what_to_build: WhatToBuildSettings | None = None,
        genetic_options: GeneticOptionsDefaults | None = None,
        blocks: BlocksSelectionSettings | None = None,
        parts_to_improve: PartsToImproveSettings | None = None,
        rankings: RankingsSettings | None = None,
    ) -> StandardResponse[BuilderWorkspaceState]:
        """Save updated settings for a project Builder workspace.

        Args:
            project_id: Project identifier.
            what_to_build: Proposed WhatToBuildSettings.
            genetic_options: Proposed GeneticOptionsDefaults.
            blocks: Proposed BlocksSelectionSettings.
            parts_to_improve: Proposed PartsToImproveSettings.
            rankings: Proposed RankingsSettings.

        Returns:
            StandardResponse containing updated BuilderWorkspaceState.
        """
        current = self._states.get(
            project_id, BuilderWorkspaceState(project_id=project_id)
        )
        new_state = BuilderWorkspaceState(
            project_id=project_id,
            what_to_build=what_to_build or current.what_to_build,
            genetic_options=genetic_options or current.genetic_options,
            blocks=blocks or current.blocks,
            parts_to_improve=parts_to_improve or current.parts_to_improve,
            rankings=rankings or current.rankings,
            status=current.status,
            generated_count=current.generated_count,
            accepted_count=current.accepted_count,
            rejected_count=current.rejected_count,
            generations_completed=current.generations_completed,
        )
        self._states[project_id] = new_state
        return wrap_response(
            request_id=f"builder-save-{project_id}",
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
    ) -> StandardResponse[BuilderWorkspaceState]:
        """Delegate admission and transitions to the shared lifecycle owner."""
        self._host().engine_action(
            project_id, action, task_id, expected_revision, job_id
        )
        logger.info(
            "FR-builder-lifecycle: delegated %s to shared project authority", action
        )
        return self.get_job_state(project_id, job_id)

    def start(
        self,
        project_id: str,
        *,
        task_id: str | None = None,
        expected_revision: int | None = None,
    ) -> StandardResponse[BuilderWorkspaceState]:
        """Submit the selected saved revision through the shared execution owner."""
        return self._apply_action(project_id, "start", task_id, expected_revision)

    def pause(
        self, project_id: str, *, job_id: str | None = None
    ) -> StandardResponse[BuilderWorkspaceState]:
        """Pause the explicitly selected real job."""
        return self._apply_action(project_id, "pause", job_id=job_id)

    def resume(
        self, project_id: str, *, job_id: str | None = None
    ) -> StandardResponse[BuilderWorkspaceState]:
        """Resume the explicitly selected real job."""
        return self._apply_action(project_id, "resume", job_id=job_id)

    def stop(
        self, project_id: str, *, job_id: str | None = None
    ) -> StandardResponse[BuilderWorkspaceState]:
        """Request cooperative cancellation of the explicitly selected job."""
        return self._apply_action(project_id, "stop", job_id=job_id)

    def get_job_state(
        self,
        project_id: str,
        job_id: str | None = None,
    ) -> StandardResponse[BuilderWorkspaceState]:
        """Project actual job observations and completed evaluation receipts."""
        observation = self._host().get_engine_status(project_id, job_id)
        receipt = observation.get("result") or {}
        current = self._states.get(project_id, BuilderWorkspaceState(project_id))
        state = replace(
            current,
            status=str(observation["status"]),
            job_id=observation["job_id"],
            generated_count=int(receipt.get("candidates_evaluated", 0)),
            accepted_count=int(receipt.get("candidates_accepted", 0)),
            rejected_count=int(receipt.get("candidates_rejected", 0)),
        )
        self._states[project_id] = state
        return wrap_response(
            request_id=f"builder-job-{project_id}",
            data=state,
            json_payload=state.to_dict(),
        )
