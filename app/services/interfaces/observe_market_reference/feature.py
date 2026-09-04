"""Feature lifecycle mount for the market reference gateway."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.data.capabilities import BROWSE_REFERENCE_CAPABILITY
from app.contracts.interfaces.capabilities import (
    OBSERVE_MARKET_REFERENCE_CAPABILITY,
)
from app.services.interfaces.observe_market_reference.config import (
    ObserveMarketReferenceConfig,
    from_dict,
)
from app.services.interfaces.observe_market_reference.gateway import (
    MarketReferenceGateway,
)
from app.services.interfaces.observe_market_reference.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class ObserveMarketReferenceFeature:
    """Composable feature package providing market reference operations."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature with its specification.

        Args:
            spec: Feature specification declaring the served capability.
        """
        self.spec = spec
        self._gateway: MarketReferenceGateway | None = None

    @property
    def gateway(self) -> MarketReferenceGateway | None:
        """Return the mounted gateway, or None before mount.

        Returns:
            Active gateway instance if mounted, otherwise None.
        """
        return self._gateway

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the gateway against the resolved Data provider.

        Args:
            context: Scoped runtime context for this feature.
            config: Mapping, ObserveMarketReferenceConfig, or None.

        Raises:
            ValueError: If configuration contains unknown keys.
            TypeError: If configuration has an unsupported type.
        """
        if config is None or isinstance(config, dict):
            parsed = from_dict(config)
        elif isinstance(config, ObserveMarketReferenceConfig):
            parsed = config
        else:
            message = (
                "observe-market-reference configuration must be a mapping or config"
            )
            raise TypeError(message)

        provider = context.optional(BROWSE_REFERENCE_CAPABILITY)
        gateway = MarketReferenceGateway(parsed, provider=provider)
        self._gateway = gateway
        context.register_callback(gateway.close)
        context.provide(OBSERVE_MARKET_REFERENCE_CAPABILITY, gateway)


def feature() -> ObserveMarketReferenceFeature:
    """Factory for discovery via entry points.

    Returns:
        New ObserveMarketReferenceFeature instance.
    """
    return ObserveMarketReferenceFeature()
