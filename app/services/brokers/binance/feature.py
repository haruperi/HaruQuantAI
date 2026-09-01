"""Feature lifecycle mount implementation for Binance direct broker channel."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.broker.capabilities import PROVIDER_BINANCE_CAPABILITY
from app.services.brokers.binance.binance import BinanceProviderService
from app.services.brokers.binance.config import BinanceConfig
from app.services.brokers.binance.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class BinanceFeature:
    """Composable feature package providing Binance broker provider capability."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and state.
        """
        self.spec = spec
        self._service: BinanceProviderService | None = None

    @property
    def service(self) -> BinanceProviderService | None:
        """Return the underlying Binance provider service instance.

        Returns:
            The provider service instance, or None if unmounted.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the broker.provider.binance capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or object.
        """
        cfg = BinanceConfig()
        if isinstance(config, BinanceConfig):
            cfg = config
        elif isinstance(config, dict):
            cfg = BinanceConfig(**config)

        self._service = BinanceProviderService(context=context, config=cfg)
        context.provide(PROVIDER_BINANCE_CAPABILITY, self._service)

    async def unmount(self, context: FeatureContext) -> None:
        """Unmount the feature and clean up resources.

        Args:
            context: Scoped runtime context for this feature.
        """
        del context
        if self._service is not None:
            await self._service.close()
        self._service = None


def feature() -> BinanceFeature:
    """Factory function for discovery via entry points.

    Returns:
        New BinanceFeature instance.
    """
    return BinanceFeature()
