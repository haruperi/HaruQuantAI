"""Apply mass config task execution coordinator.

Description:
    Coordinates applying mass configuration changes across strategies in a target
    databank. Supports configuration parameter injection, progress reporting,
    and structured outcome logging.

Purpose:
    FEAT-TASK-EXECUTION: Support automated batch strategy configuration updates.

Key Capabilities:
    - FR-task-apply-mass-config: Apply configuration to strategies in a databank
      with progress logging and exception isolation.

Python API Usage:
    ```python
    from app.workspace.task_manager.tasks.apply_mass_config import (
        ApplyMassConfigTask,
        MassConfigProgress,
        MassConfigStore,
    )

    result = ApplyMassConfigTask.run(
        target_databank="Results",
        config_type="default",
        parameters={"risk": 0.01},
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
from typing import Any, Protocol

from app.core.host.logging import get_logger

logger = get_logger(__name__)

__all__ = [
    "ApplyMassConfigResult",
    "ApplyMassConfigTask",
    "MassConfigProgress",
    "MassConfigStore",
]


class MassConfigProgress(Protocol):
    """Protocol for reporting task progress and logs."""

    def log(self, message: str) -> None:
        """Log a message."""
        ...

    def set_progress(self, percent: float) -> None:
        """Report progress percentage."""
        ...


class MassConfigStore(Protocol):
    """Protocol for databank operations supporting mass configuration."""

    def apply_config(
        self, databank: str, config_type: str, parameters: dict[str, Any]
    ) -> int:
        """Apply mass configuration to databank and return modified strategy count."""
        ...


@dataclass(frozen=True, slots=True)
class ApplyMassConfigResult:
    """Outcome of ApplyMassConfigTask execution."""

    success: bool
    modified_count: int
    message: str


class ApplyMassConfigTask:
    """Coordinator for applying mass config to databank strategies."""

    @staticmethod
    def run(
        target_databank: str,
        config_type: str,
        parameters: dict[str, Any],
        *,
        task_log_prefix: str = "",
        store: MassConfigStore | None = None,
        progress: MassConfigProgress | None = None,
    ) -> ApplyMassConfigResult:
        """Execute mass configuration application."""
        start_msg = (
            f"{task_log_prefix}Applying mass config '{config_type}' "
            f"to databank '{target_databank}'"
        )
        logger.info(start_msg)
        if progress:
            progress.log(start_msg)
            progress.set_progress(10.0)

        if not target_databank:
            msg = f"{task_log_prefix}Error: Target databank is empty"
            logger.error(msg)
            if progress:
                progress.log(msg)
            return ApplyMassConfigResult(success=False, modified_count=0, message=msg)

        modified = 0
        if store is not None:
            try:
                modified = store.apply_config(target_databank, config_type, parameters)
            except Exception as e:
                err_msg = f"{task_log_prefix}Failed applying mass config: {e}"
                logger.exception(err_msg)
                if progress:
                    progress.log(err_msg)
                return ApplyMassConfigResult(
                    success=False, modified_count=0, message=err_msg
                )

        if progress:
            progress.set_progress(100.0)
        done_msg = (
            f"{task_log_prefix}Applied mass config '{config_type}' to "
            f"{modified} strategies in '{target_databank}'"
        )
        logger.info(done_msg)
        if progress:
            progress.log(done_msg)

        return ApplyMassConfigResult(
            success=True, modified_count=modified, message=done_msg
        )
