"""Structured Data Manager activity history and active progress tracking."""

from __future__ import annotations

import math
import time
import uuid
from collections import deque
from datetime import UTC, datetime
from threading import RLock
from typing import Any

from app.host.events import EventBus
from app.host.response import (
    ErrorCode,
    ResponseMetadata,
    StandardError,
    StandardResponse,
)
from app.host.transport import get_global_event_bus

from ._helpers import (
    _COMPLETE,
    _LEVELS,
    _MAX_PAGE,
    _MAX_TASK_ID,
)

__all__ = ["Logs"]


class Logs:
    """Thread-safe activity service with injectable host event delivery."""

    def __init__(
        self, event_bus: EventBus | None = None, *, max_characters: int = 10000
    ) -> None:
        """Create an empty history, bounded by retained message characters."""
        if (
            isinstance(max_characters, bool)
            or not isinstance(max_characters, int)
            or max_characters < 1
        ):
            raise ValueError("max_characters must be a positive integer")
        self._bus = event_bus if event_bus is not None else get_global_event_bus()
        self._capacity = max_characters
        self._entries: deque[dict[str, Any]] = deque()
        self._characters = 0
        self._active: dict[str, dict[str, Any]] = {}
        self._lock = RLock()

    @staticmethod
    def _result(
        operation: str, started: float, data: Any = None, *, error: str = ""
    ) -> dict[str, Any]:
        metadata = ResponseMetadata(
            operation=f"logs.{operation}",
            duration_ms=(time.perf_counter() - started) * 1000,
        )
        if error:
            return StandardResponse.failure(
                message=error,
                metadata=metadata,
                error=StandardError(code=ErrorCode.VALIDATION, message=error),
            )
        return StandardResponse.success(
            message="Data Manager log operation completed", metadata=metadata, data=data
        )

    def list(
        self, *, task_id: str | None = None, limit: int = 100, offset: int = 0
    ) -> dict[str, Any]:
        """Return a detached newest-first page, optionally for a single task."""
        started = time.perf_counter()
        if (
            isinstance(limit, bool)
            or not isinstance(limit, int)
            or not 1 <= limit <= _MAX_PAGE
            or isinstance(offset, bool)
            or not isinstance(offset, int)
            or offset < 0
            or (task_id is not None and not self._valid_task(task_id))
        ):
            return self._result("list", started, error="Invalid task or pagination")
        with self._lock:
            entries = [
                dict(entry)
                for entry in self._entries
                if task_id is None or entry["task_id"] == task_id
            ]
        return self._result(
            "list",
            started,
            {
                "entries": entries[offset : offset + limit],
                "total": len(entries),
                "limit": limit,
                "offset": offset,
            },
        )

    def clear(self) -> dict[str, Any]:
        """Clear retained history while preserving active task progress."""
        started = time.perf_counter()
        with self._lock:
            count = len(self._entries)
            self._entries.clear()
            self._characters = 0
            self._bus.publish(
                "logs",
                "datamanager.logs.cleared",
                {"workspace": "data-manager", "cleared_count": count},
            )
        return self._result("clear", started, {"cleared_count": count})

    def list_active(self) -> dict[str, Any]:
        """Return a detached snapshot of tasks that have not finished."""
        started = time.perf_counter()
        with self._lock:
            tasks = [dict(task) for task in self._active.values()]
        return self._result("list_active", started, tasks)

    @staticmethod
    def _valid_task(task_id: object) -> bool:
        return (
            isinstance(task_id, str)
            and bool(task_id.strip())
            and len(task_id) <= _MAX_TASK_ID
        )

    def record_progress(
        self, task_id: str, *, progress: float, message: str = "", level: str = "info"
    ) -> dict[str, Any]:
        """Record activity; 100 or negative progress removes the active task.

        Empty messages update progress without creating a history entry. Oversized
        messages retain their beginning, and oldest whole entries are evicted.
        Messages are plain text; consumers must escape them when rendering HTML.
        """
        started = time.perf_counter()
        if (
            not self._valid_task(task_id)
            or isinstance(progress, bool)
            or not isinstance(progress, (int, float))
            or not math.isfinite(progress)
            or progress > _COMPLETE
            or not isinstance(message, str)
            or not isinstance(level, str)
            or level not in _LEVELS
        ):
            return self._result(
                "record_progress", started, error="Invalid progress update"
            )
        update: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "task_id": task_id,
            "message": message[: self._capacity],
            "level": level,
            "progress": float(progress),
        }
        with self._lock:
            if progress == _COMPLETE or progress < 0:
                self._active.pop(task_id, None)
            else:
                self._active[task_id] = dict(update)
            entry = {"id": uuid.uuid4().hex, **update} if message else None
            if entry is not None:
                self._entries.appendleft(entry)
                self._characters += len(entry["message"])
                while self._characters > self._capacity:
                    self._characters -= len(self._entries.pop()["message"])
            self._bus.publish(
                "logs",
                "datamanager.logs.progress",
                {
                    "workspace": "data-manager",
                    "update": dict(update),
                    "entry": dict(entry) if entry else None,
                },
            )
        return self._result(
            "record_progress", started, {"entry": entry, "update": update}
        )
