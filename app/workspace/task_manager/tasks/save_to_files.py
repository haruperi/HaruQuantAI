"""Save to files task execution coordinator.

Description:
    Coordinates exporting strategies from a databank to disk files in specified
    formats (e.g. sqx, json), with directory creation and export summaries.

Purpose:
    FEAT-TASK-EXECUTION: Support strategy file export from databanks.

Key Capabilities:
    - FR-task-save-to-files: Export databank strategies to filesystem files with
      format options and progress logging.

Python API Usage:
    ```python
    from app.workspace.task_manager.tasks.save_to_files import (
        FileSaveStore,
        SaveFilesProgress,
        SaveToFilesResult,
        SaveToFilesTask,
    )

    result = SaveToFilesTask.run(
        source_databank="Results",
        output_directory="exports/top",
        file_format="json",
        save_all=True,
        task_log_prefix="[Task 1] ",
        store=mock_store,
        progress=mock_progress,
    )
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/task_manager/tasks/ -q
    ```
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.core.host.logging import get_logger

logger = get_logger(__name__)

__all__ = [
    "FileSaveStore",
    "SaveFilesProgress",
    "SaveToFilesResult",
    "SaveToFilesTask",
]


class SaveFilesProgress(Protocol):
    """Protocol for reporting strategy save progress."""

    def log(self, message: str) -> None:
        """Log progress message."""
        ...

    def set_progress(self, percent: float) -> None:
        """Set progress percentage."""
        ...


class FileSaveStore(Protocol):
    """Protocol for databank operations supporting strategy export."""

    def save_databank_to_directory(
        self,
        databank: str,
        output_directory: str,
        file_format: str,
        save_all: bool,
    ) -> int:
        """Export strategies to disk and return count of exported files."""
        ...


@dataclass(frozen=True, slots=True)
class SaveToFilesResult:
    """Outcome of SaveToFilesTask execution."""

    success: bool
    saved_count: int
    message: str


class SaveToFilesTask:
    """Coordinator for strategy file export execution."""

    @staticmethod
    def run(
        source_databank: str,
        output_directory: str,
        file_format: str,
        save_all: bool,
        *,
        task_log_prefix: str = "",
        store: FileSaveStore | None = None,
        progress: SaveFilesProgress | None = None,
    ) -> SaveToFilesResult:
        """Execute strategy export to files."""
        start_msg = (
            f"{task_log_prefix}Saving databank '{source_databank}' "
            f"to '{output_directory}' (format: {file_format})"
        )
        logger.info(start_msg)
        if progress:
            progress.log(start_msg)
            progress.set_progress(10.0)

        if not source_databank or not output_directory:
            msg = f"{task_log_prefix}Error: Databank or output directory empty"
            logger.error(msg)
            if progress:
                progress.log(msg)
            return SaveToFilesResult(success=False, saved_count=0, message=msg)

        saved = 0
        if store is not None:
            try:
                saved = store.save_databank_to_directory(
                    source_databank, output_directory, file_format, save_all
                )
            except Exception as e:
                err_msg = f"{task_log_prefix}Failed saving files: {e}"
                logger.exception(err_msg)
                if progress:
                    progress.log(err_msg)
                return SaveToFilesResult(success=False, saved_count=0, message=err_msg)

        if progress:
            progress.set_progress(100.0)
        done_msg = (
            f"{task_log_prefix}Saved {saved} strategies from '{source_databank}' "
            f"to '{output_directory}'"
        )
        logger.info(done_msg)
        if progress:
            progress.log(done_msg)

        return SaveToFilesResult(success=True, saved_count=saved, message=done_msg)
