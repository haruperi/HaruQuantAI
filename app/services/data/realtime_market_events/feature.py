"""Feature lifecycle mount implementation for Real-Time Market Events."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.data.capabilities import STREAM_MARKET_EVENTS_CAPABILITY
from app.services.data.realtime_market_events.config import (
    RealtimeMarketEventsConfig,
)
from app.services.data.realtime_market_events.manifest import SPEC
from app.services.data.realtime_market_events.realtime_market_events import (
    StreamMarketEventsService,
)

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext
    from app.kernel.feature import FeatureSpec


def _parse_config(config: object) -> RealtimeMarketEventsConfig:
    """Parse and validate configuration input.

    Args:
        config: Configuration dictionary or typed config object.

    Returns:
        Validated RealtimeMarketEventsConfig instance.

    Raises:
        TypeError: If any configuration value is of invalid type.
    """
    cfg = RealtimeMarketEventsConfig()
    if not isinstance(config, dict):
        return config if isinstance(config, RealtimeMarketEventsConfig) else cfg

    db_path = config.get("database_path", cfg.database_path)
    buffer_capacity = config.get("buffer_capacity", cfg.buffer_capacity)
    if not isinstance(buffer_capacity, int):
        msg = "buffer_capacity must be an integer"
        raise TypeError(msg)

    max_subs = config.get("max_subscriptions", cfg.max_subscriptions)
    if not isinstance(max_subs, int):
        msg = "max_subscriptions must be an integer"
        raise TypeError(msg)

    max_insts = config.get(
        "max_instruments_per_subscription",
        cfg.max_instruments_per_subscription,
    )
    if not isinstance(max_insts, int):
        msg = "max_instruments_per_subscription must be an integer"
        raise TypeError(msg)

    stale_t = config.get("stale_timeout_seconds", cfg.stale_timeout_seconds)
    if not isinstance(stale_t, int):
        msg = "stale_timeout_seconds must be an integer"
        raise TypeError(msg)

    hb_t = config.get("heartbeat_timeout_seconds", cfg.heartbeat_timeout_seconds)
    if not isinstance(hb_t, int):
        msg = "heartbeat_timeout_seconds must be an integer"
        raise TypeError(msg)

    max_replay = config.get("max_replay_limit", cfg.max_replay_limit)
    if not isinstance(max_replay, int):
        msg = "max_replay_limit must be an integer"
        raise TypeError(msg)

    default_ord = config.get("default_ordering_mode", cfg.default_ordering_mode)
    if not isinstance(default_ord, str):
        msg = "default_ordering_mode must be a string"
        raise TypeError(msg)

    backpressure = config.get("backpressure_policy", cfg.backpressure_policy)
    if not isinstance(backpressure, str):
        msg = "backpressure_policy must be a string"
        raise TypeError(msg)

    return RealtimeMarketEventsConfig(
        database_path=db_path,
        buffer_capacity=buffer_capacity,
        max_subscriptions=max_subs,
        max_instruments_per_subscription=max_insts,
        stale_timeout_seconds=stale_t,
        heartbeat_timeout_seconds=hb_t,
        max_replay_limit=max_replay,
        default_ordering_mode=default_ord,
        backpressure_policy=backpressure,
    )


class RealtimeMarketEventsFeature:
    """Composable feature package providing Real-Time Market Events capability."""

    def __init__(self, spec: FeatureSpec = SPEC) -> None:
        """Initialize the feature instance with its specification.

        Args:
            spec: Feature specification declaring capabilities and metadata.
        """
        self.spec = spec
        self._service: StreamMarketEventsService | None = None

    @property
    def service(self) -> StreamMarketEventsService | None:
        """Return the underlying real-time market events service instance.

        Returns:
            The service instance, or None if unmounted.
        """
        return self._service

    async def mount(self, context: FeatureContext, config: object) -> None:
        """Mount the feature and provide the stream market events capability.

        Args:
            context: Scoped runtime context for this feature.
            config: Configuration dictionary or RealtimeMarketEventsConfig instance.
        """
        cfg = _parse_config(config)
        self._service = StreamMarketEventsService(
            config=cfg,
            event_bus=getattr(context, "events", None)
            or getattr(context, "event_bus", None),
        )
        context.provide(STREAM_MARKET_EVENTS_CAPABILITY, self._service)


def feature() -> RealtimeMarketEventsFeature:
    """Factory function for discovery via entry points.

    Returns:
        New RealtimeMarketEventsFeature instance.
    """
    return RealtimeMarketEventsFeature()
