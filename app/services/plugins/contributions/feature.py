"""Feature lifecycle adapter for Plugin Contributions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.plugins.capabilities import REGISTER_CONTRIBUTIONS_CAPABILITY
from app.services.plugins.contributions.config import PluginContributionsConfig
from app.services.plugins.contributions.manifest import SPEC
from app.services.plugins.contributions.plugin_contributions import (
    RegisterContributionsService,
)

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class PluginContributionsFeature:
    """Lifecycle adapter for registering plugin contributions."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature adapter.

        Args:
            spec: Feature specification declaring capabilities and config keys.
        """
        self.spec = spec
        self._service: RegisterContributionsService | None = None

    @property
    def service(self) -> RegisterContributionsService | None:
        """Return the running RegisterContributionsService instance.

        Returns:
            The service instance if mounted, else None.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature into the given feature context.

        Args:
            context: FeatureContext providing service resolution and registration.
            config: Optional configuration dictionary or object.
        """
        raw_config = config if isinstance(config, dict) else {}
        cfg = PluginContributionsConfig.from_dict(raw_config)
        self._service = RegisterContributionsService(config=cfg)
        context.provide(REGISTER_CONTRIBUTIONS_CAPABILITY, self._service)


def feature() -> PluginContributionsFeature:
    """Entry point factory for the Plugin Contributions feature.

    Returns:
        New PluginContributionsFeature instance.
    """
    return PluginContributionsFeature()
