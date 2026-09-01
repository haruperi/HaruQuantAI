"""Lifecycle adapter for the MetaTrader provider feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.broker.internal import MT5_PROVIDER_GATEWAY_CAPABILITY
from app.services.brokers.metatrader.config import MetaTraderConfig
from app.services.brokers.metatrader.gateway import MetaTraderGateway
from app.services.brokers.metatrader.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class MetaTraderFeature:
    """Composable MetaTrader external-provider feature."""

    spec = SPEC

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Construct the provider gateway and register scoped teardown."""
        if isinstance(config, MetaTraderConfig):
            parsed = config
        elif isinstance(config, dict):
            parsed = MetaTraderConfig.from_dict(config)
        else:
            raise TypeError("config must be a dict or MetaTraderConfig")
        gateway = MetaTraderGateway(parsed)
        context.register_callback(gateway.close)
        context.provide(MT5_PROVIDER_GATEWAY_CAPABILITY, gateway)


def create_feature() -> MetaTraderFeature:
    """Create a fresh MetaTrader feature instance."""
    return MetaTraderFeature()
