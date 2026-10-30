"""Debug Console workspace package.

Description:
    Exposes models, service, and event publisher for Debug Console.

Purpose:
    FEAT-DEBUG-CONSOLE: Export public symbols for Debug Console workspace.

Key Capabilities:
    FR-DEBUG-CONSOLE-PACKAGE: Public exports for workspace consumers.

Python API Usage:
    from app.workspace.debug_console import (
        DebugConsolePluginDescriptor,
        DebugConsoleService,
        DebugEventPublisher,
    )

CLI Usage:
    uv run python -c "import app.workspace.debug_console"
"""

from app.workspace.debug_console.app_debug_console import DebugConsoleService
from app.workspace.debug_console.app_debug_console_models import (
    DebugConsolePluginDescriptor,
    DebugEventsBatch,
    DebugFilterModel,
    DebugLogEntryModel,
)
from app.workspace.debug_console.events import DebugEventPublisher

__all__ = [
    "DebugConsolePluginDescriptor",
    "DebugConsoleService",
    "DebugEventPublisher",
    "DebugEventsBatch",
    "DebugFilterModel",
    "DebugLogEntryModel",
]
