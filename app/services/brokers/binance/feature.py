"""Feature lifecycle mount implementation for Binance Connection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.broker.capabilities import (
    BROKER_OPERATIONS_CAPABILITY,
    PROVIDER_BINANCE_CAPABILITY,
)
from app.services.brokers.binance.client import BinanceClient
from app.services.brokers.binance.config import BinanceConfig
from app.services.brokers.binance.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class BinanceFeature:
    """Composable feature package providing Binance capabilities."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        self.spec = spec
        self._client: BinanceClient | None = None

    @property
    def client(self) -> BinanceClient | None:
        return self._client

    @property
    def service(self) -> BinanceClient | None:
        """Compatibility accessor for mounted client."""
        return self._client

    async def mount(self, context: FeatureContext, config: object) -> None:
        raw_config = config if isinstance(config, dict) else {}
        parsed_config = (
            config if isinstance(config, BinanceConfig) else BinanceConfig(**raw_config)
        )

        self._client = BinanceClient(config=parsed_config)
        context.provide(BROKER_OPERATIONS_CAPABILITY, self._client)
        context.provide(PROVIDER_BINANCE_CAPABILITY, self._client)


def feature() -> BinanceFeature:
    """Factory function for discovery via entry points."""
    return BinanceFeature()
