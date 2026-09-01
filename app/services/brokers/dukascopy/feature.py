"""Lifecycle adapter for the Dukascopy provider feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.broker.internal import DUKASCOPY_PROVIDER_GATEWAY_CAPABILITY
from app.services.brokers.dukascopy.config import DukascopyConfig
from app.services.brokers.dukascopy.gateway import DukascopyGateway
from app.services.brokers.dukascopy.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class DukascopyFeature:
    """Composable Dukascopy read-only provider feature."""

    spec = SPEC

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Construct the provider gateway and register scoped teardown."""
        if isinstance(config, DukascopyConfig):
            parsed = config
        elif isinstance(config, dict):
            parsed = DukascopyConfig.from_dict(config)
        else:
            raise TypeError("config must be a dict or DukascopyConfig")
        gateway = DukascopyGateway(parsed)
        context.register_callback(gateway.close)
        context.provide(DUKASCOPY_PROVIDER_GATEWAY_CAPABILITY, gateway)


def create_feature() -> DukascopyFeature:
    """Create a fresh Dukascopy provider feature instance."""
    return DukascopyFeature()
