"""Configuration model for Unified CLI and MCP Automation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_ALLOWED_CONFIG_KEYS = frozenset(
    {
        "title",
        "command_timeout_seconds",
        "max_durable_jobs",
        "enable_mcp",
    }
)


@dataclass(frozen=True, slots=True)
class CliMcpAutomationConfig:
    """Configuration for Unified CLI and MCP Automation feature.

    Attributes:
        title: Interface automation title string.
        command_timeout_seconds: Default timeout for synchronous commands.
        max_durable_jobs: Maximum number of retained durable jobs in memory.
        enable_mcp: Flag indicating if MCP endpoints/tools are enabled.
    """

    title: str = "HaruQuantAI Automation Gateway"
    command_timeout_seconds: float = 30.0
    max_durable_jobs: int = 1000
    enable_mcp: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> CliMcpAutomationConfig:
        """Parse and strictly validate configuration data.

        Args:
            data: Raw configuration dictionary.

        Returns:
            Validated CliMcpAutomationConfig instance.

        Raises:
            ValueError: If unknown keys are present or values are out of bounds.
        """
        if not data:
            return cls()

        unknown = set(data) - _ALLOWED_CONFIG_KEYS
        if unknown:
            msg = "Unknown CliMcpAutomation configuration keys: " + ", ".join(
                sorted(unknown)
            )
            raise ValueError(msg)

        title = str(data.get("title", "HaruQuantAI Automation Gateway"))
        command_timeout_seconds = float(data.get("command_timeout_seconds", 30.0))
        max_durable_jobs = int(data.get("max_durable_jobs", 1000))
        enable_mcp = bool(data.get("enable_mcp", True))

        if command_timeout_seconds <= 0:
            raise ValueError("command_timeout_seconds must be positive")
        if max_durable_jobs <= 0:
            raise ValueError("max_durable_jobs must be positive")

        return cls(
            title=title,
            command_timeout_seconds=command_timeout_seconds,
            max_durable_jobs=max_durable_jobs,
            enable_mcp=enable_mcp,
        )
