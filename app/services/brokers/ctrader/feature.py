"""Feature lifecycle mount implementation for cTrader direct broker channel."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.broker.capabilities import PROVIDER_CTRADER_CAPABILITY
from app.services.brokers.ctrader.config import CTraderConfig
from app.services.brokers.ctrader.ctrader import CTraderProviderService
from app.services.brokers.ctrader.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class CTraderFeature:
    """Composable feature package providing cTrader broker provider capability."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and state.
        """
        self.spec = spec
        self._service: CTraderProviderService | None = None

    @property
    def service(self) -> CTraderProviderService | None:
        """Return the underlying cTrader provider service instance.

        Returns:
            The provider service instance, or None if unmounted.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the broker.provider.ctrader capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or object.
        """
        cfg = CTraderConfig()
        if isinstance(config, CTraderConfig):
            cfg = config
        elif isinstance(config, dict):
            cfg = CTraderConfig(**config)

        self._service = CTraderProviderService(context=context, config=cfg)
        context.provide(PROVIDER_CTRADER_CAPABILITY, self._service)

    async def unmount(self, context: FeatureContext) -> None:
        """Unmount the feature and clean up resources.

        Args:
            context: Scoped runtime context for this feature.
        """
        del context
        if self._service is not None:
            await self._service.close()
        self._service = None


def feature() -> CTraderFeature:
    """Factory function for discovery via entry points.

    Returns:
        New CTraderFeature instance.
    """
    return CTraderFeature()
