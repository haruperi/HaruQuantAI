"""Clear databanks task coordinator.

Description:
    Coordinates databank clearing operations for selected or all databanks using
    injected project and progress ports. Preserves exact logging, reason strings,
    and MemoryError handling semantics.

Purpose:
    FEAT-TASK-EXECUTION: Provide isolated databank clearing coordination.

Key Capabilities:
    - FR-task-clear-databanks: Execute databank clearing across all or selected banks
      with continuation on missing banks and explicit memory error handling.

Python API Usage:
    ```python
    from app.workspace.task_manager.tasks.clear_databanks import ClearDatabanksTask

    ClearDatabanksTask.run(
        ["Results"],
        project_name="MyProject",
        task_title="ClearTask",
        task_log_prefix="[Task 1] ",
        project=my_project_adapter,
        progress=my_progress_adapter,
    )
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/task_manager/tasks/ -q
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from app.core.host.logging import get_logger

logger = get_logger(__name__)

__all__ = [
    "ClearBank",
    "ClearDatabanksTask",
    "ClearProgress",
    "ClearProject",
]


class ClearBank(Protocol):
    """Protocol for a clearable databank."""

    name: str

    def clear_records(self, reset_view: bool, notify: bool, reason: str) -> None:
        """Clear records from this databank."""
        ...


class ClearProject(Protocol):
    """Protocol for project databank operations."""

    def list_banks(self) -> Sequence[ClearBank]:
        """List all available databanks in this project."""
        ...

    def get_bank(self, name: str) -> ClearBank | None:
        """Retrieve a databank by name, or None if absent."""
        ...

    def on_memory_error(self, error: MemoryError) -> None:
        """Handle out-of-memory error during bank clearing."""
        ...


class ClearProgress(Protocol):
    """Protocol for progress and operational logging."""

    def set_log_prefix(self, prefix: str) -> None:
        """Set task log prefix."""
        ...

    def log(self, message: str) -> None:
        """Log a message."""
        ...

    def start(self) -> None:
        """Signal task execution start."""
        ...

    def finish(self) -> None:
        """Signal task execution completion."""
        ...


class ClearDatabanksTask:
    """Task coordinator for clearing project databanks."""

    @staticmethod
    def run(
        names: Sequence[str],
        *,
        project_name: str,
        task_title: str,
        task_log_prefix: str,
        project: ClearProject,
        progress: ClearProgress,
    ) -> None:
        """Run databank clearing workflow.

        Args:
            names: Sequence of bank names to clear, or including 'all' for all banks.
            project_name: Containing project name.
            task_title: Task title descriptor.
            task_log_prefix: String prefix to set on the progress reporter.
            project: Project port adapter.
            progress: Progress reporter port adapter.
        """
        progress.set_log_prefix(task_log_prefix)
        progress.log("Clearing databanks...")
        progress.start()

        try:
            if "all" in names:
                all_banks = project.list_banks()
                for bank in all_banks:
                    reason = (
                        f"'Clear databanks task' {project_name}/{task_title}, "
                        f"clear all databanks - databank "
                        f"{project_name}/{bank.name}"
                    )
                    bank.clear_records(True, True, reason)
                progress.log("Cleared all databanks")
            else:
                for name in names:
                    selected_bank = project.get_bank(name)
                    if selected_bank is None:
                        progress.log(f"Error: Databank {name} not found")
                        continue
                    reason = (
                        f"'Clear databanks task' {project_name}/{task_title}, "
                        f"clear selected databanks - databank "
                        f"{project_name}/{selected_bank.name}"
                    )
                    selected_bank.clear_records(True, True, reason)
                    progress.log(f"Cleared databank '{name}'")
        except MemoryError as err:
            logger.exception("FR-task-clear-databanks: memory error clearing databanks")
            project.on_memory_error(err)

        progress.finish()
