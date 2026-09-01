"""Lifecycle adapter for the Yahoo provider feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.broker.internal import YAHOO_PROVIDER_GATEWAY_CAPABILITY
from app.services.brokers.yahoo.config import YahooConfig
from app.services.brokers.yahoo.gateway import YahooGateway
from app.services.brokers.yahoo.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class YahooFeature:
    """Composable Yahoo read-only provider feature."""

    spec = SPEC

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Construct the provider gateway and register scoped teardown."""
        if isinstance(config, YahooConfig):
            parsed = config
        elif isinstance(config, dict):
            parsed = YahooConfig.from_dict(config)
        else:
            raise TypeError("config must be a dict or YahooConfig")
        gateway = YahooGateway(parsed)
        context.register_callback(gateway.close)
        context.provide(YAHOO_PROVIDER_GATEWAY_CAPABILITY, gateway)


def create_feature() -> YahooFeature:
    """Create a fresh Yahoo provider feature instance."""
    return YahooFeature()
