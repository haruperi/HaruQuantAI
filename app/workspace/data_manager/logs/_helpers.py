"""Helper utilities, constants, and background task context for Data Manager logs."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .feature import Logs

_LEVELS = frozenset({"debug", "info", "warning", "error", "critical"})
_COMPLETE = 100
_MAX_PAGE = 1000
_MAX_TASK_ID = 256


def run_logged_task(
    logs: Logs | None, context: Any, action: Callable[[Any], dict[str, Any]]
) -> dict[str, Any]:
    """Bridge a backend basket job to shared activity history and task progress."""
    if logs is None:
        return action(context)
    activity = logs
    task_id = context.job_id

    class TrackedContext:
        def wait_if_paused(self) -> None:
            context.wait_if_paused()

        def report_progress(self, progress: float, message: str = "") -> None:
            context.report_progress(progress, message)
            activity.record_progress(
                task_id, progress=min(progress, 99), message=f"Updated {message}"
            )

    logs.record_progress(task_id, progress=0, message="Stock group update started")
    try:
        result = action(TrackedContext())
    except Exception as error:
        logs.record_progress(
            task_id,
            progress=-1,
            level="error",
            message=f"Stock group update ended: {type(error).__name__}",
        )
        raise
    logs.record_progress(task_id, progress=100, message="Stock group update completed")
    return result


__all__ = [
    "_COMPLETE",
    "_LEVELS",
    "_MAX_PAGE",
    "_MAX_TASK_ID",
    "run_logged_task",
]
