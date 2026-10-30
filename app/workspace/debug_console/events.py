"""Debug Console diagnostic event collector and ring buffer.

Description:
    Manages in-memory circular collection of diagnostic log events
    with bounded capacity matching donor DebugConsole.java (1000 entries).

Purpose:
    FEAT-DEBUG-CONSOLE: Collect and buffer diagnostic events from core
    subsystems for the Debug Console workspace.

Key Capabilities:
    FR-DEBUG-CONSOLE-EVENTS: Diagnostic event recording and bounded buffer.

Python API Usage:
    from app.workspace.debug_console.events import DebugEventPublisher

    publisher = DebugEventPublisher()
    publisher.emit(category="Engine", message="Task dispatched")
    events = publisher.get_entries()

CLI Usage:
    uv run python -c "from app.workspace.debug_console import DebugEventPublisher"
"""

import logging
from collections import deque
from datetime import UTC, datetime
from typing import Final

from app.workspace.debug_console.app_debug_console_models import (
    DebugFilterModel,
    DebugLogEntryModel,
)

logger: Final[logging.Logger] = logging.getLogger(__name__)
MAX_LOG_ENTRIES: Final[int] = 1000


class DebugEventPublisher:
    """In-memory circular event buffer for diagnostic log messages."""

    def __init__(self, max_entries: int = MAX_LOG_ENTRIES) -> None:
        """Initialize the event publisher with bounded ring buffer.

        Args:
            max_entries: Maximum entries retained before FIFO eviction.
        """
        self._max_entries = max_entries
        self._buffer: deque[DebugLogEntryModel] = deque(maxlen=max_entries)
        logger.info(
            "Initialized DebugEventPublisher max_capacity=%d [FR-DEBUG-CONSOLE-EVENTS]",
            max_entries,
        )

    def emit(
        self,
        category: str,
        message: str,
        time_str: str | None = None,
    ) -> DebugLogEntryModel:
        """Record a diagnostic event into the bounded ring buffer.

        Args:
            category: Log category tag (e.g. 'Engine', 'Jobs', 'System').
            message: Message payload.
            time_str: Optional explicit time string (defaults to UTC HH:MM:SS).

        Returns:
            The created DebugLogEntryModel.
        """
        if time_str is None:
            time_str = datetime.now(UTC).strftime("%H:%M:%S")

        entry = DebugLogEntryModel(time=time_str, category=category, message=message)
        self._buffer.append(entry)
        logger.info(
            "Emitted debug event category=%s message_len=%d [FR-DEBUG-CONSOLE-EVENTS]",
            category,
            len(message),
        )
        return entry

    def get_entries(self, limit: int | None = None) -> list[DebugLogEntryModel]:
        """Retrieve recorded events from the buffer.

        Args:
            limit: Optional maximum number of recent entries to return.

        Returns:
            List of recorded DebugLogEntryModel objects in chronological order.
        """
        entries = list(self._buffer)
        if limit is not None and limit < len(entries):
            entries = entries[-limit:]
        return entries

    def filter_entries(self, filter_spec: DebugFilterModel) -> list[DebugLogEntryModel]:
        """Filter buffer entries by category and case-sensitive substring.

        Args:
            filter_spec: DebugFilterModel containing category and text filter.

        Returns:
            Filtered list of DebugLogEntryModel objects.
        """
        result: list[DebugLogEntryModel] = []
        for entry in self._buffer:
            if filter_spec.category not in ("all", entry.category):
                continue
            if filter_spec.text and filter_spec.text not in entry.message:
                continue
            result.append(entry)
        return result

    def clear(self) -> None:
        """Clear all entries from the ring buffer."""
        self._buffer.clear()
        logger.info("Cleared debug event buffer [FR-DEBUG-CONSOLE-EVENTS]")

    def size(self) -> int:
        """Return the current number of buffered entries."""
        return len(self._buffer)
