"""Strict feature configuration for the MetaTrader provider."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import SecretStr

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
        "credentials",
        "probe_symbol",
        "connect_timeout_sec",
        "request_timeout_sec",
    }
)


@dataclass(frozen=True, slots=True)
class MetaTraderConfig:
    """Trusted, process-local MetaTrader feature configuration."""

    profile_id: str
    profile_version_id: str
    account_ref: str
    environment: str
    credentials: dict[str, SecretStr]
    profile_version: int = 1
    probe_symbol: str | None = None
    connect_timeout_sec: float = 10.0
    request_timeout_sec: float = 10.0

    @classmethod
    def from_dict(cls, values: dict[str, object]) -> "MetaTraderConfig":
        """Validate raw process-local provider configuration."""
        unknown = set(values) - _ALLOWED_KEYS
        if unknown:
            raise ValueError(f"unknown config keys: {sorted(unknown)}")
        required_text = ("profile_id", "profile_version_id", "account_ref", "environment")
        parsed: dict[str, str] = {}
        for key in required_text:
            value = values.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{key} must be a non-empty string")
            parsed[key] = value
        if parsed["environment"] not in {"LIVE", "DEMO"}:
            raise ValueError("MetaTrader environment must be LIVE or DEMO")
        raw_credentials = values.get("credentials")
        if not isinstance(raw_credentials, dict):
            raise ValueError("credentials must be a mapping supplied by runtime secret resolution")
        credentials: dict[str, SecretStr] = {}
        for key, value in raw_credentials.items():
            if not isinstance(key, str) or not isinstance(value, str) or not value:
                raise ValueError("credentials require non-empty string keys and values")
            credentials[key] = SecretStr(value)
        if {"login", "password", "server"} - set(credentials):
            raise ValueError("MetaTrader requires login, password, and server credentials")
        if credentials["login"].get_secret_value() != parsed["account_ref"]:
            raise ValueError("account_ref must match the resolved MetaTrader login")
        profile_version = values.get("profile_version", 1)
        if not isinstance(profile_version, int) or isinstance(profile_version, bool) or profile_version < 1:
            raise ValueError("profile_version must be a positive integer")
        probe_symbol = values.get("probe_symbol")
        if probe_symbol is not None and (not isinstance(probe_symbol, str) or not probe_symbol.strip()):
            raise ValueError("probe_symbol must be a non-empty string when supplied")
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
            environment=parsed["environment"],
            credentials=credentials,
            profile_version=profile_version,
            probe_symbol=probe_symbol,
            connect_timeout_sec=float(connect_timeout),
            request_timeout_sec=float(request_timeout),
        )

    def to_legacy_connection(self) -> BrokerConnectionConfig:
        """Build the provider-local donor adapter configuration."""
        return BrokerConnectionConfig(
            broker_id=BrokerId.MT5,
            environment=BrokerEnvironment[self.environment],
            provider_enabled=True,
            connect_timeout_sec=self.connect_timeout_sec,
            request_timeout_sec=self.request_timeout_sec,
            transport_reconnect_max_attempts=3,
            stream_buffer_size=1_000,
            circuit_failure_threshold=5,
            circuit_recovery_timeout_sec=30.0,
            circuit_half_open_max_calls=1,
            account_reference=self.account_ref,
            credentials=self.credentials,
            endpoint=None,
            auto_connect=False,
            probe_symbol=self.probe_symbol,
        )
