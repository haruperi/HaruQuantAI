"""Shared helpers for Broker workflow usage scripts."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from app.services.brokers import (
    build_broker_connection_config,
    get_broker_value_field,
)
from app.utils import load_broker_provider_settings


def build_mt5_connection_config(
    *,
    connect_timeout_sec: float = 1.0,
    request_timeout_sec: float = 1.0,
    stream_buffer_size: int = 8,
) -> object:
    """Build a bounded MT5 connection config from environment-provided settings.

    Returns:
        Bounded non-production MT5 connection configuration.

    Raises:
        RuntimeError: If verified MT5 demo credentials are unavailable.
    """
    configured = load_broker_provider_settings()
    if (
        not configured.mt5_enabled
        or configured.mt5_environment != "demo"
        or configured.mt5_login is None
        or configured.mt5_password is None
        or configured.mt5_server is None
    ):
        raise RuntimeError("Verified MT5 demo credentials are unavailable")
    credentials = {
        "login": configured.mt5_login,
        "password": configured.mt5_password,
        "server": configured.mt5_server,
    }
    if configured.mt5_terminal_path is not None:
        credentials["terminal_path"] = configured.mt5_terminal_path

    return build_broker_connection_config(
        broker_id="mt5",
        environment="demo",
        provider_enabled=True,
        connect_timeout_sec=connect_timeout_sec,
        request_timeout_sec=request_timeout_sec,
        transport_reconnect_max_attempts=0,
        stream_buffer_size=stream_buffer_size,
        circuit_failure_threshold=2,
        circuit_recovery_timeout_sec=1.0,
        circuit_half_open_max_calls=1,
        account_reference=configured.mt5_login.get_secret_value(),
        credentials=credentials,
    )


def print_result(label: str, result: object) -> None:
    """Print a bounded result summary and substantive payload."""
    metadata = get_broker_value_field(result, "metadata")
    operation = get_broker_value_field(metadata, "extensions").get(
        "operation", "unknown"
    )
    error = get_broker_value_field(result, "error")
    status = get_broker_value_field(result, "status")
    if error is not None:
        print(
            f"{label}: {operation} -> {status} {get_broker_value_field(error, 'code')}"
        )
    else:
        print(
            f"{label}: {operation} -> {status} "
            f"data={get_broker_value_field(result, 'data')!r}"
        )


def print_connection_status(
    label: str,
    result: object,
) -> None:
    """Print one canonical connection status result."""
    data = get_broker_value_field(result, "data")
    metadata = get_broker_value_field(result, "metadata")
    operation = get_broker_value_field(metadata, "extensions").get(
        "operation", "unknown"
    )
    if data is None:
        print(f"{label}: no status payload ({operation})")
        return
    print(
        f"{label}: {operation} -> {get_broker_value_field(result, 'status')} "
        f"{get_broker_value_field(data, 'state')} "
        f"transport={get_broker_value_field(data, 'transport_connected')}"
    )
