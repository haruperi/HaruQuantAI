"""Filtering task execution coordinator.

Description:
    Coordinates strategy filtering from a source databank into a destination databank
    based on customizable quantitative condition sets.

Purpose:
    FEAT-TASK-EXECUTION: Support automated strategy filtering and ranking workflows.

Key Capabilities:
    - FR-task-filtering: Filter strategies matching condition sets from one databank
      into another with detailed statistics logging.

Python API Usage:
    ```python
    from app.workspace.task_manager.tasks.filtering import (
        FilteringProgress,
        FilteringResult,
        FilteringStore,
        FilteringTask,
    )

    result = FilteringTask.run(
        source_databank="Results",
        target_databank="Passed",
        filter_conditions=[{"metric": "SharpeRatio", "comparator": ">", "value": 1.0}],
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

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from app.core.host.logging import get_logger

logger = get_logger(__name__)

__all__ = [
    "FilteringProgress",
    "FilteringResult",
    "FilteringStore",
    "FilteringTask",
]


class FilteringProgress(Protocol):
    """Protocol for reporting strategy filtering progress."""

    def log(self, message: str) -> None:
        """Log progress message."""
        ...

    def set_progress(self, percent: float) -> None:
        """Set progress percentage."""
        ...


class FilteringStore(Protocol):
    """Protocol for databank operations supporting strategy filtering."""

    def filter_strategies(
        self,
        source_databank: str,
        target_databank: str,
        conditions: Sequence[dict[str, Any]],
    ) -> tuple[int, int]:
        """Apply filters and return (total_evaluated, total_passed)."""
        ...


@dataclass(frozen=True, slots=True)
class FilteringResult:
    """Outcome of FilteringTask execution."""

    success: bool
    evaluated_count: int
    passed_count: int
    message: str


class FilteringTask:
    """Coordinator for strategy filtering execution."""

    @staticmethod
    def run(
        source_databank: str,
        target_databank: str,
        filter_conditions: Sequence[dict[str, Any]],
        *,
        task_log_prefix: str = "",
        store: FilteringStore | None = None,
        progress: FilteringProgress | None = None,
    ) -> FilteringResult:
        """Execute filtering across databank strategies."""
        start_msg = (
            f"{task_log_prefix}Filtering strategies from '{source_databank}' "
            f"to '{target_databank}' ({len(filter_conditions)} conditions)"
        )
        logger.info(start_msg)
        if progress:
            progress.log(start_msg)
            progress.set_progress(10.0)

        if not source_databank or not target_databank:
            msg = f"{task_log_prefix}Error: Databank names cannot be empty"
            logger.error(msg)
            if progress:
                progress.log(msg)
            return FilteringResult(
                success=False, evaluated_count=0, passed_count=0, message=msg
            )

        evaluated = 0
        passed = 0
        if store is not None:
            try:
                evaluated, passed = store.filter_strategies(
                    source_databank, target_databank, filter_conditions
                )
            except Exception as e:
                err_msg = f"{task_log_prefix}Filtering failed: {e}"
                logger.exception(err_msg)
                if progress:
                    progress.log(err_msg)
                return FilteringResult(
                    success=False,
                    evaluated_count=0,
                    passed_count=0,
                    message=err_msg,
                )

        if progress:
            progress.set_progress(100.0)
        done_msg = (
            f"{task_log_prefix}Filtered {evaluated} strategies: "
            f"{passed} passed to '{target_databank}'"
        )
        logger.info(done_msg)
        if progress:
            progress.log(done_msg)

        return FilteringResult(
            success=True,
            evaluated_count=evaluated,
            passed_count=passed,
            message=done_msg,
        )
