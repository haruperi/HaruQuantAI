"""Update data task execution coordinator.

Description:
    Coordinates downloading and updating historical market price data for
    configured symbols and timeframes using injected data feed providers.

Purpose:
    FEAT-TASK-EXECUTION: Support automated market data acquisition and updates.

Key Capabilities:
    - FR-task-update-data: Fetch and update historical data for symbols with
      provider injection, error boundary handling, and bar count reporting.

Python API Usage:
    ```python
    from app.workspace.task_manager.tasks.update_data import (
        DataFeedProvider,
        UpdateDataProgress,
        UpdateDataResult,
        UpdateDataTask,
    )

    result = UpdateDataTask.run(
        symbol="EURUSD",
        timeframe="H1",
        data_provider="Dukascopy",
        clean_history=False,
        task_log_prefix="[Task 1] ",
        provider=mock_provider,
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
    "DataFeedProvider",
    "UpdateDataProgress",
    "UpdateDataResult",
    "UpdateDataTask",
]


class UpdateDataProgress(Protocol):
    """Protocol for reporting data update progress."""

    def log(self, message: str) -> None:
        """Log progress message."""
        ...

    def set_progress(self, percent: float) -> None:
        """Set progress percentage."""
        ...


class DataFeedProvider(Protocol):
    """Protocol for downloading market data updates."""

    def update_market_data(
        self,
        symbol: str,
        timeframe: str,
        provider: str,
        clean_history: bool,
    ) -> int:
        """Fetch updated bars and return new bars count."""
        ...


@dataclass(frozen=True, slots=True)
class UpdateDataResult:
    """Outcome of UpdateDataTask execution."""

    success: bool
    bars_updated: int
    message: str


class UpdateDataTask:
    """Coordinator for Market Data Update task execution."""

    @staticmethod
    def run(
        symbol: str,
        timeframe: str,
        data_provider: str,
        clean_history: bool,
        *,
        task_log_prefix: str = "",
        provider: DataFeedProvider | None = None,
        progress: UpdateDataProgress | None = None,
    ) -> UpdateDataResult:
        """Execute market data update."""
        start_msg = (
            f"{task_log_prefix}Updating data for '{symbol}' ({timeframe}) "
            f"via provider '{data_provider}'"
        )
        logger.info(start_msg)
        if progress:
            progress.log(start_msg)
            progress.set_progress(10.0)

        if not symbol:
            msg = f"{task_log_prefix}Error: Instrument symbol cannot be empty"
            logger.error(msg)
            if progress:
                progress.log(msg)
            return UpdateDataResult(success=False, bars_updated=0, message=msg)

        bars = 0
        if provider is not None:
            try:
                bars = provider.update_market_data(
                    symbol, timeframe, data_provider, clean_history
                )
            except Exception as e:
                err_msg = f"{task_log_prefix}Failed updating market data: {e}"
                logger.exception(err_msg)
                if progress:
                    progress.log(err_msg)
                return UpdateDataResult(success=False, bars_updated=0, message=err_msg)

        if progress:
            progress.set_progress(100.0)
        done_msg = f"{task_log_prefix}Updated {bars} bars for '{symbol}' ({timeframe})"
        logger.info(done_msg)
        if progress:
            progress.log(done_msg)

        return UpdateDataResult(success=True, bars_updated=bars, message=done_msg)
