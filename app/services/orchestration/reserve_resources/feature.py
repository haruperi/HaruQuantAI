"""Lifecycle adapter for finite resource admission."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.composition.logging import get_logger
from app.contracts.orchestration.capabilities import RESERVE_RESOURCES_CAPABILITY
from app.contracts.workspace.capabilities import (
    ADMINISTER_SETTINGS_CAPABILITY,
    PERSISTENCE_CAPABILITY,
)
from app.services.orchestration.reserve_resources._persistence import (
    ResourceReservationStore,
)
from app.services.orchestration.reserve_resources.config import (
    ReserveResourcesConfig,
    from_dict,
)
from app.services.orchestration.reserve_resources.manifest import SPEC
from app.services.orchestration.reserve_resources.reserve_resources import (
    ReserveResourcesService,
)

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

_LOGGER = get_logger("orchestration.reserve_resources.feature")


class ReserveResourcesFeature:
    """Mount one lifecycle-owned resource admission coordinator."""

    spec = SPEC

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Build and register the resource admission service.

        Args:
            context: Lifecycle-owned feature context.
            config: Mapping, parsed configuration, or None.

        Raises:
            TypeError: If config has an unsupported type.
            ValueError: If config contains invalid values.
        """
        if config is None or isinstance(config, dict):
            parsed = from_dict(config)
        elif isinstance(config, ReserveResourcesConfig):
            parsed = config
        else:
            raise TypeError(
                "reserve-resources config must be a mapping or ReserveResourcesConfig"
            )

        persistence_port = context.require(PERSISTENCE_CAPABILITY)
        settings_port = context.optional(ADMINISTER_SETTINGS_CAPABILITY)
        if settings_port is not None:
            _LOGGER.debug(
                "Administer settings capability available for resource limits"
            )

        store = ResourceReservationStore(persistence_port)
        service = ReserveResourcesService(store=store, policy=parsed.policy)

        context.register_callback(service.close)
        context.provide(RESERVE_RESOURCES_CAPABILITY, service)
        _LOGGER.info("Mounted ReserveResourcesFeature successfully")


def feature() -> ReserveResourcesFeature:
    """Return a new reserve resources feature instance."""
    return ReserveResourcesFeature()


def create_feature() -> ReserveResourcesFeature:
    """Return a new reserve resources feature instance (canonical factory)."""
    return ReserveResourcesFeature()
