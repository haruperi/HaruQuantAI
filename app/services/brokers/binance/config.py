"""Configuration dataclass for Binance direct broker channel."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BinanceConfig:
    """Configuration options for Binance direct broker channel."""

    probe_symbol: str | None = "BTCUSDT"
    api_key: str | None = None
    api_secret: str | None = None
    request_timeout_sec: float = 30.0
    connect_timeout_sec: float = 10.0
    circuit_failure_threshold: int = 5
    circuit_recovery_timeout_sec: float = 30.0
    circuit_half_open_max_calls: int = 1
    environment: str = "TESTNET"
    stream_buffer_size: int = 1000
