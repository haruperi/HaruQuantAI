"""Feature lifecycle mount for the market catalogue browsing gateway."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.catalogue.capabilities import CATALOG_INSTRUMENTS_CAPABILITY
from app.contracts.interfaces.capabilities import OBSERVE_MARKET_CATALOGUE_CAPABILITY
from app.services.interfaces.observe_market_catalogue.config import (
    ObserveMarketCatalogueConfig,
)
from app.services.interfaces.observe_market_catalogue.gateway import (
    MarketCatalogueGateway,
)
from app.services.interfaces.observe_market_catalogue.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class ObserveMarketCatalogueFeature:
    """Composable feature package providing market catalogue pages."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature with its specification.

        Args:
            spec: Feature specification declaring the served capability.
        """
        self.spec = spec
        self._gateway: MarketCatalogueGateway | None = None

    @property
    def gateway(self) -> MarketCatalogueGateway | None:
        """Return the mounted gateway, or None before mount.

        Returns:
            Active gateway instance if mounted, otherwise None.
        """
        return self._gateway

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the gateway against the resolved Catalogue provider.

        Args:
            context: Scoped runtime context for this feature.
            config: Mapping, ObserveMarketCatalogueConfig, or None.

        Raises:
            ValueError: If configuration contains unknown or invalid keys.
            TypeError: If configuration has an unsupported type.
            CapabilityUnavailableError: If the required Catalogue
                capability has no active provider.
        """
        if config is None or isinstance(config, dict):
            parsed = ObserveMarketCatalogueConfig.from_dict(config)
        elif isinstance(config, ObserveMarketCatalogueConfig):
            parsed = config
        else:
            message = (
                "observe-market-catalogue configuration must be a mapping, "
                "ObserveMarketCatalogueConfig, or None"
            )
            raise TypeError(message)
        provider = context.require(CATALOG_INSTRUMENTS_CAPABILITY)
        gateway = MarketCatalogueGateway(provider, parsed)
        context.register_callback(gateway.close)
        context.provide(OBSERVE_MARKET_CATALOGUE_CAPABILITY, gateway)
        self._gateway = gateway


def feature() -> ObserveMarketCatalogueFeature:
    """Factory for discovery via entry points.

    Returns:
        New ObserveMarketCatalogueFeature instance.
    """
    return ObserveMarketCatalogueFeature()
