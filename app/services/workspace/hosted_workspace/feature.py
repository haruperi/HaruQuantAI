"""Feature lifecycle mount implementation for Hosted Workspace Boundary."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.workspace.capabilities import (
    HOST_WORKSPACES_CAPABILITY,
)
from app.services.workspace.hosted_workspace.config import (
    HostedWorkspaceConfig,
)
from app.services.workspace.hosted_workspace.hosted_workspace import (
    HostedWorkspaceService,
)
from app.services.workspace.hosted_workspace.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class HostedWorkspaceFeature:
    """Composable feature package providing Hosted Workspace Boundary capabilities."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and state.
        """
        self.spec = spec
        self._service: HostedWorkspaceService | None = None

    @property
    def service(self) -> HostedWorkspaceService | None:
        """Return the underlying service instance if mounted.

        Returns:
            HostedWorkspaceService instance or None.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the host workspaces capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or object.
        """
        _ = config
        self._service = HostedWorkspaceService(
            config=HostedWorkspaceConfig(),
        )
        context.provide(HOST_WORKSPACES_CAPABILITY, self._service)


def feature() -> HostedWorkspaceFeature:
    """Factory function for discovery via entry points.

    Returns:
        New HostedWorkspaceFeature instance.
    """
    return HostedWorkspaceFeature()
