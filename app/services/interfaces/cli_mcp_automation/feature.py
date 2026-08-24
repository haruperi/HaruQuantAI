"""Feature lifecycle mount implementation for Unified CLI and MCP Automation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.contracts.interfaces.capabilities import AUTOMATE_COMMANDS_CAPABILITY
from app.services.interfaces.cli_mcp_automation.cli_mcp_automation import (
    CliMcpAutomationService,
)
from app.services.interfaces.cli_mcp_automation.config import (
    CliMcpAutomationConfig,
)
from app.services.interfaces.cli_mcp_automation.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class CliMcpAutomationFeature:
    """Composable feature package providing Unified CLI and MCP Automation."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and state.
        """
        self.spec = spec
        self._service: CliMcpAutomationService | None = None

    @property
    def service(self) -> CliMcpAutomationService | None:
        """Return the underlying automation service instance if mounted.

        Returns:
            The automation service instance.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the automate-commands capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or object.
        """
        raw_config: dict[str, Any] = config if isinstance(config, dict) else {}
        parsed_config = CliMcpAutomationConfig.from_dict(raw_config)
        self._service = CliMcpAutomationService(parsed_config)
        context.provide(AUTOMATE_COMMANDS_CAPABILITY, self._service)


def feature() -> CliMcpAutomationFeature:
    """Factory function for discovery via entry points.

    Returns:
        New CliMcpAutomationFeature instance.
    """
    return CliMcpAutomationFeature()
