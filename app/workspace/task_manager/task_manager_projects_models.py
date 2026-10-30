"""Task Manager Projects domain models and data transfer structures.

Description:
    Provides typed models for project representations, validation verdicts,
    summaries, and symbol modification payloads in the Task Manager workspace.

Purpose:
    FEAT-TM-PROJ-MODELS: Native JSON persistence and validation models.

Key Capabilities:
    FR-TM-PROJ-INFO: Typed ProjectInfo and ProjectSummary representations.
    FR-TM-PROJ-VALIDATION: Structured project validation outcome model.
    FR-TM-PROJ-SYMBOLS: Typed symbol migration items and list models.

Python API Usage:
    ```python
    from app.workspace.task_manager.task_manager_projects_models import (
        ProjectInfo,
        ProjectSummary,
        ProjectValidationResult,
    )

    info = ProjectInfo(name="TrendHunter", tasks=[])
    summary = ProjectSummary(project_name="TrendHunter", tasks_count=0)
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
class ModifySymbolItem:
    """A symbol replacement pair."""

    symbol_from: str
    symbol_to: str

    def to_dict(self) -> dict[str, str]:
        """Convert item to dictionary matching donor REST representation."""
        return {
            "symbolFrom": self.symbol_from,
            "symbolTo": self.symbol_to,
        }


@dataclass(slots=True)
class ProjectValidationResult:
    """Outcome of validating a project file."""

    valid: bool
    stage: str
    error: str | None = None
    success: str = "ok"

    def to_dict(self) -> dict[str, Any]:
        """Convert validation result to JSON-serializable dictionary."""
        result: dict[str, Any] = {
            "valid": self.valid,
            "stage": self.stage,
            "success": self.success,
        }
        if self.error is not None:
            result["error"] = self.error
        return result


@dataclass(slots=True)
class ProjectSummary:
    """Summary of a project for list operations."""

    project_name: str
    tasks_count: int
    active: bool = True
    is_app_project: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert summary to dictionary matching donor REST expectations."""
        return {
            "projectName": self.project_name,
            "tasksCount": self.tasks_count,
            "active": self.active,
            "isAppProject": self.is_app_project,
        }


@dataclass(slots=True)
class ProjectInfo:
    """Full in-memory project configuration."""

    name: str
    active: bool = True
    tasks: list[dict[str, Any]] = field(default_factory=list)
    settings: dict[str, Any] = field(default_factory=dict)
    conditions: list[dict[str, Any]] = field(default_factory=list)
    is_app_project: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert project to JSON dictionary."""
        return {
            "name": self.name,
            "active": self.active,
            "tasks": self.tasks,
            "settings": self.settings,
            "conditions": self.conditions,
            "is_app_project": self.is_app_project,
        }
