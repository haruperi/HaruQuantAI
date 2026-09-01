"""Lifecycle adapter for point-in-time market-news tracking."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.data.capabilities import TRACK_MARKET_NEWS_CAPABILITY
from app.services.data.track_market_news.config import TrackMarketNewsConfig
from app.services.data.track_market_news.manifest import SPEC
from app.services.data.track_market_news.news_store import MarketNewsStore
from app.services.data.track_market_news.track_market_news import TrackMarketNewsService

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class TrackMarketNewsFeature:
    """Composable point-in-time market-news feature."""

    spec = SPEC

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Parse configuration and publish market-news capability.

        Args:
            context: Scoped feature runtime context.
            config: Raw configuration mapping or trusted config instance.

        Raises:
            TypeError: If config has an unsupported type.
        """
        if isinstance(config, TrackMarketNewsConfig):
            parsed = config
        elif isinstance(config, dict):
            parsed = TrackMarketNewsConfig.from_dict(config)
        else:
            raise TypeError("config must be a dict or TrackMarketNewsConfig")
        context.provide(
            TRACK_MARKET_NEWS_CAPABILITY,
            TrackMarketNewsService(MarketNewsStore(parsed.database_path)),
        )


def create_feature() -> TrackMarketNewsFeature:
    """Create a fresh market-news feature instance.

    Returns:
        Unmounted feature instance.
    """
    return TrackMarketNewsFeature()
