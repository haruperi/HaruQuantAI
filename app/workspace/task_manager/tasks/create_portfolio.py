"""Create portfolio task execution coordinator.

Description:
    Coordinates portfolio creation by combining selected or top N strategies
    from a source databank into a named portfolio strategy in the destination bank.

Purpose:
    FEAT-TASK-EXECUTION: Support strategy portfolio creation workflows.

Key Capabilities:
    - FR-task-create-portfolio: Group strategies into a composite portfolio
      with selection modes and structured execution reporting.

Python API Usage:
    ```python
    from app.workspace.task_manager.tasks.create_portfolio import (
        CreatePortfolioResult,
        CreatePortfolioTask,
        PortfolioCreationStore,
        PortfolioProgress,
    )

    result = CreatePortfolioTask.run(
        source_databank="Results",
        portfolio_name="MainPortfolio",
        selection_mode="top_n",
        top_n=5,
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
    "CreatePortfolioResult",
    "CreatePortfolioTask",
    "PortfolioCreationStore",
    "PortfolioProgress",
]


class PortfolioProgress(Protocol):
    """Protocol for reporting portfolio creation progress."""

    def log(self, message: str) -> None:
        """Log progress message."""
        ...

    def set_progress(self, percent: float) -> None:
        """Set progress percentage."""
        ...


class PortfolioCreationStore(Protocol):
    """Protocol for databank operations supporting portfolio assembly."""

    def create_portfolio_strategy(
        self,
        source_databank: str,
        portfolio_name: str,
        selection_mode: str,
        top_n: int,
    ) -> int:
        """Combine strategies into a portfolio and return component count."""
        ...


@dataclass(frozen=True, slots=True)
class CreatePortfolioResult:
    """Outcome of CreatePortfolioTask execution."""

    success: bool
    components_count: int
    message: str


class CreatePortfolioTask:
    """Coordinator for Create Portfolio task execution."""

    @staticmethod
    def run(
        source_databank: str,
        portfolio_name: str,
        selection_mode: str,
        top_n: int,
        *,
        task_log_prefix: str = "",
        store: PortfolioCreationStore | None = None,
        progress: PortfolioProgress | None = None,
    ) -> CreatePortfolioResult:
        """Execute portfolio creation."""
        start_msg = (
            f"{task_log_prefix}Creating portfolio '{portfolio_name}' "
            f"from '{source_databank}' using mode '{selection_mode}'"
        )
        logger.info(start_msg)
        if progress:
            progress.log(start_msg)
            progress.set_progress(10.0)

        if not source_databank or not portfolio_name:
            msg = f"{task_log_prefix}Error: Source databank or portfolio name empty"
            logger.error(msg)
            if progress:
                progress.log(msg)
            return CreatePortfolioResult(success=False, components_count=0, message=msg)

        count = 0
        if store is not None:
            try:
                count = store.create_portfolio_strategy(
                    source_databank, portfolio_name, selection_mode, top_n
                )
            except Exception as e:
                err_msg = f"{task_log_prefix}Failed creating portfolio: {e}"
                logger.exception(err_msg)
                if progress:
                    progress.log(err_msg)
                return CreatePortfolioResult(
                    success=False, components_count=0, message=err_msg
                )

        if progress:
            progress.set_progress(100.0)
        done_msg = (
            f"{task_log_prefix}Created portfolio '{portfolio_name}' with "
            f"{count} strategies"
        )
        logger.info(done_msg)
        if progress:
            progress.log(done_msg)

        return CreatePortfolioResult(
            success=True, components_count=count, message=done_msg
        )
