"""Feature lifecycle mount implementation for Dukascopy direct broker channel."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.broker.capabilities import PROVIDER_DUKASCOPY_CAPABILITY
from app.services.brokers.dukascopy.config import DukascopyConfig
from app.services.brokers.dukascopy.dukascopy import DukascopyProviderService
from app.services.brokers.dukascopy.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class DukascopyFeature:
    """Composable feature package providing Dukascopy broker provider capability."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and state.
        """
        self.spec = spec
        self._service: DukascopyProviderService | None = None

    @property
    def service(self) -> DukascopyProviderService | None:
        """Return the underlying Dukascopy provider service instance.

        Returns:
            The provider service instance, or None if unmounted.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the broker.provider.dukascopy capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or object.
        """
        cfg = DukascopyConfig()
        if isinstance(config, DukascopyConfig):
            cfg = config
        elif isinstance(config, dict):
            cfg = DukascopyConfig(**config)

        self._service = DukascopyProviderService(context=context, config=cfg)
        context.provide(PROVIDER_DUKASCOPY_CAPABILITY, self._service)

    async def unmount(self, context: FeatureContext) -> None:
        """Unmount the feature and clean up resources.

        Args:
            context: Scoped runtime context for this feature.
        """
        del context
        self._service = None


def feature() -> DukascopyFeature:
    """Factory function for discovery via entry points.

    Returns:
        New DukascopyFeature instance.
    """
    return DukascopyFeature()
