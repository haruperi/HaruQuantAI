"""Configuration dataclass for MetaTrader direct broker channel."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MetaTraderConfig:
    """Configuration options for MetaTrader direct broker channel."""

    terminal_path: str | None = None
    login: int | None = None
    password: str | None = None
    server: str | None = None
    environment: str = "DEMO"
    probe_symbol: str | None = "EURUSD"
    request_timeout_sec: float = 30.0
    connect_timeout_sec: float = 10.0
    circuit_failure_threshold: int = 5
    circuit_recovery_timeout_sec: float = 30.0
    circuit_half_open_max_calls: int = 1
    stream_buffer_size: int = 1000
