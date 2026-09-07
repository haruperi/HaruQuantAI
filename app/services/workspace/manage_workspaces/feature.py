"""Feature lifecycle mount for workspace management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.workspace.capabilities import MANAGE_WORKSPACES_CAPABILITY
from app.services.workspace.manage_workspaces.config import (
    ManageWorkspacesConfig,
    from_dict,
)
from app.services.workspace.manage_workspaces.manage_workspaces import (
    ManageWorkspacesService,
)
from app.services.workspace.manage_workspaces.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class ManageWorkspacesFeature:
    """Composable feature package providing workspace management."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and state.
        """
        self.spec = spec
        self._service: ManageWorkspacesService | None = None

    @property
    def service(self) -> ManageWorkspacesService | None:
        """Return the mounted service, if available.

        Returns:
            The active service, otherwise None.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the workspace management capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or object.

        Raises:
            TypeError: If configuration is not a supported mapping or config object.
        """
        if config is None or isinstance(config, dict):
            parsed = from_dict(config)
        elif isinstance(config, ManageWorkspacesConfig):
            parsed = config
        else:
            raise TypeError(
                "manage-workspaces configuration must be a mapping, "
                "ManageWorkspacesConfig, or None"
            )
        service = ManageWorkspacesService(parsed)
        context.register_callback(service.close)
        context.provide(MANAGE_WORKSPACES_CAPABILITY, service)
        self._service = service


def feature() -> ManageWorkspacesFeature:
    """Factory function for discovery via entry points.

    Returns:
        New ManageWorkspacesFeature instance.
    """
    return ManageWorkspacesFeature()
