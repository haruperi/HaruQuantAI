"""Feature lifecycle mount for the market data observation gateway."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.data.capabilities import STREAM_MARKET_EVENTS_CAPABILITY
from app.contracts.interfaces.capabilities import OBSERVE_MARKET_DATA_CAPABILITY
from app.services.interfaces.observe_market_data.config import ObserveMarketDataConfig
from app.services.interfaces.observe_market_data.gateway import MarketDataGateway
from app.services.interfaces.observe_market_data.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec

_CONSUMER_TASK_NAME = "observe-market-data:consume"


class ObserveMarketDataFeature:
    """Composable feature package providing market tick observations."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature with its specification.

        Args:
            spec: Feature specification declaring the served capability.
        """
        self.spec = spec
        self._gateway: MarketDataGateway | None = None

    @property
    def gateway(self) -> MarketDataGateway | None:
        """Return the mounted gateway, or None before mount.

        Returns:
            Active gateway instance if mounted, otherwise None.
        """
        return self._gateway

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the gateway against the resolved Data stream provider.

        Args:
            context: Scoped runtime context for this feature.
            config: Mapping, ObserveMarketDataConfig, or None.

        Raises:
            ValueError: If configuration contains unknown or invalid keys.
            TypeError: If configuration has an unsupported type.
            CapabilityUnavailableError: If the required Data stream
                capability has no active provider.
        """
        if config is None or isinstance(config, dict):
            parsed = ObserveMarketDataConfig.from_dict(config)
        elif isinstance(config, ObserveMarketDataConfig):
            parsed = config
        else:
            message = (
                "observe-market-data configuration must be a mapping, "
                "ObserveMarketDataConfig, or None"
            )
            raise TypeError(message)
        provider = context.require(STREAM_MARKET_EVENTS_CAPABILITY)
        gateway = MarketDataGateway(provider, parsed)
        context.spawn(gateway.run(), name=_CONSUMER_TASK_NAME)
        context.register_callback(gateway.close)
        context.provide(OBSERVE_MARKET_DATA_CAPABILITY, gateway)
        self._gateway = gateway


def feature() -> ObserveMarketDataFeature:
    """Factory for discovery via entry points.

    Returns:
        New ObserveMarketDataFeature instance.
    """
    return ObserveMarketDataFeature()
