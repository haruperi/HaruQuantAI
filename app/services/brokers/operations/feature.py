"""Feature lifecycle mount implementation for Broker Operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.broker.capabilities import BROKER_OPERATIONS_CAPABILITY
from app.services.brokers.operations.config import BrokerOperationsConfig
from app.services.brokers.operations.execute import BrokerOperationsService
from app.services.brokers.operations.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class BrokerOperationsFeature:
    """Composable feature package providing Broker Operations capabilities."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and state.
        """
        self.spec = spec
        self._service: BrokerOperationsService | None = None

    @property
    def service(self) -> BrokerOperationsService | None:
        """Return the underlying broker operations service instance.

        Returns:
            The broker operations service instance, or None if unmounted.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the broker operations capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or object.
        """
        raw_config = config if isinstance(config, dict) else None
        parsed_config = (
            config
            if isinstance(config, BrokerOperationsConfig)
            else BrokerOperationsConfig.from_dict(raw_config)
        )

        self._service = BrokerOperationsService(config=parsed_config)
        context.provide(BROKER_OPERATIONS_CAPABILITY, self._service)


def feature() -> BrokerOperationsFeature:
    """Factory function for discovery via entry points.

    Returns:
        New BrokerOperationsFeature instance.
    """
    return BrokerOperationsFeature()
