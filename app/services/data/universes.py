"""Dynamic asset baskets and point-in-time constituent universe management.

Feature:
    FEAT-DATA-UNIVERSES

Purpose:
    Provides dynamic asset baskets with point-in-time constituent tracking,
    membership intervals (date_from, date_to), and survivorship-bias-free universe
    queries matching StrategyQuant X Universe / Basket architecture.

Invariants:
    * System baskets are protected against deletion.
    * Point-in-time constituent queries filter strictly by membership intervals.
    * Constituent symbols are stored in canonical uppercase format.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, override

from app.contracts.data import (
    DATA_PERSISTENCE,
    DATA_UNIVERSES,
    DataError,
    DataPersistenceService,
    UniverseBasket,
    UniverseNotFoundError,
)
from app.contracts.data import (
    UniverseManagerService as IUniverseManagerService,
)
from app.kernel.feature import FeatureSpec
from app.kernel.logging import get_logger

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext

logger = get_logger(__name__)


@dataclass(slots=True, frozen=True)
class UniverseConfig:
    """Configuration for universe management service."""

    max_basket_size: int = 5000


class UniverseManagerServiceImpl(IUniverseManagerService):
    """Concrete implementation of UniverseManagerService protocol."""

    def __init__(
        self,
        persistence: DataPersistenceService,
        config: UniverseConfig | None = None,
    ) -> None:
        """Initialize universe manager service.

        Args:
            persistence: Persistence service for universe baskets.
            config: Optional configuration.
        """
        self._persistence = persistence
        self._config = config or UniverseConfig()

    @override
    async def get_basket(self, name_or_id: str | int) -> UniverseBasket | None:
        """Retrieve basket definition by name or ID."""
        return await self._persistence.get_basket(name_or_id)

    @override
    async def list_baskets(self) -> list[UniverseBasket]:
        """List all asset baskets."""
        return await self._persistence.list_baskets()

    @override
    async def save_basket(self, basket: UniverseBasket) -> UniverseBasket:
        """Persist or update an asset basket definition."""
        if len(basket.constituents) > self._config.max_basket_size:
            msg = (
                f"Basket constituents count ({len(basket.constituents)}) "
                f"exceeds max_basket_size ({self._config.max_basket_size})"
            )
            raise DataError(msg)
        return await self._persistence.save_basket(basket)

    @override
    async def delete_basket(self, basket_id: int) -> bool:
        """Delete a basket definition from the database."""
        basket = await self._persistence.get_basket(basket_id)
        if basket is None:
            return False
        if basket.is_system:
            msg = f"Cannot delete system universe basket {basket.name}"
            raise DataError(msg)
        return await self._persistence.delete_basket(basket_id)

    @override
    async def get_point_in_time_constituents(
        self, basket_id: int, as_of: datetime
    ) -> list[str]:
        """Query active constituent symbols in a basket at a historical instant."""
        basket = await self._persistence.get_basket(basket_id)
        if basket is None:
            msg = f"Universe basket with ID {basket_id} not found"
            raise UniverseNotFoundError(msg)

        return [c.symbol for c in basket.constituents if c.is_active_at(as_of)]


SPEC: FeatureSpec = FeatureSpec(
    name="data.universes",
    provides=frozenset({DATA_UNIVERSES}),
    requires=frozenset({DATA_PERSISTENCE}),
    optional=frozenset(),
    description="Dynamic asset baskets and point-in-time constituent universes.",
)


class UniverseFeature:
    """Wire universe manager feature into kernel composition lifecycle."""

    def __init__(self, config: UniverseConfig | None = None) -> None:
        """Initialize feature with optional configuration.

        Args:
            config: Optional universe configuration.
        """
        self._config = config or UniverseConfig()

    @property
    def spec(self) -> FeatureSpec:
        """Return immutable feature specification."""
        return SPEC

    async def start(self, context: FeatureContext) -> None:
        """Resolve persistence and provide universe manager service.

        Args:
            context: Lifecycle feature context.
        """
        persistence = context.require(DATA_PERSISTENCE)
        service = UniverseManagerServiceImpl(persistence, self._config)
        context.provide(DATA_UNIVERSES, service)
        logger.info("data_universes_feature_started")


def feature() -> UniverseFeature:
    """Return an unmounted UniverseFeature instance.

    Returns:
        New UniverseFeature instance.
    """
    return UniverseFeature()


__all__ = [
    "SPEC",
    "UniverseConfig",
    "UniverseFeature",
    "UniverseManagerServiceImpl",
    "feature",
]
