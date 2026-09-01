"""Lifecycle adapter for point-in-time series alignment."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.data.capabilities import ALIGN_SERIES_CAPABILITY
from app.contracts.data.internal import DATA_SERIES_STORE_CAPABILITY
from app.services.data.align_series.align_series import AlignSeriesService
from app.services.data.align_series.config import AlignSeriesConfig
from app.services.data.align_series.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class AlignSeriesFeature:
    """Composable point-in-time series-alignment feature."""

    spec = SPEC

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Resolve the immutable series store and publish alignment.

        Args:
            context: Scoped feature runtime context.
            config: Raw feature configuration or trusted config instance.

        Raises:
            TypeError: If configuration has the wrong type.
        """
        if isinstance(config, AlignSeriesConfig):
            parsed = config
        elif isinstance(config, dict):
            parsed = AlignSeriesConfig.from_dict(config)
        else:
            raise TypeError("config must be a dict or AlignSeriesConfig")
        del parsed
        store = context.require(DATA_SERIES_STORE_CAPABILITY)
        context.provide(ALIGN_SERIES_CAPABILITY, AlignSeriesService(store))


def create_feature() -> AlignSeriesFeature:
    """Create a fresh alignment feature.

    Returns:
        Unmounted feature instance.
    """
    return AlignSeriesFeature()
