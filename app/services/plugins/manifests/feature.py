"""Feature lifecycle mount implementation for Plugin Manifests."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.plugins.capabilities import DECLARE_MANIFESTS_CAPABILITY
from app.services.plugins.manifests.config import PluginManifestsConfig
from app.services.plugins.manifests.manifest import SPEC
from app.services.plugins.manifests.plugin_manifests import DeclareManifestsService

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class PluginManifestsFeature:
    """Composable feature package providing plugin manifest and package validation."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and config keys.
        """
        self.spec = spec
        self._service: DeclareManifestsService | None = None

    @property
    def service(self) -> DeclareManifestsService | None:
        """Return the initialized manifest service instance.

        Returns:
            The service instance if mounted, else None.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the plugin manifest capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or object.
        """
        raw_config = config if isinstance(config, dict) else {}
        parsed_config = PluginManifestsConfig.from_dict(raw_config)
        self._service = DeclareManifestsService(config=parsed_config)
        context.provide(DECLARE_MANIFESTS_CAPABILITY, self._service)


def feature() -> PluginManifestsFeature:
    """Factory function for discovery via entry points.

    Returns:
        New PluginManifestsFeature instance.
    """
    return PluginManifestsFeature()
