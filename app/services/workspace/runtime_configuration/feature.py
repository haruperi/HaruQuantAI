"""Feature lifecycle mount implementation for Runtime Configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.workspace.capabilities import CONFIGURE_RUNTIME_CAPABILITY
from app.services.workspace.runtime_configuration.config import (
    RuntimeConfigurationConfig,
)
from app.services.workspace.runtime_configuration.manifest import SPEC
from app.services.workspace.runtime_configuration.runtime_configuration import (
    RuntimeConfigurationService,
)

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class RuntimeConfigurationFeature:
    """Composable feature package providing Runtime Configuration."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and state.
        """
        self.spec = spec
        self._service = RuntimeConfigurationService(
            RuntimeConfigurationConfig(),
        )

    @property
    def service(self) -> RuntimeConfigurationService:
        """Return the underlying runtime configuration service.

        Returns:
            The runtime configuration service instance.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the runtime configuration capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or object.
        """
        _ = config
        context.provide(CONFIGURE_RUNTIME_CAPABILITY, self._service)


def feature() -> RuntimeConfigurationFeature:
    """Factory function for discovery via entry points.

    Returns:
        New RuntimeConfigurationFeature instance.
    """
    return RuntimeConfigurationFeature()
