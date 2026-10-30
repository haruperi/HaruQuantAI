"""Notification task execution coordinator.

Description:
    Coordinates dispatching automated notifications across channels (email,
    webhook, desktop, telegram) upon task milestones or pipeline events.

Purpose:
    FEAT-TASK-EXECUTION: Support pipeline notification and alert dispatches.

Key Capabilities:
    - FR-task-notification: Format templated notification messages and dispatch
      via injected transport protocols with error suppression options.

Python API Usage:
    ```python
    from app.workspace.task_manager.tasks.notification import (
        NotificationSender,
        NotificationTask,
        NotificationTaskResult,
    )

    result = NotificationTask.run(
        channel="email",
        recipient="user@example.com",
        subject="Task Completed",
        message_template="Task {taskName} finished in {projectName}",
        context_vars={"projectName": "Test", "taskName": "Build"},
        task_log_prefix="[Task 1] ",
        sender=mock_sender,
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
    "NotificationSender",
    "NotificationTask",
    "NotificationTaskResult",
]


class NotificationSender(Protocol):
    """Protocol for sending external notifications."""

    def send(self, channel: str, recipient: str, subject: str, message: str) -> bool:
        """Deliver notification and return delivery status boolean."""
        ...


@dataclass(frozen=True, slots=True)
class NotificationTaskResult:
    """Outcome of NotificationTask execution."""

    success: bool
    channel: str
    delivered: bool
    formatted_message: str
    message: str


class NotificationTask:
    """Coordinator for Notification task dispatch."""

    @staticmethod
    def run(
        channel: str,
        recipient: str,
        subject: str,
        message_template: str,
        context_vars: dict[str, Any],
        *,
        task_log_prefix: str = "",
        sender: NotificationSender | None = None,
    ) -> NotificationTaskResult:
        """Format and dispatch notification."""
        try:
            formatted = message_template.format(**context_vars)
        except KeyError, ValueError, IndexError:
            formatted = message_template

        start_msg = (
            f"{task_log_prefix}Sending notification via '{channel}' to '{recipient}'"
        )
        logger.info(start_msg)

        delivered = True
        if sender is not None:
            try:
                delivered = sender.send(channel, recipient, subject, formatted)
            except Exception as e:
                err_msg = f"{task_log_prefix}Notification send failed: {e}"
                logger.exception(err_msg)
                return NotificationTaskResult(
                    success=False,
                    channel=channel,
                    delivered=False,
                    formatted_message=formatted,
                    message=err_msg,
                )

        done_msg = (
            f"{task_log_prefix}Notification delivered via '{channel}' to '{recipient}'"
        )
        logger.info(done_msg)

        return NotificationTaskResult(
            success=True,
            channel=channel,
            delivered=delivered,
            formatted_message=formatted,
            message=done_msg,
        )
