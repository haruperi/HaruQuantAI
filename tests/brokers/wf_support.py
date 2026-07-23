"""Shared helpers for Broker workflow usage scripts."""

from __future__ import annotations

import sys
from pathlib import Path

from pydantic import SecretStr

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.services.brokers import (
    BrokerConnectionConfig,
    BrokerConnectionStatus,
    BrokerEnvironment,
    BrokerId,
    BrokerResult,
)
from app.utils import settings


class _WorkflowSettings(settings.AppSettings):
    """Local runtime settings for workflow examples with MT5 credentials."""

    mt5_environment: str = "demo"
    mt5_login: SecretStr | None = None
    mt5_password: SecretStr | None = None
    mt5_server: SecretStr | None = None
    mt5_terminal_path: SecretStr | None = None


def _workflow_settings() -> _WorkflowSettings:
    """Load runtime settings from `.env` and the current process.

    Returns:
        Validated workflow settings.
    """
    return _WorkflowSettings()


def _environment_from_settings(value: str) -> BrokerEnvironment:
    """Map workflow environment value to a broker environment enum.

    Returns:
        Parsed environment, defaulting safely to demo.
    """
    normalized = value.strip().lower()
    try:
        return BrokerEnvironment(normalized)
    except ValueError:
        return BrokerEnvironment.DEMO


def build_mt5_connection_config(
    *,
    connect_timeout_sec: float = 1.0,
    request_timeout_sec: float = 1.0,
    stream_buffer_size: int = 8,
) -> BrokerConnectionConfig:
    """Build a bounded MT5 connection config from environment-provided settings.

    Env variables are sourced through ``from app.utils import settings``.

    Falls back to offline placeholder credentials when broker credentials are not
    present so script execution remains deterministic in offline environments.

    Returns:
        Bounded non-production MT5 connection configuration.
    """
    configured = _workflow_settings()
    if (
        configured.mt5_login is not None
        and configured.mt5_password is not None
        and configured.mt5_server is not None
    ):
        credentials: dict[str, SecretStr] = {
            "login": configured.mt5_login,
            "password": configured.mt5_password,
            "server": configured.mt5_server,
        }
        account_reference = configured.mt5_login.get_secret_value()
    else:
        account_reference = "100001"
        credentials = {
            "login": SecretStr(account_reference),
            "password": SecretStr("offline-placeholder"),
            "server": SecretStr("Offline-Demo"),
        }
    if configured.mt5_terminal_path is not None:
        credentials["terminal_path"] = configured.mt5_terminal_path

    return BrokerConnectionConfig(
        broker_id=BrokerId.MT5,
        environment=_environment_from_settings(configured.mt5_environment),
        provider_enabled=True,
        connect_timeout_sec=connect_timeout_sec,
        request_timeout_sec=request_timeout_sec,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=stream_buffer_size,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1.0,
        circuit_half_open_max_calls=1,
        account_reference=account_reference,
        credentials=credentials,
    )


def print_result(label: str, result: BrokerResult[object]) -> None:
    """Print a bounded result summary for workflow verification."""
    operation = result.operation.value if result.operation is not None else "unknown"
    if result.error is not None:
        print(f"{label}: {operation} -> {result.status} {result.error.code.value}")
    else:
        print(f"{label}: {operation} -> {result.status}")


def print_connection_status(
    label: str,
    result: BrokerResult[BrokerConnectionStatus],
) -> None:
    """Print one canonical connection status result."""
    if result.data is None:
        print(f"{label}: no status payload ({result.operation.value})")
        return
    print(
        f"{label}: {result.operation.value} -> {result.status} "
        f"{result.data.state} transport={result.data.transport_connected}"
    )
