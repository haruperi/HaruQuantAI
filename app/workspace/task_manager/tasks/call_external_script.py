"""Call external script task execution coordinator.

Description:
    Coordinates process execution of an external script or executable with
    injected executor, argument passing, timeout enforcement, and log prefixing.

Purpose:
    FEAT-TASK-EXECUTION: Support external CLI script automation from task pipelines.

Key Capabilities:
    - FR-task-call-external-script: Execute external scripts safely with timeout
      isolation, error policies, and structured exit reporting.

Python API Usage:
    ```python
    from app.workspace.task_manager.tasks.call_external_script import (
        CallScriptResult,
        CallExternalScriptTask,
        ScriptExecutor,
        ScriptProgress,
    )

    result = CallExternalScriptTask.run(
        script_path="scripts/process.py",
        arguments=["--all"],
        working_directory="",
        timeout_seconds=60,
        fail_on_error=True,
        task_log_prefix="[Task 1] ",
        executor=mock_executor,
        progress=mock_progress,
    )
    ```

CLI Usage:
    ```bash
    uv run python -m pytest tests/workspace/task_manager/tasks/ -q
    ```
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from app.core.host.logging import get_logger

logger = get_logger(__name__)

__all__ = [
    "CallExternalScriptTask",
    "CallScriptResult",
    "ScriptExecutor",
    "ScriptProgress",
]


class ScriptProgress(Protocol):
    """Protocol for external script progress reporting."""

    def log(self, message: str) -> None:
        """Log progress message."""
        ...

    def set_progress(self, percent: float) -> None:
        """Set progress percentage."""
        ...


class ScriptExecutor(Protocol):
    """Protocol for executing external system commands."""

    def execute(
        self,
        script_path: str,
        arguments: Sequence[str],
        working_directory: str,
        timeout: int,
    ) -> tuple[int, str]:
        """Execute script and return (exit_code, output_text)."""
        ...


@dataclass(frozen=True, slots=True)
class CallScriptResult:
    """Outcome of CallExternalScriptTask execution."""

    success: bool
    exit_code: int
    output: str
    message: str


class CallExternalScriptTask:
    """Coordinator for Call External Script execution."""

    @staticmethod
    def run(
        script_path: str,
        arguments: Sequence[str],
        working_directory: str,
        timeout_seconds: int,
        fail_on_error: bool,
        *,
        task_log_prefix: str = "",
        executor: ScriptExecutor | None = None,
        progress: ScriptProgress | None = None,
    ) -> CallScriptResult:
        """Execute external script execution."""
        start_msg = f"{task_log_prefix}Executing external script: '{script_path}'"
        logger.info(start_msg)
        if progress:
            progress.log(start_msg)
            progress.set_progress(10.0)

        if not script_path:
            msg = f"{task_log_prefix}Error: Script path cannot be empty"
            logger.error(msg)
            if progress:
                progress.log(msg)
            return CallScriptResult(success=False, exit_code=-1, output="", message=msg)

        exit_code = 0
        output = ""
        if executor is not None:
            try:
                exit_code, output = executor.execute(
                    script_path, arguments, working_directory, timeout_seconds
                )
            except Exception as e:
                err_msg = f"{task_log_prefix}Script execution failed: {e}"
                logger.exception(err_msg)
                if progress:
                    progress.log(err_msg)
                if fail_on_error:
                    return CallScriptResult(
                        success=False,
                        exit_code=-1,
                        output="",
                        message=err_msg,
                    )
                return CallScriptResult(
                    success=True,
                    exit_code=-1,
                    output=str(e),
                    message=err_msg,
                )

        if progress:
            progress.set_progress(100.0)

        success = exit_code == 0 or not fail_on_error
        done_msg = (
            f"{task_log_prefix}Script '{script_path}' finished "
            f"with exit code {exit_code}"
        )
        logger.info(done_msg)
        if progress:
            progress.log(done_msg)

        return CallScriptResult(
            success=success,
            exit_code=exit_code,
            output=output,
            message=done_msg,
        )
