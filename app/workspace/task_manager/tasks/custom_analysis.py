"""Custom analysis task execution coordinator.

Description:
    Coordinates custom quantitative analysis routines against strategies in a
    target databank using injected analysis execution runners.

Purpose:
    FEAT-TASK-EXECUTION: Support user-defined and custom analysis script runs.

Key Capabilities:
    - FR-task-custom-analysis: Run custom analytics routines across databank
      records with progress updates and structured exception handling.

Python API Usage:
    ```python
    from app.workspace.task_manager.tasks.custom_analysis import (
        AnalysisProgress,
        AnalysisRunner,
        CustomAnalysisResult,
        CustomAnalysisTask,
    )

    result = CustomAnalysisTask.run(
        snippet_name="drawdown_audit",
        target_databank="Results",
        parameters={"threshold": 0.15},
        task_log_prefix="[Task 1] ",
        runner=mock_runner,
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
from typing import Any, Protocol

from app.core.host.logging import get_logger

logger = get_logger(__name__)

__all__ = [
    "AnalysisProgress",
    "AnalysisRunner",
    "CustomAnalysisResult",
    "CustomAnalysisTask",
]


class AnalysisProgress(Protocol):
    """Protocol for reporting custom analysis progress."""

    def log(self, message: str) -> None:
        """Log progress message."""
        ...

    def set_progress(self, percent: float) -> None:
        """Set progress percentage."""
        ...


class AnalysisRunner(Protocol):
    """Protocol for executing custom analysis logic."""

    def run_analysis(
        self, snippet_name: str, databank: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """Run custom analysis routine and return outcome metrics."""
        ...


@dataclass(frozen=True, slots=True)
class CustomAnalysisResult:
    """Outcome of CustomAnalysisTask execution."""

    success: bool
    output_metrics: dict[str, Any]
    message: str


class CustomAnalysisTask:
    """Coordinator for Custom Analysis task execution."""

    @staticmethod
    def run(
        snippet_name: str,
        target_databank: str,
        parameters: dict[str, Any],
        *,
        task_log_prefix: str = "",
        runner: AnalysisRunner | None = None,
        progress: AnalysisProgress | None = None,
    ) -> CustomAnalysisResult:
        """Execute custom analysis routine."""
        start_msg = (
            f"{task_log_prefix}Starting custom analysis '{snippet_name}' "
            f"on databank '{target_databank}'"
        )
        logger.info(start_msg)
        if progress:
            progress.log(start_msg)
            progress.set_progress(10.0)

        if not snippet_name:
            msg = f"{task_log_prefix}Error: Snippet name cannot be empty"
            logger.error(msg)
            if progress:
                progress.log(msg)
            return CustomAnalysisResult(success=False, output_metrics={}, message=msg)

        metrics: dict[str, Any] = {}
        if runner is not None:
            try:
                metrics = runner.run_analysis(snippet_name, target_databank, parameters)
            except Exception as e:
                err_msg = f"{task_log_prefix}Custom analysis failed: {e}"
                logger.exception(err_msg)
                if progress:
                    progress.log(err_msg)
                return CustomAnalysisResult(
                    success=False, output_metrics={}, message=err_msg
                )

        if progress:
            progress.set_progress(100.0)
        done_msg = f"{task_log_prefix}Completed custom analysis '{snippet_name}'"
        logger.info(done_msg)
        if progress:
            progress.log(done_msg)

        return CustomAnalysisResult(
            success=True, output_metrics=metrics, message=done_msg
        )
