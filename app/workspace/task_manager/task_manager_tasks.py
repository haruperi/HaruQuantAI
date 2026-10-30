"""Task Manager Tasks graph management and catalogue operations.

Description:
    Provides operations for task graph modification within projects: adding,
    removing, reordering, renaming, cloning, activating, and listing supported tasks.

Purpose:
    FEAT-TM-TASKS-ENGINE: Task graph manager for Task Manager projects.

Key Capabilities:
    FR-TM-TASK-CATALOGUE: Listing available task plugins matching donor registry.
    FR-TM-TASK-GRAPH-CRUD: Add, remove, and clone tasks in project graphs.
    FR-TM-TASK-ORDERING: Reorder and reparent tasks within pipeline sequences.
    FR-TM-TASK-ACTIVATION: Activate or deactivate tasks for execution.

Python API Usage:
    ```python
    from app.workspace.task_manager.task_manager_projects import (
        TaskManagerProjects,
    )
    from app.workspace.task_manager.task_manager_tasks import TaskManagerTasks

    proj_engine = TaskManagerProjects()
    proj_engine.create_project("Alpha")
    task_engine = TaskManagerTasks(proj_engine)
    task_engine.add_task("Alpha", "Build 1", "Build")
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/task_manager/ -q
    ```
"""

from __future__ import annotations

import copy
import logging
from collections.abc import Mapping
from typing import Any

from app.workspace.task_manager.task_manager_projects import (
    TaskManagerProjects,
)
from app.workspace.task_manager.task_manager_tasks_models import (
    AvailableTask,
    TaskConfig,
)

logger = logging.getLogger("haruquant.task_manager.tasks")

# Standard task catalogue matching StrategyQuant donor, sorted alphabetically
DEFAULT_AVAILABLE_TASKS: list[AvailableTask] = [
    AvailableTask(type="ApplyMassConfig", name="Apply mass config"),
    AvailableTask(type="AutomaticPortfolioBuilder", name="Automatic portfolio builder"),
    AvailableTask(type="AutomaticRetest", name="Automatic retest"),
    AvailableTask(type="Build", name="Build strategies"),
    AvailableTask(type="CallExternalScript", name="Call external script"),
    AvailableTask(type="ClearDatabanks", name="Clear databanks"),
    AvailableTask(type="CreatePortfolio", name="Create portfolio"),
    AvailableTask(type="CustomAnalysis", name="Custom analysis"),
    AvailableTask(type="DeleteFile", name="Delete file"),
    AvailableTask(type="Filtering", name="Filtering"),
    AvailableTask(type="GoToTask", name="Go to task"),
    AvailableTask(type="LoadFromFiles", name="Load from files"),
    AvailableTask(type="LogDatabankStats", name="Log databank stats"),
    AvailableTask(type="Notification", name="Notification"),
    AvailableTask(type="Optimize", name="Optimize strategies"),
    AvailableTask(type="Retest", name="Retest strategies"),
    AvailableTask(type="SaveToFiles", name="Save to files"),
    AvailableTask(type="StopAndStart", name="Stop & Start"),
    AvailableTask(type="UpdateData", name="Update data"),
    AvailableTask(type="WaitFor", name="Wait for user/file"),
]


