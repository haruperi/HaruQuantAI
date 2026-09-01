"""Configuration dataclass for Dukascopy direct broker channel."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DukascopyConfig:
    """Configuration options for Dukascopy direct broker channel."""

    probe_symbol: str | None = "EURUSD"
    request_timeout_sec: float = 30.0
    circuit_failure_threshold: int = 5
    circuit_recovery_timeout_sec: float = 30.0
    circuit_half_open_max_calls: int = 1
    environment: str = "SANDBOX"
