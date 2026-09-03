"""Configuration model for Real-Time Market Events."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RealtimeMarketEventsConfig:
    """Configuration for real-time market event streaming, buffering, and replay."""

    database_path: Path | str = ":memory:"
    buffer_capacity: int = 1_000
    max_subscriptions: int = 100
    max_instruments_per_subscription: int = 500
    stale_timeout_seconds: int = 30
    heartbeat_timeout_seconds: int = 15
    max_replay_limit: int = 10_000
    default_ordering_mode: str = "RECEIPT_ORDER"
    backpressure_policy: str = "DROP_AND_GAP"
