"""Feature composition and lifecycle mounting for Historical Bars."""

from typing import TYPE_CHECKING

from app.contracts.broker.market_data import BROKER_MARKET_DATA
from app.contracts.data.bar_cache import BAR_CACHE
from app.contracts.data.historical_bars import HISTORICAL_BARS
from app.services.data.historical_bars.config import HistoricalBarsConfig
from app.services.data.historical_bars.manifest import SPEC
from app.services.data.historical_bars.retrieve import HistoricalBarsService

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class HistoricalBarsFeature:
    """Feature package providing normalized historical bars capability."""

    spec: FeatureSpec = SPEC

    async def mount(
        self,
        context: FeatureContext,
        config: object,
    ) -> None:
        """Mount the feature and resolve required and optional capabilities."""
        cfg_dict = config if isinstance(config, dict) else {}
        bars_config = HistoricalBarsConfig.from_dict(cfg_dict)
        market_data = context.require(BROKER_MARKET_DATA)
        cache = context.optional(BAR_CACHE) if bars_config.cache_enabled else None
        service = HistoricalBarsService(market_data=market_data, cache=cache)
        context.provide(HISTORICAL_BARS, service)


def create_feature() -> HistoricalBarsFeature:
    """Create a HistoricalBarsFeature instance."""
    return HistoricalBarsFeature()
