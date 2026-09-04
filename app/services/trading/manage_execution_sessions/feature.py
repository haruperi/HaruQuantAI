"""Feature lifecycle mount for the trading execution sessions manager."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.trading.capabilities import MANAGE_EXECUTION_SESSIONS_CAPABILITY
from app.services.trading.manage_execution_sessions.config import (
    ManageExecutionSessionsConfig,
    from_dict,
)
from app.services.trading.manage_execution_sessions.execution_sessions import (
    ExecutionSessionsService,
)
from app.services.trading.manage_execution_sessions.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class ManageExecutionSessionsFeature:
    """Composable feature package providing trading execution session operations."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature with its specification.

        Args:
            spec: Feature specification declaring the served capability.
        """
        self.spec = spec
        self._service: ExecutionSessionsService | None = None

    @property
    def service(self) -> ExecutionSessionsService | None:
        """Return the mounted service, or None before mount.

        Returns:
            Active execution sessions service if mounted, otherwise None.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the execution sessions service and provide its capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Mapping, ManageExecutionSessionsConfig, or None.

        Raises:
            ValueError: If configuration contains unknown keys.
            TypeError: If configuration has an unsupported type.
        """
        if config is None or isinstance(config, dict):
            parsed = from_dict(config)
        elif isinstance(config, ManageExecutionSessionsConfig):
            parsed = config
        else:
            message = (
                "manage-execution-sessions configuration must be a mapping or config"
            )
            raise TypeError(message)
        service = ExecutionSessionsService(parsed)
        context.register_callback(service.close)
        context.provide(MANAGE_EXECUTION_SESSIONS_CAPABILITY, service)
        self._service = service


def feature() -> ManageExecutionSessionsFeature:
    """Factory for discovery via entry points.

    Returns:
        New ManageExecutionSessionsFeature instance.
    """
    return ManageExecutionSessionsFeature()
