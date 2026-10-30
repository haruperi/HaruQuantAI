"""Stop and start task execution coordinator.

Description:
    Coordinates lifecycle actions (stop, start, restart) on target projects
    or current pipeline tasks subject to condition evaluation.

Purpose:
    FEAT-TASK-EXECUTION: Support project lifecycle automation and scheduled restart.

Key Capabilities:
    - FR-task-stop-and-start: Execute lifecycle operations on target projects
      when conditions are met with structured outcome logging.

Python API Usage:
    ```python
    from app.workspace.task_manager.tasks.stop_and_start import (
        ProjectLifecycleController,
        StopAndStartResult,
        StopAndStartTaskCoordinator,
    )

    result = StopAndStartTaskCoordinator.run(
        action="restart",
        target_project="WorkerProject",
        conditions_met=True,
        task_log_prefix="[Task 1] ",
        controller=mock_controller,
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
    "ProjectLifecycleController",
    "StopAndStartResult",
    "StopAndStartTaskCoordinator",
]


class ProjectLifecycleController(Protocol):
    """Protocol for controlling project execution lifecycle."""

    def perform_action(self, project_name: str, action: str) -> bool:
        """Perform start, stop, or restart on target project."""
        ...


@dataclass(frozen=True, slots=True)
class StopAndStartResult:
    """Outcome of StopAndStartTask execution."""

    action_executed: bool
    action: str
    target_project: str
    message: str


class StopAndStartTaskCoordinator:
    """Coordinator for Stop & Start task execution."""

    @staticmethod
    def run(
        action: str,
        target_project: str,
        conditions_met: bool,
        *,
        task_log_prefix: str = "",
        controller: ProjectLifecycleController | None = None,
    ) -> StopAndStartResult:
        """Execute project lifecycle action if conditions are met."""
        if not conditions_met:
            msg = f"{task_log_prefix}Conditions not met for action '{action}'; skipping"
            logger.info(msg)
            return StopAndStartResult(
                action_executed=False,
                action=action,
                target_project=target_project,
                message=msg,
            )

        start_msg = (
            f"{task_log_prefix}Executing action '{action}' on target '{target_project}'"
        )
        logger.info(start_msg)

        executed = True
        if controller is not None and target_project:
            try:
                executed = controller.perform_action(target_project, action)
            except Exception as e:
                err_msg = (
                    f"{task_log_prefix}Failed executing '{action}' on "
                    f"'{target_project}': {e}"
                )
                logger.exception(err_msg)
                return StopAndStartResult(
                    action_executed=False,
                    action=action,
                    target_project=target_project,
                    message=err_msg,
                )

        done_msg = f"{task_log_prefix}Action '{action}' executed for '{target_project}'"
        logger.info(done_msg)

        return StopAndStartResult(
            action_executed=executed,
            action=action,
            target_project=target_project,
            message=done_msg,
        )
