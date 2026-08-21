"""Feature composition and lifecycle mounting for Historical Bars."""

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
    """Feature package providing normalized historical bars capability."""

    spec: FeatureSpec = SPEC

    async def mount(
        self,
        context: FeatureContext,
        config: object,
    ) -> None:
        """Mount feature, resolve broker dependency, and register capability.

        Args:
            context: Scoped feature context.
            config: Feature configuration dictionary or object.
        """
        cfg_dict = config if isinstance(config, dict) else {}
        _bars_config = HistoricalBarsConfig.from_dict(cfg_dict)

        market_data = context.require(BROKER_MARKET_DATA)
        service = HistoricalBarsService(market_data=market_data)

        context.provide(HISTORICAL_BARS, service)


def create_feature() -> HistoricalBarsFeature:
    """Entry point factory creating HistoricalBarsFeature instance.

    Returns:
        New HistoricalBarsFeature instance.
    """
    return HistoricalBarsFeature()
