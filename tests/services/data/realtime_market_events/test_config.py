"""Unit tests for Real-Time Market Events configuration."""

from dataclasses import FrozenInstanceError

import pytest
from app.services.data.realtime_market_events.config import (
    RealtimeMarketEventsConfig,
)


def test_config_defaults() -> None:
    """Test default values for RealtimeMarketEventsConfig."""
    cfg = RealtimeMarketEventsConfig()
    assert cfg.database_path == ":memory:"
    assert cfg.buffer_capacity == 1_000
    assert cfg.max_subscriptions == 100
    assert cfg.max_instruments_per_subscription == 500
    assert cfg.stale_timeout_seconds == 30
    assert cfg.heartbeat_timeout_seconds == 15
    assert cfg.max_replay_limit == 10_000
    assert cfg.default_ordering_mode == "RECEIPT_ORDER"
    assert cfg.backpressure_policy == "DROP_AND_GAP"


def test_config_frozen() -> None:
    """Test that configuration instance is immutable."""
    cfg = RealtimeMarketEventsConfig()
    with pytest.raises(FrozenInstanceError):
        cfg.buffer_capacity = 500  # type: ignore[misc]