class TaskManagerTasks:
    """Manages the task graph and operations within Task Manager projects."""

    def __init__(self, projects_engine: TaskManagerProjects) -> None:
        """Initialize the task manager with a project engine reference."""
        self._projects_engine = projects_engine
        self._available_tasks: list[AvailableTask] = sorted(
            DEFAULT_AVAILABLE_TASKS, key=lambda t: t.name
        )
        logger.info(
            "Initialized TaskManagerTasks with %d tasks in catalogue",
            len(self._available_tasks),
        )

    def get_available_tasks(self) -> list[AvailableTask]:
        """Return the sorted list of available task types."""
        return list(self._available_tasks)

    def _find_task_index(self, tasks: list[dict[str, Any]], task_name: str) -> int:
        """Locate index of task by its unique task name."""
        for idx, task in enumerate(tasks):
            name = task.get("task_name") or task.get("name") or task.get("taskName")
            if name == task_name:
                return idx
        return -1

    def add_task(
        self,
        project_name: str,
        task_name: str,
        task_type: str,
        *,
        task_title: str | None = None,
        index: int = -1,
        config: Mapping[str, Any] | None = None,
    ) -> TaskConfig:
        """Add a new task to a project.

        Args:
            project_name: Name of target project.
            task_name: Unique name for the task in the project.
            task_type: Type identifier of the task.
            task_title: Optional human-readable title (defaults to task_name).
            index: Position to insert (-1 appends to the end).
            config: Initial settings mapping for the task.

        Returns:
            The created TaskConfig.

        Raises:
            KeyError: If project does not exist.
            ValueError: If a task with the same name already exists.
        """
        project = self._projects_engine.get_project(project_name)
        if self._find_task_index(project.tasks, task_name) >= 0:
            logger.error(
                "Task '%s' already exists in project '%s'",
                task_name,
                project_name,
            )
            raise ValueError(f"Task with name '{task_name}' already exists.")

        title = task_title or task_name
        task_cfg = TaskConfig(
            task_name=task_name,
            task_type=task_type,
            task_title=title,
            active=True,
            config=dict(config) if config else {},
            iterations=0,
        )

        task_dict = task_cfg.to_dict()
        if 0 <= index < len(project.tasks):
            project.tasks.insert(index, task_dict)
        else:
            project.tasks.append(task_dict)

        logger.info(
            "Added task '%s' (%s) to project '%s'",
            task_name,
            task_type,
            project_name,
        )
        return task_cfg

    def remove_task(self, project_name: str, task_name: str) -> TaskConfig:
        """Remove a task from a project by its unique name.

        Args:
            project_name: Target project.
            task_name: Task to remove.

        Returns:
            The removed TaskConfig.

        Raises:
            KeyError: If the project or task does not exist.
        """
        project = self._projects_engine.get_project(project_name)
        idx = self._find_task_index(project.tasks, task_name)
        if idx < 0:
            logger.error("Task '%s' not found in project '%s'", task_name, project_name)
            raise KeyError(f"Task '{task_name}' does not exist.")

        raw = project.tasks.pop(idx)
        cfg = TaskConfig(
            task_name=str(raw.get("task_name") or raw.get("name")),
            task_type=str(raw.get("task_type") or raw.get("type")),
            task_title=str(raw.get("task_title") or raw.get("title")),
            active=bool(raw.get("active", True)),
            config=dict(raw.get("config", {})),
            iterations=int(raw.get("iterations", 0)),
        )
        logger.info("Removed task '%s' from project '%s'", task_name, project_name)
        return cfg

    def move_task(self, project_name: str, task_name: str, to_index: int) -> None:
        """Move a task to a different position in the task list.

        Args:
            project_name: Target project.
            task_name: Task to reposition.
            to_index: Target zero-based index.

        Raises:
            KeyError: If project or task does not exist.
        """
        project = self._projects_engine.get_project(project_name)
        idx = self._find_task_index(project.tasks, task_name)
        if idx < 0:
            raise KeyError(f"Task '{task_name}' does not exist.")

        task = project.tasks.pop(idx)
        bounded_index = max(0, min(to_index, len(project.tasks)))
        project.tasks.insert(bounded_index, task)
        logger.info(
            "Moved task '%s' from index %d to %d in project '%s'",
            task_name,
            idx,
            bounded_index,
            project_name,
        )

    def rename_task(self, project_name: str, task_name: str, task_title: str) -> None:
        """Update the human-readable title of a task.

        Args:
            project_name: Target project.
            task_name: Task identifier.
            task_title: New display title.

        Raises:
            KeyError: If project or task does not exist.
        """
        project = self._projects_engine.get_project(project_name)
        idx = self._find_task_index(project.tasks, task_name)
        if idx < 0:
            raise KeyError(f"Task '{task_name}' does not exist.")

        project.tasks[idx]["title"] = task_title
        project.tasks[idx]["taskTitle"] = task_title
        logger.info(
            "Renamed task '%s' title to '%s' in project '%s'",
            task_name,
            task_title,
            project_name,
        )

    def activate_task(self, project_name: str, task_name: str, active: bool) -> None:
        """Set task active status.

        Args:
            project_name: Target project.
            task_name: Task identifier.
            active: Desired boolean activation status.

        Raises:
            KeyError: If project or task does not exist.
        """
        project = self._projects_engine.get_project(project_name)
        idx = self._find_task_index(project.tasks, task_name)
        if idx < 0:
            raise KeyError(f"Task '{task_name}' does not exist.")

        project.tasks[idx]["active"] = active
        logger.info(
            "Set task '%s' active=%s in project '%s'",
            task_name,
            active,
            project_name,
        )

    def _generate_unique_task_name(
        self, tasks: list[dict[str, Any]], task_type: str
    ) -> str:
        """Generate a unique task name like 'Build 1', 'Build 2'."""
        for i in range(1, 1000):
            candidate = f"{task_type} {i}"
            if self._find_task_index(tasks, candidate) < 0:
                return candidate
        return f"{task_type}_clone"

    def clone_task(
        self, project_name: str, task_name: str, *, position: str = "end"
    ) -> TaskConfig:
        """Clone an existing task within a project.

        Args:
            project_name: Target project.
            task_name: Task to duplicate.
            position: 'end' or 'after' the source task.

        Returns:
            The newly cloned TaskConfig.

        Raises:
            KeyError: If project or task does not exist.
        """
        project = self._projects_engine.get_project(project_name)
        idx = self._find_task_index(project.tasks, task_name)
        if idx < 0:
            raise KeyError(f"Task '{task_name}' does not exist.")

        source = project.tasks[idx]
        task_type = str(source.get("task_type") or source.get("type"))
        new_name = self._generate_unique_task_name(project.tasks, task_type)
        old_title = str(source.get("task_title") or source.get("title") or task_name)
        new_title = f"{old_title} - Cloned"

        cloned_config = copy.deepcopy(source.get("config", {}))
        cloned_task = TaskConfig(
            task_name=new_name,
            task_type=task_type,
            task_title=new_title,
            active=bool(source.get("active", True)),
            config=cloned_config,
            iterations=0,
        )

        cloned_dict = cloned_task.to_dict()
        if position == "after":
            project.tasks.insert(idx + 1, cloned_dict)
        else:
            project.tasks.append(cloned_dict)

        logger.info(
            "Cloned task '%s' to '%s' in project '%s' (position=%s)",
            task_name,
            new_name,
            project_name,
            position,
        )
        return cloned_task
