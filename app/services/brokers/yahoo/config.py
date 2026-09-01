"""Strict feature configuration for the Yahoo provider."""

from __future__ import annotations

from dataclasses import dataclass

from app.services.brokers.canonical_contracts import (
    BrokerConnectionConfig,
    BrokerEnvironment,
    BrokerId,
)

_ALLOWED_KEYS = frozenset(
    {
        "profile_id",
        "profile_version_id",
        "profile_version",
        "account_ref",
        "environment",
        "probe_symbol",
        "connect_timeout_sec",
        "request_timeout_sec",
    }
)


@dataclass(frozen=True, slots=True)
class YahooConfig:
    """Trusted Yahoo sandbox provider configuration."""

    profile_id: str
    profile_version_id: str
    account_ref: str
    probe_symbol: str
    environment: str = "SANDBOX"
    profile_version: int = 1
    connect_timeout_sec: float = 10.0
    request_timeout_sec: float = 10.0

    @classmethod
    def from_dict(cls, values: dict[str, object]) -> "YahooConfig":
        """Validate explicit Yahoo provider configuration."""
        unknown = set(values) - _ALLOWED_KEYS
        if unknown:
            raise ValueError(f"unknown config keys: {sorted(unknown)}")
        parsed: dict[str, str] = {}
        for key in ("profile_id", "profile_version_id", "account_ref", "probe_symbol"):
            value = values.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{key} must be a non-empty string")
            parsed[key] = value
        environment = values.get("environment", "SANDBOX")
        if environment != "SANDBOX":
            raise ValueError("Yahoo is SANDBOX-only")
        profile_version = values.get("profile_version", 1)
        if not isinstance(profile_version, int) or isinstance(profile_version, bool) or profile_version < 1:
            raise ValueError("profile_version must be a positive integer")
        connect_timeout = values.get("connect_timeout_sec", 10.0)
        request_timeout = values.get("request_timeout_sec", 10.0)
        if not isinstance(connect_timeout, (int, float)) or connect_timeout <= 0:
            raise ValueError("connect_timeout_sec must be positive")
        if not isinstance(request_timeout, (int, float)) or request_timeout <= 0:
            raise ValueError("request_timeout_sec must be positive")
        return cls(
            profile_id=parsed["profile_id"],
            profile_version_id=parsed["profile_version_id"],
            account_ref=parsed["account_ref"],
            probe_symbol=parsed["probe_symbol"],
            profile_version=profile_version,
            connect_timeout_sec=float(connect_timeout),
            request_timeout_sec=float(request_timeout),
        )

    def to_legacy_connection(self) -> BrokerConnectionConfig:
        """Build the provider-local donor adapter configuration."""
        return BrokerConnectionConfig(
            broker_id=BrokerId.YAHOO,
            environment=BrokerEnvironment.SANDBOX,
            provider_enabled=True,
            connect_timeout_sec=self.connect_timeout_sec,
            request_timeout_sec=self.request_timeout_sec,
            transport_reconnect_max_attempts=3,
            stream_buffer_size=1_000,
            circuit_failure_threshold=5,
            circuit_recovery_timeout_sec=30.0,
            circuit_half_open_max_calls=1,
            account_reference=None,
            credentials=None,
            endpoint=None,
            auto_connect=False,
            probe_symbol=self.probe_symbol,
        )
