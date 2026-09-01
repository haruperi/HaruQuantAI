"""Lifecycle adapter for the Binance provider feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.broker.internal import BINANCE_PROVIDER_GATEWAY_CAPABILITY
from app.services.brokers.binance.config import BinanceConfig
from app.services.brokers.binance.gateway import BinanceGateway
from app.services.brokers.binance.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class BinanceFeature:
    """Composable Binance external-provider feature."""

    spec = SPEC

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Construct the provider gateway and register scoped teardown."""
        if isinstance(config, BinanceConfig):
            parsed = config
        elif isinstance(config, dict):
            parsed = BinanceConfig.from_dict(config)
        else:
            raise TypeError("config must be a dict or BinanceConfig")
        gateway = BinanceGateway(parsed)
        context.register_callback(gateway.close)
        context.provide(BINANCE_PROVIDER_GATEWAY_CAPABILITY, gateway)


def create_feature() -> BinanceFeature:
    """Create a fresh Binance feature instance."""
    return BinanceFeature()
