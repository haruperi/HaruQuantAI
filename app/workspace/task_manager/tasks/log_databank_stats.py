"""Log databank stats task execution coordinator.

Description:
    Coordinates querying and logging quantitative summary metrics for strategies
    residing in a named databank.

Purpose:
    FEAT-TASK-EXECUTION: Support databank summary and statistics logging.

Key Capabilities:
    - FR-task-log-databank-stats: Compute and log strategy metrics for databanks
      with configurable log levels and structured dictionary returns.

Python API Usage:
    ```python
    from app.workspace.task_manager.tasks.log_databank_stats import (
        DatabankStatsReporter,
        LogDatabankStatsResult,
        LogDatabankStatsTask,
    )

    result = LogDatabankStatsTask.run(
        databank="Results",
        metrics=["count", "netProfit", "sharpeRatio"],
        log_level="INFO",
        task_log_prefix="[Task 1] ",
        reporter=mock_reporter,
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
    "DatabankStatsReporter",
    "LogDatabankStatsResult",
    "LogDatabankStatsTask",
]


class DatabankStatsReporter(Protocol):
    """Protocol for calculating stats metrics on databanks."""

    def compute_stats(self, databank: str, metrics: Sequence[str]) -> dict[str, Any]:
        """Compute requested metrics and return summary mapping."""
        ...


@dataclass(frozen=True, slots=True)
class LogDatabankStatsResult:
    """Outcome of LogDatabankStatsTask execution."""

    success: bool
    stats: dict[str, Any]
    message: str


class LogDatabankStatsTask:
    """Coordinator for logging databank statistics."""

    @staticmethod
    def run(
        databank: str,
        metrics: Sequence[str],
        log_level: str = "INFO",
        *,
        task_log_prefix: str = "",
        reporter: DatabankStatsReporter | None = None,
    ) -> LogDatabankStatsResult:
        """Execute databank stats logging."""
        start_msg = f"{task_log_prefix}Computing statistics for databank '{databank}'"
        logger.info(start_msg)

        if not databank:
            msg = f"{task_log_prefix}Error: Databank name is empty"
            logger.error(msg)
            return LogDatabankStatsResult(success=False, stats={}, message=msg)

        computed: dict[str, Any] = {}
        if reporter is not None:
            try:
                computed = reporter.compute_stats(databank, metrics)
            except Exception as e:
                err_msg = (
                    f"{task_log_prefix}Failed computing stats for '{databank}': {e}"
                )
                logger.exception(err_msg)
                return LogDatabankStatsResult(success=False, stats={}, message=err_msg)

        formatted_stats = ", ".join(f"{k}={v}" for k, v in computed.items())
        summary_str = formatted_stats or "no records"
        done_msg = f"{task_log_prefix}Stats for '{databank}': {summary_str}"
        if log_level.upper() == "DEBUG":
            logger.debug(done_msg)
        else:
            logger.info(done_msg)

        return LogDatabankStatsResult(success=True, stats=computed, message=done_msg)
