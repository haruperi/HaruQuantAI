"""Feature composition and lifecycle mounting for Mock Broker Feed."""

from typing import TYPE_CHECKING

from app.contracts.broker.market_data import BROKER_MARKET_DATA
from app.services.broker.mock_feed.config import MockFeedConfig
from app.services.broker.mock_feed.feed import MockBrokerMarketData
from app.services.broker.mock_feed.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class MockFeedFeature:
    """Feature package providing mock broker market data capability."""

    spec: FeatureSpec = SPEC

    async def mount(
        self,
        context: FeatureContext,
        config: object,
    ) -> None:
        """Mount feature and register broker market data capability.

        Args:
            context: Scoped feature context.
            config: Feature configuration dictionary or object.
        """
        cfg_dict = config if isinstance(config, dict) else {}
        feed_config = MockFeedConfig.from_dict(cfg_dict)
        service = MockBrokerMarketData(feed_config)

        context.provide(BROKER_MARKET_DATA, service)


def create_feature() -> MockFeedFeature:
    """Entry point factory creating MockFeedFeature instance.

    Returns:
        New MockFeedFeature instance.
    """
    return MockFeedFeature()
