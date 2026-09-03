"""Feature lifecycle mount implementation for Economic Calendar and News Evidence."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.data.capabilities import TRACK_MARKET_NEWS_CAPABILITY
from app.services.data.economic_news_evidence.config import (
    EconomicNewsEvidenceConfig,
)
from app.services.data.economic_news_evidence.economic_news_evidence import (
    TrackMarketNewsService,
)
from app.services.data.economic_news_evidence.manifest import SPEC

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


class EconomicNewsEvidenceFeature:
    """Composable feature package providing News Evidence capability."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and metadata.
        """
        self.spec = spec
        self._service: TrackMarketNewsService | None = None

    @property
    def service(self) -> TrackMarketNewsService | None:
        """Return the underlying news evidence service instance.

        Returns:
            The service instance, or None if unmounted.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the track market news capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or EconomicNewsEvidenceConfig instance.

        Raises:
            TypeError: If config parameters are invalid types.
        """
        cfg = EconomicNewsEvidenceConfig()
        if isinstance(config, dict):
            db_path = config.get("database_path", cfg.database_path)
            max_results = config.get("max_query_results", cfg.max_query_results)
            if not isinstance(max_results, int):
                msg = "max_query_results must be an integer"
                raise TypeError(msg)

            rate_limit = config.get(
                "default_rate_limit_per_minute",
                cfg.default_rate_limit_per_minute,
            )
            if not isinstance(rate_limit, int):
                msg = "default_rate_limit_per_minute must be an integer"
                raise TypeError(msg)

            max_payload = config.get(
                "max_payload_size_bytes", cfg.max_payload_size_bytes
            )
            if not isinstance(max_payload, int):
                msg = "max_payload_size_bytes must be an integer"
                raise TypeError(msg)

            freshness = config.get(
                "default_freshness_limit_seconds",
                cfg.default_freshness_limit_seconds,
            )
            if not isinstance(freshness, int):
                msg = "default_freshness_limit_seconds must be an integer"
                raise TypeError(msg)

            sources = config.get("allowed_sources", cfg.allowed_sources)
            if isinstance(sources, (list, set, tuple)):
                sources = frozenset(sources)
            elif not isinstance(sources, frozenset):
                msg = "allowed_sources must be a set or frozenset of strings"
                raise TypeError(msg)

            cfg = EconomicNewsEvidenceConfig(
                database_path=db_path,
                max_query_results=max_results,
                default_rate_limit_per_minute=rate_limit,
                max_payload_size_bytes=max_payload,
                default_freshness_limit_seconds=freshness,
                allowed_sources=sources,
            )
        elif isinstance(config, EconomicNewsEvidenceConfig):
            cfg = config

        self._service = TrackMarketNewsService(
            config=cfg,
            event_bus=getattr(context, "events", None)
            or getattr(context, "event_bus", None),
        )
        context.provide(TRACK_MARKET_NEWS_CAPABILITY, self._service)


def feature() -> EconomicNewsEvidenceFeature:
    """Factory function for discovery via entry points.

    Returns:
        New EconomicNewsEvidenceFeature instance.
    """
    return EconomicNewsEvidenceFeature()
