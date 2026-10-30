"""Delete file task coordinator.

Description:
    Coordinates file deletion operations with injected file operations and progress
    ports. Preserves exact ordered execution, basename message formatting, and
    catch-and-finish error policies.

Purpose:
    FEAT-TASK-EXECUTION: Provide isolated file deletion task coordination.

Key Capabilities:
    - FR-task-delete-file: Execute file deletion with status logging and
      exception isolation.

Python API Usage:
    ```python
    from app.workspace.task_manager.tasks.delete_file import DeleteFileTask

    result = DeleteFileTask.run(
        "/path/to/strategy.sqx",
        task_log_prefix="[Task 1] ",
        files=my_file_adapter,
        progress=my_progress_adapter,
    )
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/task_manager/tasks/test_delete_file.py -q
    ```
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.core.host.logging import get_logger

logger = get_logger("haruquant.task_manager.delete_file")

__all__ = [
    "DeleteFileTask",
    "DeleteProgress",
    "FileOperations",
    "TaskLogResult",
]


@dataclass(frozen=True, slots=True)
class TaskLogResult:
    """Outcome message result of a file deletion task."""

    message: str


class FileOperations(Protocol):
    """Protocol for abstract file system operations."""

    def exists(self, path: str) -> bool:
        """Check whether path exists."""
        ...

    def delete(self, path: str) -> bool:
        """Delete file at path."""
        ...

    def basename(self, path: str) -> str:
        """Return file basename."""
        ...


class DeleteProgress(Protocol):
    """Protocol for task execution progress and logging."""

    def set_log_prefix(self, prefix: str) -> None:
        """Set task log prefix."""
        ...

    def log(self, message: str) -> None:
        """Log message."""
        ...

    def start(self) -> None:
        """Signal start of execution."""
        ...

    def finish(self) -> None:
        """Signal completion of execution."""
        ...


def _perform_deletion(files: FileOperations, file_path: str) -> str:
    """Validate existence and delete target file, returning success log."""
    base = files.basename(file_path)
    if not files.exists(file_path):
        raise RuntimeError(f"File '{base}' not found.")

    deleted = files.delete(file_path)
    if not deleted:
        raise RuntimeError(f"File '{base}' cannot be deleted.")

    return f"File '{base}' deleted."


class DeleteFileTask:
    """Task coordinator for deleting files."""

    @staticmethod
    def run(
        file_path: str,
        *,
        task_log_prefix: str,
        files: FileOperations,
        progress: DeleteProgress,
    ) -> TaskLogResult:
        """Run file deletion workflow.

        Args:
            file_path: Target path to delete.
            task_log_prefix: Prefix to apply to progress logger.
            files: Injected FileOperations adapter.
            progress: Injected DeleteProgress adapter.

        Returns:
            TaskLogResult containing the selected outcome message.
        """
        progress.set_log_prefix(task_log_prefix)
        progress.log("Deleting file...")
        progress.start()

        selected_message = ""
        try:
            selected_message = _perform_deletion(files, file_path)
            progress.log(selected_message)
        except Exception as err:
            logger.exception("Error while loading strategies. Exc.")
            selected_message = str(err)
            progress.log(selected_message)

        progress.finish()
        return TaskLogResult(message=selected_message)
