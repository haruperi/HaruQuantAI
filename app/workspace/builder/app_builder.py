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

from dataclasses import dataclass, field
from typing import Any, Literal

from app.core.host.logging import get_logger
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
from app.workspace.builder.task_build import TaskBuildRunner

logger = get_logger(__name__)

BuilderStatus = Literal["IDLE", "RUNNING", "PAUSED", "COMPLETED", "STOPPED", "FAILED"]


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

    def to_dict(self) -> dict[str, Any]:
        """Convert state snapshot to dictionary."""
        return {
            "project_id": self.project_id,
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

    def __init__(self) -> None:
        """Initialize service with memory state store."""
        self._states: dict[str, BuilderWorkspaceState] = {}

    def get_state(self, project_id: str) -> StandardResponse[BuilderWorkspaceState]:
        """Retrieve or initialize the Builder workspace state for a project.

        Args:
            project_id: Project identifier.

        Returns:
            StandardResponse containing BuilderWorkspaceState.
        """
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

    def start(self, project_id: str) -> StandardResponse[BuilderWorkspaceState]:
        """Start strategy generation run for a project.

        Args:
            project_id: Project identifier.

        Returns:
            StandardResponse containing updated BuilderWorkspaceState.
        """
        logger.debug("Starting builder for project=%s", project_id)
        current = self._states.get(
            project_id, BuilderWorkspaceState(project_id=project_id)
        )
        summary = TaskBuildRunner.execute(
            project_id=project_id,
            what_to_build=current.what_to_build,
            genetic_options=current.genetic_options,
            blocks=current.blocks,
            parts_to_improve=current.parts_to_improve,
            rankings=current.rankings,
        )
        new_state = BuilderWorkspaceState(
            project_id=project_id,
            what_to_build=current.what_to_build,
            genetic_options=current.genetic_options,
            blocks=current.blocks,
            parts_to_improve=current.parts_to_improve,
            rankings=current.rankings,
            status="RUNNING",
            generated_count=summary.candidates_evaluated,
            accepted_count=summary.candidates_accepted,
            rejected_count=summary.candidates_rejected,
            generations_completed=summary.generations_completed,
        )
        self._states[project_id] = new_state
        return wrap_response(
            request_id=f"builder-start-{project_id}",
            data=new_state,
            json_payload=new_state.to_dict(),
        )

    def pause(self, project_id: str) -> StandardResponse[BuilderWorkspaceState]:
        """Pause active generation run for a project."""
        logger.debug("Pausing builder for project=%s", project_id)
        current = self._states.get(
            project_id, BuilderWorkspaceState(project_id=project_id)
        )
        new_state = BuilderWorkspaceState(
            project_id=project_id,
            what_to_build=current.what_to_build,
            genetic_options=current.genetic_options,
            blocks=current.blocks,
            parts_to_improve=current.parts_to_improve,
            rankings=current.rankings,
            status="PAUSED",
            generated_count=current.generated_count,
            accepted_count=current.accepted_count,
            rejected_count=current.rejected_count,
            generations_completed=current.generations_completed,
        )
        self._states[project_id] = new_state
        return wrap_response(
            request_id=f"builder-pause-{project_id}",
            data=new_state,
            json_payload=new_state.to_dict(),
        )

    def resume(self, project_id: str) -> StandardResponse[BuilderWorkspaceState]:
        """Resume paused generation run for a project."""
        logger.debug("Resuming builder for project=%s", project_id)
        current = self._states.get(
            project_id, BuilderWorkspaceState(project_id=project_id)
        )
        new_state = BuilderWorkspaceState(
            project_id=project_id,
            what_to_build=current.what_to_build,
            genetic_options=current.genetic_options,
            blocks=current.blocks,
            parts_to_improve=current.parts_to_improve,
            rankings=current.rankings,
            status="RUNNING",
            generated_count=current.generated_count,
            accepted_count=current.accepted_count,
            rejected_count=current.rejected_count,
            generations_completed=current.generations_completed,
        )
        self._states[project_id] = new_state
        return wrap_response(
            request_id=f"builder-resume-{project_id}",
            data=new_state,
            json_payload=new_state.to_dict(),
        )

    def stop(self, project_id: str) -> StandardResponse[BuilderWorkspaceState]:
        """Stop strategy generation run for a project."""
        logger.debug("Stopping builder for project=%s", project_id)
        current = self._states.get(
            project_id, BuilderWorkspaceState(project_id=project_id)
        )
        new_state = BuilderWorkspaceState(
            project_id=project_id,
            what_to_build=current.what_to_build,
            genetic_options=current.genetic_options,
            blocks=current.blocks,
            parts_to_improve=current.parts_to_improve,
            rankings=current.rankings,
            status="STOPPED",
            generated_count=current.generated_count,
            accepted_count=current.accepted_count,
            rejected_count=current.rejected_count,
            generations_completed=current.generations_completed,
        )
        self._states[project_id] = new_state
        return wrap_response(
            request_id=f"builder-stop-{project_id}",
            data=new_state,
            json_payload=new_state.to_dict(),
        )
