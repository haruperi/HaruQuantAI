"""Go to task execution coordinator.

Description:
    Coordinates evaluation of loop and branch conditions for the "Go to task"
    workflow, calculating target task jump indices or advancing sequentially.

Purpose:
    FEAT-TASK-EXECUTION: Support project pipeline looping and branching control flow.

Key Capabilities:
    - FR-task-go-to-task: Evaluate conditions, record evaluated and activated cycles,
      and resolve the next task graph index.

Python API Usage:
    ```python
    from app.workspace.task_manager.tasks.go_to_task import (
        GoToTaskCoordinator,
        GoToTaskResult,
    )

    result = GoToTaskCoordinator.evaluate_jump(
        task_name="LoopBack",
        target_task_name="Step1",
        conditions_met=True,
        current_index=3,
        tasks_list=[{"name": "Step1"}, {"name": "Step2"}, {"name": "LoopBack"}],
        task_log_prefix="[Task 3] ",
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
from typing import Any

from app.core.host.logging import get_logger

logger = get_logger(__name__)

__all__ = ["GoToTaskCoordinator", "GoToTaskResult"]


@dataclass(frozen=True, slots=True)
class GoToTaskResult:
    """Outcome of Go to task evaluation."""

    jump_occurred: bool
    next_index: int
    target_task_name: str
    message: str


class GoToTaskCoordinator:
    """Coordinator for Go to task conditional branching."""

    @staticmethod
    def evaluate_jump(
        task_name: str,
        target_task_name: str,
        conditions_met: bool,
        current_index: int,
        tasks_list: Sequence[dict[str, Any]],
        *,
        task_log_prefix: str = "",
    ) -> GoToTaskResult:
        """Resolve next index based on condition evaluation and target task."""
        if not conditions_met or not target_task_name:
            next_idx = current_index + 1
            msg = (
                f"{task_log_prefix}GoTo conditions not met or no target task; "
                f"advancing to index {next_idx}"
            )
            logger.info(msg)
            return GoToTaskResult(
                jump_occurred=False,
                next_index=next_idx,
                target_task_name=target_task_name,
                message=msg,
            )

        for idx, t in enumerate(tasks_list):
            name = t.get("task_name") or t.get("name")
            if name == target_task_name:
                jump_msg = (
                    f"{task_log_prefix}GoToTask '{task_name}' jumping "
                    f"to '{target_task_name}' (index {idx})"
                )
                logger.info(jump_msg)
                return GoToTaskResult(
                    jump_occurred=True,
                    next_index=idx,
                    target_task_name=target_task_name,
                    message=jump_msg,
                )

        fallback_idx = current_index + 1
        warn_msg = (
            f"{task_log_prefix}GoTo target '{target_task_name}' not found; "
            f"advancing to index {fallback_idx}"
        )
        logger.warning(warn_msg)
        return GoToTaskResult(
            jump_occurred=False,
            next_index=fallback_idx,
            target_task_name=target_task_name,
            message=warn_msg,
        )
