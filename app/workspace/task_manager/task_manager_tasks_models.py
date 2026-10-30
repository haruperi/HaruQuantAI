"""Task Manager Tasks models and available task declarations.

Description:
    Provides typed models for task configurations, task manipulation requests,
    and available task descriptors in the Task Manager task graph.

Purpose:
    FEAT-TM-TASKS-MODELS: Models for task items and task catalog.

Key Capabilities:
    FR-TM-TASK-CONFIG: Structured TaskConfig representation.
    FR-TM-TASK-AVAILABLE: Catalog of supported available task types.
    FR-TM-TASK-REQUESTS: Move, rename, clone, and activation request models.

Python API Usage:
    ```python
    from app.workspace.task_manager.task_manager_tasks_models import (
        AvailableTask,
        TaskConfig,
    )

    task = TaskConfig(
        task_name="Build 1",
        task_type="Build",
        task_title="Build strategies",
    )
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/task_manager/ -q
    ```
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AvailableTask:
    """Descriptor of a task type available in the catalog."""

    type: str
    name: str

    def to_dict(self) -> dict[str, str]:
        """Convert available task descriptor to dictionary."""
        return {
            "type": self.type,
            "name": self.name,
        }


@dataclass(slots=True)
class TaskConfig:
    """Configuration and state of a single task in a project."""

    task_name: str
    task_type: str
    task_title: str
    active: bool = True
    config: dict[str, Any] = field(default_factory=dict)
    iterations: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert task configuration to dictionary."""
        return {
            "name": self.task_name,
            "type": self.task_type,
            "title": self.task_title,
            "taskName": self.task_name,
            "taskType": self.task_type,
            "taskTitle": self.task_title,
            "active": self.active,
            "config": self.config,
            "iterations": self.iterations,
        }


@dataclass(slots=True)
class TaskMoveRequest:
    """Request payload to move a task within a project."""

    project_name: str
    task_name: str
    to_index: int


@dataclass(slots=True)
class TaskRenameRequest:
    """Request payload to rename a task title."""

    project_name: str
    task_name: str
    task_title: str


@dataclass(slots=True)
class TaskActivateRequest:
    """Request payload to activate or deactivate a task."""

    project_name: str
    task_name: str
    active: bool


@dataclass(slots=True)
class TaskCloneRequest:
    """Request payload to clone an existing task."""

    project_name: str
    task_name: str
    position: str = "end"
