"""Unit tests for MetaTrader 5 FR 1: Terminal Info and Environment."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from app.services.brokers.metatrader._terminal_info import (
    connect,
    disconnect,
    get_connection_status,
    get_platform_info,
    get_provider_specification,
    get_terminal_info,
    is_connected,
    ping,
)
from app.services.brokers.metatrader.client import MetaTraderClient


def test_terminal_connect_success() -> None:
    """Verify successful terminal initialization and state update via client instance."""
    mock_terminal = MagicMock()
    mock_terminal.connected = True
    mock_terminal.ping_last = 25000
    mock_terminal._asdict.return_value = {
        "connected": True,
        "build": 6140,
        "name": "MetaTrader 5",
        "ping_last": 25000,
    }

    mock_mt5 = MagicMock()
    mock_mt5.initialize.return_value = True
    mock_mt5.terminal_info.return_value = mock_terminal
    mock_mt5.version.return_value = (500, 6140, "2026-08-21")

    client = MetaTraderClient(mt5_module=mock_mt5)

    conn_res = connect(client=client)
    assert conn_res["status"] == "connected"
    assert conn_res["connected"] is True
    assert is_connected(client=client) is True
    assert ping(client=client) == 25.0

    status = get_connection_status(client=client)
    assert status["connected"] is True
    assert status["ping_ms"] == 25.0

    p_info = get_platform_info(client=client)
    assert p_info["platform"] == "mt5"
    assert p_info["build"] == 6140

    t_info = get_terminal_info(client=client)
    assert t_info["connected"] is True

    spec = get_provider_specification()
    assert spec["provider"] == "mt5"
    assert spec["supports_market_orders"] is True

    assert disconnect(client=client) is True
    assert is_connected(client=client) is False


def test_terminal_connect_failure_raises_error() -> None:
    """Verify initialization failure strictly raises RuntimeError with exact error."""
    mock_mt5 = MagicMock()
    mock_mt5.initialize.return_value = False
    mock_mt5.last_error.return_value = (-10004, "No IPC connection")

    client = MetaTraderClient(mt5_module=mock_mt5)

    with pytest.raises(
        RuntimeError,
        match=r"Failed to initialize MetaTrader 5 terminal: \[-10004\] No IPC connection",
    ):
        connect(login=99999, client=client)

    assert is_connected(client=client) is False


def test_ping_disconnected_raises_error() -> None:
    """Verify ping raises RuntimeError when disconnected."""
    mock_mt5 = MagicMock()
    client = MetaTraderClient(mt5_module=mock_mt5)
    disconnect(client=client)
    with pytest.raises(RuntimeError, match="MetaTrader 5 terminal is not connected"):
        ping(client=client)
