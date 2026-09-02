"""Feature lifecycle mount implementation for Service-Level Broker Resolver."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.broker.capabilities import BROKER_RESOLVER_CAPABILITY
from app.services.brokers.resolve.config import ResolveConfig
from app.services.brokers.resolve.manifest import SPEC
from app.services.brokers.resolve.router import ResolveService

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class ResolveFeature:
    """Composable feature package providing Service-Level Broker Resolver."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and state.
        """
        self.spec = spec
        self._service: ResolveService | None = None

    @property
    def service(self) -> ResolveService | None:
        """Return the underlying broker resolver service instance.

        Returns:
            The broker resolver service instance, or None if unmounted.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the broker resolver capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or object.
        """
        raw_config = config if isinstance(config, dict) else None
        parsed_config = (
            config
            if isinstance(config, ResolveConfig)
            else ResolveConfig.from_dict(raw_config)
        )

        self._service = ResolveService(config=parsed_config)
        context.provide(BROKER_RESOLVER_CAPABILITY, self._service)


def feature() -> ResolveFeature:
    """Factory function for discovery via entry points.

    Returns:
        New ResolveFeature instance.
    """
    return ResolveFeature()
