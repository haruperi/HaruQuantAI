"""Feature lifecycle mount for bounded persistence execution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.workspace.capabilities import PERSISTENCE_CAPABILITY
from app.services.workspace.execute_persistence.config import (
    ExecutePersistenceConfig,
    from_dict,
)
from app.services.workspace.execute_persistence.execute_persistence import (
    ExecutePersistenceService,
)
from app.services.workspace.execute_persistence.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class ExecutePersistenceFeature:
    """Composable feature package providing bounded persistence execution."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and state.
        """
        self.spec = spec
        self._service: ExecutePersistenceService | None = None

    @property
    def service(self) -> ExecutePersistenceService | None:
        """Return the mounted service, if available.

        Returns:
            The active service, otherwise None.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the persistence capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or object.

        Raises:
            TypeError: If configuration is not a supported mapping or config object.
        """
        if config is None or isinstance(config, dict):
            parsed = from_dict(config)
        elif isinstance(config, ExecutePersistenceConfig):
            parsed = config
        else:
            raise TypeError(
                "execute-persistence configuration must be a mapping, "
                "ExecutePersistenceConfig, or None"
            )
        service = ExecutePersistenceService(parsed)
        context.register_callback(service.close)
        context.provide(PERSISTENCE_CAPABILITY, service)
        self._service = service


def feature() -> ExecutePersistenceFeature:
    """Factory function for discovery via entry points.

    Returns:
        New ExecutePersistenceFeature instance.
    """
    return ExecutePersistenceFeature()
