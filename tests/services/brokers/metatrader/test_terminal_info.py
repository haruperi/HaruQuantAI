"""Unit tests for MetaTrader 5 FR 1: Terminal Info and Environment."""

from __future__ import annotations

from unittest.mock import MagicMock

import app.services.brokers.metatrader._terminal_info as term_mod
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


def test_terminal_connect_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify successful terminal initialization and state update."""
    mock_terminal = MagicMock()
    mock_terminal.connected = True
    mock_terminal.ping_last = 25000
    mock_terminal._asdict.return_value = {
        "connected": True,
        "build": 6140,
        "name": "MetaTrader 5",
        "ping_last": 25000,
    }

    monkeypatch.setattr(term_mod.mt5, "initialize", lambda **kwargs: True)
    monkeypatch.setattr(term_mod.mt5, "terminal_info", lambda: mock_terminal)
    monkeypatch.setattr(term_mod.mt5, "version", lambda: (500, 6140, "2026-08-21"))

    conn_res = connect()
    assert conn_res["status"] == "connected"
    assert conn_res["connected"] is True
    assert is_connected() is True
    assert ping() == 25.0

    status = get_connection_status()
    assert status["connected"] is True
    assert status["ping_ms"] == 25.0

    p_info = get_platform_info()
    assert p_info["platform"] == "mt5"
    assert p_info["build"] == 6140

    t_info = get_terminal_info()
    assert t_info["connected"] is True

    spec = get_provider_specification()
    assert spec["provider"] == "mt5"
    assert spec["supports_market_orders"] is True

    assert disconnect() is True
    assert is_connected() is False


def test_terminal_connect_failure_raises_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify initialization failure strictly raises RuntimeError with exact error."""
    monkeypatch.setattr(term_mod.mt5, "initialize", lambda **kwargs: False)
    monkeypatch.setattr(
        term_mod.mt5, "last_error", lambda: (-10004, "No IPC connection")
    )

    with pytest.raises(
        RuntimeError,
        match=r"Failed to initialize MetaTrader 5 terminal: \[-10004\] No IPC connection",
    ):
        connect(login=99999)

    assert is_connected() is False


def test_ping_disconnected_raises_error() -> None:
    """Verify ping raises RuntimeError when disconnected."""
    disconnect()
    with pytest.raises(RuntimeError, match="MetaTrader 5 terminal is not connected"):
        ping()
