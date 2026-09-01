"""Feature lifecycle mount implementation for Yahoo direct broker channel."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.broker.capabilities import PROVIDER_YAHOO_CAPABILITY
from app.services.brokers.yahoo.config import YahooConfig
from app.services.brokers.yahoo.manifest import SPEC
from app.services.brokers.yahoo.yahoo import YahooProviderService

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class YahooFeature:
    """Composable feature package providing Yahoo broker provider capability."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and state.
        """
        self.spec = spec
        self._service: YahooProviderService | None = None

    @property
    def service(self) -> YahooProviderService | None:
        """Return the underlying Yahoo provider service instance.

        Returns:
            The provider service instance, or None if unmounted.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the broker.provider.yahoo capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or object.
        """
        cfg = YahooConfig()
        if isinstance(config, YahooConfig):
            cfg = config
        elif isinstance(config, dict):
            cfg = YahooConfig(**config)

        self._service = YahooProviderService(context=context, config=cfg)
        context.provide(PROVIDER_YAHOO_CAPABILITY, self._service)

    async def unmount(self, context: FeatureContext) -> None:
        """Unmount the feature and clean up resources.

        Args:
            context: Scoped runtime context for this feature.
        """
        del context
        self._service = None


def feature() -> YahooFeature:
    """Factory function for discovery via entry points.

    Returns:
        New YahooFeature instance.
    """
    return YahooFeature()
