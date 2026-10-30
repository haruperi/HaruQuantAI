"""Wait for task execution coordinator.

Description:
    Coordinates pausing pipeline execution or waiting for external file arrival
    based on task WaitFor configuration.

Purpose:
    FEAT-TASK-EXECUTION: Support interactive user pause and filesystem watch gates.

Key Capabilities:
    - FR-task-wait-for: Evaluate user-wait or file-wait triggers and return
      pipeline pause decisions with status logging.

Python API Usage:
    ```python
    from app.workspace.task_manager.tasks.wait_for import (
        FilePresenceChecker,
        WaitForResult,
        WaitForTaskCoordinator,
    )

    result = WaitForTaskCoordinator.run(
        action="user",
        file_path="",
        task_log_prefix="[Task 1] ",
        checker=mock_checker,
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
    "FilePresenceChecker",
    "WaitForResult",
    "WaitForTaskCoordinator",
]


class FilePresenceChecker(Protocol):
    """Protocol for checking presence of a target file."""

    def exists(self, path: str) -> bool:
        """Check if target file exists."""
        ...


@dataclass(frozen=True, slots=True)
class WaitForResult:
    """Outcome of WaitForTask execution."""

    should_pause: bool
    condition_satisfied: bool
    message: str


class WaitForTaskCoordinator:
    """Coordinator for WaitFor task execution."""

    @staticmethod
    def run(
        action: str,
        file_path: str,
        *,
        task_log_prefix: str = "",
        checker: FilePresenceChecker | None = None,
    ) -> WaitForResult:
        """Evaluate WaitFor behavior."""
        if action == "user":
            msg = f"{task_log_prefix}Pausing execution for user confirmation"
            logger.info(msg)
            return WaitForResult(
                should_pause=True,
                condition_satisfied=False,
                message=msg,
            )

        if action == "file":
            start_msg = f"{task_log_prefix}Checking presence of file '{file_path}'"
            logger.info(start_msg)
            found = False
            if checker is not None and file_path:
                try:
                    found = checker.exists(file_path)
                except Exception as e:
                    err_msg = f"{task_log_prefix}Error checking file '{file_path}': {e}"
                    logger.exception(err_msg)
                    return WaitForResult(
                        should_pause=True,
                        condition_satisfied=False,
                        message=err_msg,
                    )

            if found:
                done_msg = f"{task_log_prefix}File '{file_path}' exists; continuing"
                logger.info(done_msg)
                return WaitForResult(
                    should_pause=False,
                    condition_satisfied=True,
                    message=done_msg,
                )

            pause_msg = f"{task_log_prefix}File '{file_path}' not found; waiting"
            logger.info(pause_msg)
            return WaitForResult(
                should_pause=True,
                condition_satisfied=False,
                message=pause_msg,
            )

        # Default fallback: unknown action does not pause
        fallback_msg = f"{task_log_prefix}Unknown wait action '{action}'; continuing"
        logger.warning(fallback_msg)
        return WaitForResult(
            should_pause=False,
            condition_satisfied=True,
            message=fallback_msg,
        )
