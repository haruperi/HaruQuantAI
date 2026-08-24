"""Feature lifecycle mount implementation for Workspace Lifecycle."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.workspace.capabilities import MANAGE_WORKSPACES_CAPABILITY
from app.services.workspace.workspace_lifecycle.manifest import SPEC
from app.services.workspace.workspace_lifecycle.workspace_lifecycle import (
    WorkspaceLifecycleService,
)

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class WorkspaceLifecycleFeature:
    """Composable feature package providing Workspace Lifecycle capabilities."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and state.
        """
        self.spec = spec
        self._service = WorkspaceLifecycleService()

    @property
    def service(self) -> WorkspaceLifecycleService:
        """Return the underlying workspace lifecycle service.

        Returns:
            The workspace lifecycle service instance.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the workspace management capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or object.
        """
        _ = config
        context.provide(MANAGE_WORKSPACES_CAPABILITY, self._service)


def feature() -> WorkspaceLifecycleFeature:
    """Factory function for discovery via entry points.

    Returns:
        New WorkspaceLifecycleFeature instance.
    """
    return WorkspaceLifecycleFeature()
