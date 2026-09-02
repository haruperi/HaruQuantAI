"""Feature lifecycle mount implementation for MetaTrader 5 Connection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.broker.capabilities import (
    BROKER_OPERATIONS_CAPABILITY,
    PROVIDER_METATRADER_CAPABILITY,
)
from app.services.brokers.metatrader.client import MetaTraderService
from app.services.brokers.metatrader.config import MetaTraderConfig
from app.services.brokers.metatrader.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class MetaTraderFeature:
    """Composable feature package providing MetaTrader 5 live capabilities."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and state.
        """
        self.spec = spec
        self._service: MetaTraderService | None = None

    @property
    def service(self) -> MetaTraderService | None:
        """Return the underlying MetaTrader service instance.

        Returns:
            The MetaTraderService instance, or None if unmounted.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the MetaTrader capabilities.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or object.
        """
        raw_config = config if isinstance(config, dict) else None
        parsed_config = (
            config
            if isinstance(config, MetaTraderConfig)
            else MetaTraderConfig.from_dict(raw_config)
        )

        self._service = MetaTraderService(config=parsed_config)
        context.provide(BROKER_OPERATIONS_CAPABILITY, self._service)
        context.provide(PROVIDER_METATRADER_CAPABILITY, self._service)


def feature() -> MetaTraderFeature:
    """Factory function for discovery via entry points.

    Returns:
        New MetaTraderFeature instance.
    """
    return MetaTraderFeature()
