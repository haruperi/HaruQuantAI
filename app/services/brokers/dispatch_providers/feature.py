"""Lifecycle adapter for explicit Broker provider dispatch."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.broker.capabilities import (
    MANAGE_SESSIONS_CAPABILITY,
    READ_PROVIDER_STATE_CAPABILITY,
    TRANSPORT_ORDERS_CAPABILITY,
)
from app.contracts.broker.internal import PROVIDER_GATEWAY_CAPABILITIES
from app.services.brokers.dispatch_providers.config import DispatchProvidersConfig
from app.services.brokers.dispatch_providers.dispatch import DispatchProvidersService
from app.services.brokers.dispatch_providers.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class DispatchProvidersFeature:
    """Composable explicit provider-dispatch feature."""

    spec = SPEC

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Resolve installed provider gateways and publish public Broker ports."""
        if isinstance(config, DispatchProvidersConfig):
            parsed = config
        elif isinstance(config, dict):
            parsed = DispatchProvidersConfig.from_dict(config)
        else:
            raise TypeError("config must be a dict or DispatchProvidersConfig")

        gateways = tuple(
            gateway
            for capability in PROVIDER_GATEWAY_CAPABILITIES
            if (gateway := context.optional(capability)) is not None
        )
        service = DispatchProvidersService(gateways, parsed)
        context.provide(MANAGE_SESSIONS_CAPABILITY, service)
        context.provide(READ_PROVIDER_STATE_CAPABILITY, service)
        context.provide(TRANSPORT_ORDERS_CAPABILITY, service)


def create_feature() -> DispatchProvidersFeature:
    """Create a fresh provider dispatcher feature instance."""
    return DispatchProvidersFeature()
