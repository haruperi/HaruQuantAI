"""Load from files task execution coordinator.

Description:
    Coordinates loading strategies from local files on disk into a target databank,
    supporting glob patterns, clear-before-load, and import statistics reporting.

Purpose:
    FEAT-TASK-EXECUTION: Support strategy file ingestion into databanks.

Key Capabilities:
    - FR-task-load-from-files: Scan filesystem directory for strategy files and
      load them into databanks with error boundary protection.

Python API Usage:
    ```python
    from app.workspace.task_manager.tasks.load_from_files import (
        FileLoadStore,
        LoadFilesProgress,
        LoadFromFilesResult,
        LoadFromFilesTask,
    )

    result = LoadFromFilesTask.run(
        directory_path="data/strategies",
        file_pattern="*.sqx",
        target_databank="Results",
        clear_before_load=False,
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
    "FileLoadStore",
    "LoadFilesProgress",
    "LoadFromFilesResult",
    "LoadFromFilesTask",
]


class LoadFilesProgress(Protocol):
    """Protocol for reporting file loading progress."""

    def log(self, message: str) -> None:
        """Log progress message."""
        ...

    def set_progress(self, percent: float) -> None:
        """Set progress percentage."""
        ...


class FileLoadStore(Protocol):
    """Protocol for databank operations supporting strategy file loading."""

    def load_files_into_databank(
        self,
        directory: str,
        pattern: str,
        databank: str,
        clear_before_load: bool,
    ) -> int:
        """Load matching files into databank and return count of loaded items."""
        ...


@dataclass(frozen=True, slots=True)
class LoadFromFilesResult:
    """Outcome of LoadFromFilesTask execution."""

    success: bool
    loaded_count: int
    message: str


class LoadFromFilesTask:
    """Coordinator for strategy file loading execution."""

    @staticmethod
    def run(
        directory_path: str,
        file_pattern: str,
        target_databank: str,
        clear_before_load: bool,
        *,
        task_log_prefix: str = "",
        store: FileLoadStore | None = None,
        progress: LoadFilesProgress | None = None,
    ) -> LoadFromFilesResult:
        """Execute strategy loading from filesystem files."""
        start_msg = (
            f"{task_log_prefix}Loading files '{file_pattern}' from '{directory_path}' "
            f"into databank '{target_databank}'"
        )
        logger.info(start_msg)
        if progress:
            progress.log(start_msg)
            progress.set_progress(10.0)

        if not directory_path or not target_databank:
            msg = f"{task_log_prefix}Error: Directory path or databank empty"
            logger.error(msg)
            if progress:
                progress.log(msg)
            return LoadFromFilesResult(success=False, loaded_count=0, message=msg)

        count = 0
        if store is not None:
            try:
                count = store.load_files_into_databank(
                    directory_path,
                    file_pattern,
                    target_databank,
                    clear_before_load,
                )
            except Exception as e:
                err_msg = f"{task_log_prefix}Failed loading files: {e}"
                logger.exception(err_msg)
                if progress:
                    progress.log(err_msg)
                return LoadFromFilesResult(
                    success=False, loaded_count=0, message=err_msg
                )

        if progress:
            progress.set_progress(100.0)
        done_msg = (
            f"{task_log_prefix}Loaded {count} strategies from '{directory_path}' "
            f"into '{target_databank}'"
        )
        logger.info(done_msg)
        if progress:
            progress.log(done_msg)

        return LoadFromFilesResult(success=True, loaded_count=count, message=done_msg)
