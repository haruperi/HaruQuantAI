"""Feature lifecycle mount implementation for Broker Provider Gateway."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.broker.capabilities import (
    MANAGE_SESSIONS_CAPABILITY,
    READ_PROVIDER_STATE_CAPABILITY,
    TRANSPORT_ORDERS_CAPABILITY,
)
from app.services.brokers.provider_gateway.config import ProviderGatewayConfig
from app.services.brokers.provider_gateway.manifest import SPEC
from app.services.brokers.provider_gateway.provider_gateway import (
    ProviderGatewayService,
)

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class ProviderGatewayFeature:
    """Composable feature package providing Broker Provider Gateway capabilities."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and state.
        """
        self.spec = spec
        self._service: ProviderGatewayService | None = None

    @property
    def service(self) -> ProviderGatewayService | None:
        """Return the underlying provider gateway service instance.

        Returns:
            The provider gateway service instance, or None if unmounted.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the three Broker business capabilities.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or object.
        """
        cfg = ProviderGatewayConfig()
        if isinstance(config, ProviderGatewayConfig):
            cfg = config
        elif isinstance(config, dict):
            cfg = ProviderGatewayConfig()

        self._service = ProviderGatewayService(context=context, config=cfg)
        context.provide(MANAGE_SESSIONS_CAPABILITY, self._service)
        context.provide(READ_PROVIDER_STATE_CAPABILITY, self._service)
        context.provide(TRANSPORT_ORDERS_CAPABILITY, self._service)


def feature() -> ProviderGatewayFeature:
    """Factory function for discovery via entry points.

    Returns:
        New ProviderGatewayFeature instance.
    """
    return ProviderGatewayFeature()
