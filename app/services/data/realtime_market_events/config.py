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
    # MT5 snapshot bridge listener (haruquant.mt5.snapshot.v2). Disabled by
    # default: authentication is fail-closed, so enabling requires a token.
    snapshot_bridge_enabled: bool = False
    snapshot_bridge_host: str = "127.0.0.1"
    snapshot_bridge_port: int = 9001
    snapshot_bridge_source_id: str = "mt5-terminal-1"
    snapshot_bridge_auth_token: str = ""
    snapshot_bridge_symbols: str = "EURUSD,GBPUSD,USDJPY,XAUUSD"

    def snapshot_bridge_symbol_tuple(self) -> tuple[str, ...]:
        """Split the configured bridge symbol list into a tuple.

        Returns:
            Non-empty trimmed symbols in configured order.
        """
        return tuple(
            symbol.strip()
            for symbol in self.snapshot_bridge_symbols.split(",")
            if symbol.strip()
        )
