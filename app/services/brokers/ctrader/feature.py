"""Lifecycle adapter for the cTrader provider feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.broker.internal import CTRADER_PROVIDER_GATEWAY_CAPABILITY
from app.services.brokers.ctrader.config import CTraderConfig
from app.services.brokers.ctrader.gateway import CTraderGateway
from app.services.brokers.ctrader.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class CTraderFeature:
    """Composable cTrader external-provider feature."""

    spec = SPEC

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Construct the provider gateway and register scoped teardown."""
        if isinstance(config, CTraderConfig):
            parsed = config
        elif isinstance(config, dict):
            parsed = CTraderConfig.from_dict(config)
        else:
            raise TypeError("config must be a dict or CTraderConfig")
        gateway = CTraderGateway(parsed)
        context.register_callback(gateway.close)
        context.provide(CTRADER_PROVIDER_GATEWAY_CAPABILITY, gateway)


def create_feature() -> CTraderFeature:
    """Create a fresh cTrader feature instance."""
    return CTraderFeature()
