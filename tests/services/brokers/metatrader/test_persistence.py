"""Unit tests for MetaTrader 5 persistence layer."""

from __future__ import annotations

from pathlib import Path

from app.services.brokers.metatrader._persistence import (
    get_mt5_credentials,
    save_mt5_credentials,
)


def test_get_and_save_mt5_credentials(tmp_path: Path) -> None:
    """Verify storing and retrieving MT5 credentials in SQLite settings table."""
    db_file = tmp_path / "test_mt5_settings.db"

    # Default lookup on non-existent or empty db returns None values
    empty_creds = get_mt5_credentials(db_file)
    assert empty_creds["login"] is None
    assert empty_creds["server"] is None

    # Save credentials
    save_mt5_credentials(
        login=12345678,
        password="secret_password",  # pragma: allowlist secret
        server="Broker-Live-01",
        terminal_path="C:/Program Files/MetaTrader 5/terminal64.exe",
        db_path=db_file,
    )

    # Retrieve and verify
    creds = get_mt5_credentials(db_file)
    assert creds["login"] == 12345678
    assert creds["password"] == "secret_password"  # pragma: allowlist secret
    assert creds["server"] == "Broker-Live-01"
    assert creds["terminal_path"] == "C:/Program Files/MetaTrader 5/terminal64.exe"
    assert creds["enabled"] is True
