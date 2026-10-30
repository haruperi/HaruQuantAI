"""Debug Console application service and plugin management.

Description:
    Implements DebugConsoleService, coordinating plugin descriptor metadata,
    diagnostic event recording, and filtering for the Debug Console workspace.

Purpose:
    FEAT-DEBUG-CONSOLE: Provide backend registration and event management
    for the Debug Console application.

Key Capabilities:
    FR-DEBUG-CONSOLE-PLUGIN-REGISTRATION: Export application registration metadata.
    FR-DEBUG-CONSOLE-SERVICE: Coordinate event buffering and category filtering.

Python API Usage:
    from app.workspace.debug_console.app_debug_console import DebugConsoleService

    service = DebugConsoleService()
    descriptor = service.get_plugin_descriptor()
    service.log("Engine", "Calculation complete")
    batch = service.get_events()

CLI Usage:
    uv run python -c "from app.workspace.debug_console import DebugConsoleService"
"""

import logging
from typing import Final

from app.workspace.debug_console.app_debug_console_models import (
    DebugConsolePluginDescriptor,
    DebugEventsBatch,
    DebugFilterModel,
    DebugLogEntryModel,
)
from app.workspace.debug_console.events import DebugEventPublisher

logger: Final[logging.Logger] = logging.getLogger(__name__)


class DebugConsoleService:
    """Application service for Debug Console plugin and event management."""

    def __init__(self, publisher: DebugEventPublisher | None = None) -> None:
        """Initialize DebugConsoleService with descriptor and publisher.

        Args:
            publisher: Optional custom DebugEventPublisher instance.
        """
        self._descriptor = DebugConsolePluginDescriptor()
        self._publisher = publisher if publisher is not None else DebugEventPublisher()
        logger.info(
            "Initialized DebugConsoleService for app_code=%s "
            "[FR-DEBUG-CONSOLE-PLUGIN-REGISTRATION]",
            self._descriptor.app_code,
        )

    def get_plugin_descriptor(self) -> DebugConsolePluginDescriptor:
        """Retrieve plugin registration descriptor metadata.

        Returns:
            DebugConsolePluginDescriptor instance.
        """
        logger.info(
            "Retrieved plugin descriptor for %s [FR-DEBUG-CONSOLE-PLUGIN-REGISTRATION]",
            self._descriptor.app_code,
        )
        return self._descriptor

    def log(
        self,
        category: str,
        message: str,
        time_str: str | None = None,
    ) -> DebugLogEntryModel:
        """Record a diagnostic event into the event publisher.

        Args:
            category: Log category.
            message: Log message text.
            time_str: Optional timestamp string.

        Returns:
            The recorded DebugLogEntryModel.
        """
        entry = self._publisher.emit(
            category=category, message=message, time_str=time_str
        )
        logger.info(
            "DebugConsoleService logged event category=%s [FR-DEBUG-CONSOLE-SERVICE]",
            category,
        )
        return entry

    def get_events(self, limit: int | None = None) -> DebugEventsBatch:
        """Retrieve recorded events batch.

        Args:
            limit: Optional maximum number of recent events.

        Returns:
            DebugEventsBatch containing matching events and total count.
        """
        entries = self._publisher.get_entries(limit=limit)
        logger.info(
            "DebugConsoleService retrieved %d events [FR-DEBUG-CONSOLE-SERVICE]",
            len(entries),
        )
        return DebugEventsBatch(events=entries, total_count=len(entries))

    def filter_events(self, filter_spec: DebugFilterModel) -> DebugEventsBatch:
        """Filter events using category and case-sensitive text criteria.

        Args:
            filter_spec: DebugFilterModel criteria.

        Returns:
            DebugEventsBatch containing filtered events.
        """
        filtered = self._publisher.filter_entries(filter_spec)
        logger.info(
            "DebugConsoleService filtered %d events for category=%s "
            "[FR-DEBUG-CONSOLE-SERVICE]",
            len(filtered),
            filter_spec.category,
        )
        return DebugEventsBatch(events=filtered, total_count=len(filtered))

    def clear(self) -> None:
        """Clear all buffered events."""
        self._publisher.clear()
        logger.info("DebugConsoleService cleared events [FR-DEBUG-CONSOLE-SERVICE]")
