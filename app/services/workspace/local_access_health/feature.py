"""Feature lifecycle mount implementation for Local Access and Health."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.workspace.capabilities import (
    CONFIGURE_RUNTIME_CAPABILITY,
    MANAGE_WORKSPACES_CAPABILITY,
    SECURE_LOCAL_ACCESS_CAPABILITY,
)
from app.services.workspace.local_access_health.config import (
    LocalAccessHealthConfig,
)
from app.services.workspace.local_access_health.local_access_health import (
    LocalAccessHealthService,
)
from app.services.workspace.local_access_health.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class LocalAccessHealthFeature:
    """Composable feature package providing Local Access and Health."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and state.
        """
        self.spec = spec
        self._service: LocalAccessHealthService | None = None

    @property
    def service(self) -> LocalAccessHealthService | None:
        """Return the underlying local access health service instance.

        Returns:
            The service instance if mounted, else None.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the secure local access capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or object.
        """
        _ = config
        manage_workspaces = context.require(MANAGE_WORKSPACES_CAPABILITY)
        configure_runtime = context.optional(CONFIGURE_RUNTIME_CAPABILITY)
        self._service = LocalAccessHealthService(
            config=LocalAccessHealthConfig(),
            manage_workspaces=manage_workspaces,
            configure_runtime=configure_runtime,
        )
        context.provide(SECURE_LOCAL_ACCESS_CAPABILITY, self._service)


def feature() -> LocalAccessHealthFeature:
    """Factory function for discovery via entry points.

    Returns:
        New LocalAccessHealthFeature instance.
    """
    return LocalAccessHealthFeature()
