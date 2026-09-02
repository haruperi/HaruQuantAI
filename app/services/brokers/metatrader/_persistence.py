"""Persistence layer for MetaTrader 5 credentials and configuration."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_CENTRAL_DB_PATH = Path("data/database/haruquantai.db")


def _get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Open SQLite connection to the target database.

    Args:
        db_path: Optional path to SQLite database.

    Returns:
        SQLite connection handle with WAL mode enabled.
    """
    path = Path(db_path) if db_path is not None else DEFAULT_CENTRAL_DB_PATH
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def get_mt5_credentials(db_path: Path | str | None = None) -> dict[str, Any]:
    """Retrieve MetaTrader 5 credentials and terminal settings from database.

    Args:
        db_path: Optional path to SQLite central database.

    Returns:
        Dictionary containing login, password, server, terminal_path, and enabled status.
    """
    target = Path(db_path) if db_path is not None else DEFAULT_CENTRAL_DB_PATH
    if not target.exists():
        return {
            "login": None,
            "password": None,
            "server": None,
            "terminal_path": None,
            "enabled": True,
        }

    keys = [
        "credentials.mt5_login",
        "credentials.mt5_password",
        "credentials.mt5_server",
        "broker.mt5.terminal_path",
        "broker.mt5.enabled",
    ]

    conn = _get_connection(target)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='settings';"
        )
        if not cursor.fetchone():
            return {
                "login": None,
                "password": None,
                "server": None,
                "terminal_path": None,
                "enabled": True,
            }

        cursor.execute(
            "SELECT key, value FROM settings WHERE key IN (?, ?, ?, ?, ?);",
            (
                "credentials.mt5_login",
                "credentials.mt5_password",
                "credentials.mt5_server",
                "broker.mt5.terminal_path",
                "broker.mt5.enabled",
            ),
        )
        results = dict(cursor.fetchall())

        raw_login = results.get("credentials.mt5_login")
        login_val = (
            int(raw_login)
            if raw_login and str(raw_login).isdigit()
            else (raw_login or None)
        )
        enabled_val = results.get("broker.mt5.enabled")
        is_enabled = (
            str(enabled_val).lower() in ("true", "1")
            if enabled_val is not None
            else True
        )

        return {
            "login": login_val,
            "password": results.get("credentials.mt5_password") or None,
            "server": results.get("credentials.mt5_server") or None,
            "terminal_path": results.get("broker.mt5.terminal_path") or None,
            "enabled": is_enabled,
        }
    finally:
        conn.close()


def save_mt5_credentials(
    login: int | str | None = None,
    password: str | None = None,
    server: str | None = None,
    terminal_path: str | None = None,
    db_path: Path | str | None = None,
) -> None:
    """Save or update MetaTrader 5 credentials and terminal settings in the database.

    Args:
        login: Account login number.
        password: Account password.
        server: Broker server name.
        terminal_path: Path to terminal64.exe executable.
        db_path: Optional path to SQLite central database.
    """
    target = Path(db_path) if db_path is not None else DEFAULT_CENTRAL_DB_PATH
    conn = _get_connection(target)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                value_type TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                default_value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )

        items = [
            (
                "credentials.mt5_login",
                str(login or ""),
                "string",
                "credentials",
                "MT5 Login",
                "",
            ),
            (
                "credentials.mt5_password",
                str(password or ""),
                "string",
                "credentials",
                "MT5 Password",
                "",
            ),
            (
                "credentials.mt5_server",
                str(server or ""),
                "string",
                "credentials",
                "MT5 Server",
                "",
            ),
            (
                "broker.mt5.terminal_path",
                str(terminal_path or ""),
                "string",
                "broker",
                "MT5 Terminal Path",
                "",
            ),
        ]

        for key, value, vtype, cat, desc, dflt in items:
            cursor.execute(
                """
                INSERT INTO settings (key, value, value_type, category, description, default_value, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = excluded.updated_at;
                """,
                (key, value, vtype, cat, desc, dflt),
            )
        conn.commit()
    finally:
        conn.close()
