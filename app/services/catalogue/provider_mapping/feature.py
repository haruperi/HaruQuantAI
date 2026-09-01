"""Feature lifecycle mount implementation for Provider and Broker Mapping."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.catalogue.capabilities import MAP_PROVIDERS_CAPABILITY
from app.services.catalogue.provider_mapping.config import ProviderMappingConfig
from app.services.catalogue.provider_mapping.manifest import SPEC
from app.services.catalogue.provider_mapping.provider_mapping import (
    ProviderMappingService,
)

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class ProviderMappingFeature:
    """Composable feature package providing Provider and Broker Mapping capabilities."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and state.
        """
        self.spec = spec
        self._service: ProviderMappingService | None = None

    @property
    def service(self) -> ProviderMappingService | None:
        """Return the underlying provider mapping service instance.

        Returns:
            The provider mapping service instance, or None if unmounted.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the provider mapping capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or object.

        Raises:
            TypeError: If config database_path is not a valid string or path.
        """
        cfg = ProviderMappingConfig()
        if isinstance(config, dict):
            db_path = config.get("database_path")
            if db_path is not None and not isinstance(db_path, str):
                msg = "database_path must be a string if provided"
                raise TypeError(msg)
            cfg = ProviderMappingConfig(
                database_path=db_path,
                auto_migrate=config.get("auto_migrate", True),
            )
        elif isinstance(config, ProviderMappingConfig):
            cfg = config

        self._service = ProviderMappingService(
            config=cfg,
            event_bus=getattr(context, "events", None)
            or getattr(context, "event_bus", None),
        )
        context.provide(MAP_PROVIDERS_CAPABILITY, self._service)


def feature() -> ProviderMappingFeature:
    """Factory function for discovery via entry points.

    Returns:
        New ProviderMappingFeature instance.
    """
    return ProviderMappingFeature()
