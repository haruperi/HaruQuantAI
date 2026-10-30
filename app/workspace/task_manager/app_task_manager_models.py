"""Task Manager App pipeline execution models and status structures.

Description:
    Provides typed models for project execution states, task iterations,
    and progress publisher statistics in the Task Manager workspace.

Purpose:
    FEAT-TM-APP-MODELS: Pipeline execution models and status representations.

Key Capabilities:
    FR-TM-APP-STATUS: Execution status constants and state tracking.
    FR-TM-APP-ITERATIONS: Per-task iteration counters and history.
    FR-TM-APP-PUBLISHER: Project stats publisher data transfer structures.

Python API Usage:
    ```python
    from app.workspace.task_manager.app_task_manager_models import (
        ExecutionStatus,
        ProjectExecutionState,
        TaskIterationRecord,
    )

    state = ProjectExecutionState(
        project_name="Alpha",
        running_status=ExecutionStatus.RUNNING,
        active_task="Build 1",
    )
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/task_manager/ -q
    ```
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ExecutionStatus(StrEnum):
    """Lifecycle status of a project execution pipeline."""

    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"
    ERROR = "error"


@dataclass(slots=True)
class TaskIterationRecord:
    """Record of runs/iterations for an individual task in a project."""

    task_name: str
    iterations: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert iteration record to dictionary matching donor publisher."""
        return {
            "taskName": self.task_name,
            "iterations": self.iterations,
        }


@dataclass(slots=True)
class ProjectExecutionState:
    """Runtime execution snapshot of a project."""

    project_name: str
    running_status: ExecutionStatus = ExecutionStatus.STOPPED
    active_task: str | None = None
    tasks_iterations: list[TaskIterationRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary matching TaskManagerProgressPublisher."""
        return {
            "projectName": self.project_name,
            "runningStatus": self.running_status.value,
            "activeTask": self.active_task,
            "tasksIterations": [t.to_dict() for t in self.tasks_iterations],
        }
