"""Lifecycle adapter for immutable Data series storage."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.data.internal import DATA_SERIES_STORE_CAPABILITY
from app.services.data.manage_series.config import ManageSeriesConfig
from app.services.data.manage_series.manifest import SPEC
from app.services.data.manage_series.series_store import SeriesStoreService

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class ManageSeriesFeature:
    """Composable Data series-store feature."""

    spec = SPEC

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Parse configuration, construct the store, and publish its capability.

        Args:
            context: Scoped feature runtime context.
            config: Raw feature configuration mapping or trusted config instance.

        Raises:
            TypeError: If config is neither a mapping nor ManageSeriesConfig.
        """
        if isinstance(config, ManageSeriesConfig):
            parsed = config
        elif isinstance(config, dict):
            parsed = ManageSeriesConfig.from_dict(config)
        else:
            raise TypeError("config must be a dict or ManageSeriesConfig")
        context.provide(DATA_SERIES_STORE_CAPABILITY, SeriesStoreService(parsed))


def create_feature() -> ManageSeriesFeature:
    """Create a fresh series-store feature instance.

    Returns:
        Unmounted feature instance.
    """
    return ManageSeriesFeature()
