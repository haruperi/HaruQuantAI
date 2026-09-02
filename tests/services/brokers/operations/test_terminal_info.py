"""Unit tests for FR 1: Terminal Info and Environment Properties."""

from __future__ import annotations

from app.services.brokers.operations._terminal_info import (
    connect,
    disconnect,
    get_connection_status,
    get_platform_info,
    get_provider_specification,
    get_terminal_info,
    is_connected,
    ping,
)


def test_terminal_connect_disconnect_lifecycle() -> None:
    """Verify connect, is_connected, ping, and disconnect lifecycle."""
    disconnect()
    assert is_connected() is False
    assert ping() == 0.0

    conn_res = connect(account_id=12345, server="TestServer")
    assert conn_res["status"] == "connected"
    assert conn_res["connected"] is True
    assert conn_res["account_id"] == 12345
    assert is_connected() is True
    assert ping() > 0.0

    status = get_connection_status()
    assert status["connected"] is True
    assert status["account_id"] == 12345

    assert disconnect() is True
    assert is_connected() is False


def test_get_platform_and_terminal_info() -> None:
    """Verify platform info, terminal properties, and provider specifications."""
    connect()
    p_info = get_platform_info()
    assert "platform" in p_info
    assert "build" in p_info

    t_info = get_terminal_info()
    assert t_info["trade_allowed"] is True
    assert t_info["max_bars"] > 0

    spec = get_provider_specification()
    assert spec["supports_market_orders"] is True
    assert spec["max_orders"] >= 100
