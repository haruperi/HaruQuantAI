"""Debug Console workspace data models.

Description:
    Defines Pydantic models for the DebugConsole application plugin descriptor,
    log entry representation, filter settings, and event batch responses.

Purpose:
    FEAT-DEBUG-CONSOLE: Provide strongly typed schemas for Debug Console plugin
    registration and log event transport.

Key Capabilities:
    FR-DEBUG-CONSOLE-PLUGIN-MODELS: Strongly typed plugin descriptor attributes.
    FR-DEBUG-CONSOLE-EVENT-MODELS: Log entry model and filter schema.

Python API Usage:
    from app.workspace.debug_console.app_debug_console_models import (
        DebugConsolePluginDescriptor,
        DebugFilterModel,
        DebugLogEntryModel,
    )

CLI Usage:
    uv run python -c "from app.workspace.debug_console import DebugConsoleService"
"""

from pydantic import BaseModel, Field


class DebugLogEntryModel(BaseModel):
    """Data representation of a single debug log entry."""

    time: str = Field(..., description="Timestamp string (e.g. HH:MM:SS)")
    category: str = Field(..., description="Logging category tag")
    message: str = Field(..., description="Raw log message text")


class DebugFilterModel(BaseModel):
    """Filter parameters for category and case-sensitive substring matching."""

    category: str = Field(
        default="all", description="Target category or 'all' for unrestricted"
    )
    text: str = Field(
        default="", description="Case-sensitive substring to match in message"
    )


class DebugConsolePluginDescriptor(BaseModel):
    """Plugin registration descriptor for DebugConsole."""

    name: str = Field(default="DebugConsole", description="Plugin display name")
    app_code: str = Field(
        default="DEBUGCONSOLE", description="Application code identifier"
    )
    category: str = Field(default="App", description="Plugin category")
    product: str = Field(default="SQUANT", description="Target product")
    preferred_position: int = Field(
        default=1, description="Navigation menu order position"
    )
    context_path: str = Field(
        default="/debugconsole", description="Context root URL path"
    )
    tooltip: str = Field(
        default="DebugConsole", description="Hover tooltip description"
    )
    hidden: bool = Field(
        default=False, description="Whether hidden from primary navigation"
    )
    only_in_pro: bool = Field(
        default=True, description="Restricted to professional edition"
    )


class DebugEventsBatch(BaseModel):
    """Response containing a batch of collected debug log entries."""

    events: list[DebugLogEntryModel] = Field(
        default_factory=list, description="Collected debug log entries"
    )
    total_count: int = Field(..., description="Total entry count in this batch")
