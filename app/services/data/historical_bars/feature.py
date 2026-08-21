"""Lifecycle composition for the Historical Bars feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.broker.market_data import BROKER_MARKET_DATA
from app.contracts.data.historical_bars import HISTORICAL_BARS
from app.services.data.historical_bars.config import HistoricalBarsConfig
from app.services.data.historical_bars.manifest import SPEC
from app.services.data.historical_bars.retrieve import HistoricalBarsService

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class HistoricalBarsFeature:
    """Provide normalized historical bars through the active broker contract."""

    spec: FeatureSpec = SPEC

    async def mount(
        self,
        context: FeatureContext,
        config: object,
    ) -> None:
        """Resolve market data and publish the historical-bars service."""
        raw_config = config if isinstance(config, dict) else {}
        bars_config = HistoricalBarsConfig.from_dict(raw_config)
        service = HistoricalBarsService(
            market_data=context.require(BROKER_MARKET_DATA),
            default_timeframe=bars_config.default_timeframe,
        )
        context.provide(HISTORICAL_BARS, service)


def create_feature() -> HistoricalBarsFeature:
    """Create a HistoricalBarsFeature instance.

    Returns:
        New feature instance.
    """
    return HistoricalBarsFeature()
