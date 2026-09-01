"""Lifecycle adapter for deterministic bar aggregation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.data.capabilities import AGGREGATE_BARS_CAPABILITY
from app.contracts.data.internal import DATA_SERIES_STORE_CAPABILITY
from app.services.data.aggregate_bars.aggregate_bars import AggregateBarsService
from app.services.data.aggregate_bars.config import AggregateBarsConfig
from app.services.data.aggregate_bars.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class AggregateBarsFeature:
    """Composable closed-bar aggregation feature."""

    spec = SPEC

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Resolve immutable storage and publish bar aggregation.

        Args:
            context: Scoped feature runtime context.
            config: Raw mapping or trusted config instance.

        Raises:
            TypeError: If config has an unsupported type.
        """
        if isinstance(config, AggregateBarsConfig):
            parsed = config
        elif isinstance(config, dict):
            parsed = AggregateBarsConfig.from_dict(config)
        else:
            raise TypeError("config must be a dict or AggregateBarsConfig")
        store = context.require(DATA_SERIES_STORE_CAPABILITY)
        context.provide(
            AGGREGATE_BARS_CAPABILITY,
            AggregateBarsService(store, parsed),
        )


def create_feature() -> AggregateBarsFeature:
    """Create a fresh aggregation feature instance.

    Returns:
        Unmounted feature instance.
    """
    return AggregateBarsFeature()
