"""Automatic retest task execution coordinator.

Description:
    Coordinates automated backtest retesting of strategies in a target databank,
    filtering results and optionally storing surviving strategies.

Purpose:
    FEAT-TASK-EXECUTION: Support automated strategy re-validation workflows.

Key Capabilities:
    - FR-task-auto-retest: Retest strategies in a databank with profile options,
      filtering, and status logging.

Python API Usage:
    ```python
    from app.workspace.task_manager.tasks.automatic_retest import (
        AutoRetestResult,
        AutomaticRetestTask,
        RetestEngine,
        RetestProgress,
    )

    result = AutomaticRetestTask.run(
        databank="Results",
        retest_profile="StressTest",
        filter_results=True,
        save_to_target_databank=False,
        target_databank="",
        task_log_prefix="[Task 1] ",
        engine=mock_engine,
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
    "AutoRetestResult",
    "AutomaticRetestTask",
    "RetestEngine",
    "RetestProgress",
]


class RetestProgress(Protocol):
    """Protocol for retest task progress reporting."""

    def log(self, message: str) -> None:
        """Log progress message."""
        ...

    def set_progress(self, percent: float) -> None:
        """Set progress percentage."""
        ...


class RetestEngine(Protocol):
    """Protocol for executing retests on databank strategies."""

    def retest_strategies(
        self,
        databank: str,
        profile: str,
        filter_results: bool,
        target_databank: str,
    ) -> tuple[int, int]:
        """Retest strategies, returning (retested_count, passed_count)."""
        ...


@dataclass(frozen=True, slots=True)
class AutoRetestResult:
    """Outcome of AutomaticRetestTask execution."""

    success: bool
    retested_count: int
    passed_count: int
    message: str


class AutomaticRetestTask:
    """Coordinator for Automatic Retest execution."""

    @staticmethod
    def run(
        databank: str,
        retest_profile: str,
        filter_results: bool,
        save_to_target_databank: bool,
        target_databank: str,
        *,
        task_log_prefix: str = "",
        engine: RetestEngine | None = None,
        progress: RetestProgress | None = None,
    ) -> AutoRetestResult:
        """Execute automatic retesting of strategies."""
        start_msg = (
            f"{task_log_prefix}Starting automatic retest on databank '{databank}' "
            f"with profile '{retest_profile}'"
        )
        logger.info(start_msg)
        if progress:
            progress.log(start_msg)
            progress.set_progress(10.0)

        if not databank:
            msg = f"{task_log_prefix}Error: Source databank is empty"
            logger.error(msg)
            if progress:
                progress.log(msg)
            return AutoRetestResult(
                success=False, retested_count=0, passed_count=0, message=msg
            )

        destination = target_databank if save_to_target_databank else databank
        retested = 0
        passed = 0
        if engine is not None:
            try:
                retested, passed = engine.retest_strategies(
                    databank, retest_profile, filter_results, destination
                )
            except Exception as e:
                err_msg = f"{task_log_prefix}Failed automatic retest: {e}"
                logger.exception(err_msg)
                if progress:
                    progress.log(err_msg)
                return AutoRetestResult(
                    success=False,
                    retested_count=0,
                    passed_count=0,
                    message=err_msg,
                )

        if progress:
            progress.set_progress(100.0)
        done_msg = (
            f"{task_log_prefix}Completed retest: {retested} retested, "
            f"{passed} passed in '{destination}'"
        )
        logger.info(done_msg)
        if progress:
            progress.log(done_msg)

        return AutoRetestResult(
            success=True,
            retested_count=retested,
            passed_count=passed,
            message=done_msg,
        )
