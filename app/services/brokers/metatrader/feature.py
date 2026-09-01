"""Feature lifecycle mount implementation for MetaTrader direct broker channel."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.broker.capabilities import PROVIDER_METATRADER_CAPABILITY
from app.services.brokers.metatrader.config import MetaTraderConfig
from app.services.brokers.metatrader.manifest import SPEC
from app.services.brokers.metatrader.metatrader import MetaTraderProviderService

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class MetaTraderFeature:
    """Composable feature package providing MetaTrader broker provider capability."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and state.
        """
        self.spec = spec
        self._service: MetaTraderProviderService | None = None

    @property
    def service(self) -> MetaTraderProviderService | None:
        """Return the underlying MetaTrader provider service instance.

        Returns:
            The provider service instance, or None if unmounted.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the broker.provider.metatrader capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or object.
        """
        cfg = MetaTraderConfig()
        if isinstance(config, MetaTraderConfig):
            cfg = config
        elif isinstance(config, dict):
            cfg = MetaTraderConfig(**config)

        self._service = MetaTraderProviderService(context=context, config=cfg)
        context.provide(PROVIDER_METATRADER_CAPABILITY, self._service)

    async def unmount(self, context: FeatureContext) -> None:
        """Unmount the feature and clean up resources.

        Args:
            context: Scoped runtime context for this feature.
        """
        del context
        if self._service is not None:
            await self._service.close()
        self._service = None


def feature() -> MetaTraderFeature:
    """Factory function for discovery via entry points.

    Returns:
        New MetaTraderFeature instance.
    """
    return MetaTraderFeature()
