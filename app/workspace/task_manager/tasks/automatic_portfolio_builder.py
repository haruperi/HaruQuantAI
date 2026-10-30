"""Automatic portfolio builder task execution coordinator.

Description:
    Coordinates portfolio construction from a source databank into a destination
    portfolio databank, applying correlation constraints and ranking criteria.

Purpose:
    FEAT-TASK-EXECUTION: Support automated portfolio assembly workflows.

Key Capabilities:
    - FR-task-auto-portfolio-builder: Construct optimized portfolios from strategies
      with correlation filtering and structured result logging.

Python API Usage:
    ```python
    from app.workspace.task_manager.tasks.automatic_portfolio_builder import (
        AutoPortfolioResult,
        AutomaticPortfolioBuilderTask,
        PortfolioBuilderStore,
        PortfolioProgress,
    )

    result = AutomaticPortfolioBuilderTask.run(
        source_databank="Results",
        target_databank="Portfolio",
        portfolio_size=5,
        correlation_threshold=0.7,
        ranking_method="SharpeRatio",
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
    "AutoPortfolioResult",
    "AutomaticPortfolioBuilderTask",
    "PortfolioBuilderStore",
    "PortfolioProgress",
]


class PortfolioProgress(Protocol):
    """Protocol for portfolio builder progress reporting."""

    def log(self, message: str) -> None:
        """Log progress message."""
        ...

    def set_progress(self, percent: float) -> None:
        """Set progress percentage."""
        ...


class PortfolioBuilderStore(Protocol):
    """Protocol for databank operations supporting portfolio creation."""

    def build_portfolio(
        self,
        source_databank: str,
        target_databank: str,
        size: int,
        correlation_threshold: float,
        ranking_method: str,
    ) -> int:
        """Build portfolio and return count of selected strategies."""
        ...


@dataclass(frozen=True, slots=True)
class AutoPortfolioResult:
    """Outcome of AutomaticPortfolioBuilderTask execution."""

    success: bool
    strategies_included: int
    message: str


class AutomaticPortfolioBuilderTask:
    """Coordinator for Automatic Portfolio Builder execution."""

    @staticmethod
    def run(
        source_databank: str,
        target_databank: str,
        portfolio_size: int,
        correlation_threshold: float,
        ranking_method: str,
        *,
        task_log_prefix: str = "",
        store: PortfolioBuilderStore | None = None,
        progress: PortfolioProgress | None = None,
    ) -> AutoPortfolioResult:
        """Execute portfolio generation."""
        start_msg = (
            f"{task_log_prefix}Building portfolio of size {portfolio_size} "
            f"from '{source_databank}' to '{target_databank}'"
        )
        logger.info(start_msg)
        if progress:
            progress.log(start_msg)
            progress.set_progress(10.0)

        if not source_databank or not target_databank:
            msg = f"{task_log_prefix}Error: Databank name cannot be empty"
            logger.error(msg)
            if progress:
                progress.log(msg)
            return AutoPortfolioResult(
                success=False, strategies_included=0, message=msg
            )

        count = 0
        if store is not None:
            try:
                count = store.build_portfolio(
                    source_databank,
                    target_databank,
                    portfolio_size,
                    correlation_threshold,
                    ranking_method,
                )
            except Exception as e:
                err_msg = f"{task_log_prefix}Failed building portfolio: {e}"
                logger.exception(err_msg)
                if progress:
                    progress.log(err_msg)
                return AutoPortfolioResult(
                    success=False, strategies_included=0, message=err_msg
                )

        if progress:
            progress.set_progress(100.0)
        done_msg = (
            f"{task_log_prefix}Built portfolio with {count} strategies "
            f"in '{target_databank}'"
        )
        logger.info(done_msg)
        if progress:
            progress.log(done_msg)

        return AutoPortfolioResult(
            success=True, strategies_included=count, message=done_msg
        )
