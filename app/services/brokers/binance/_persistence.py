"""Internal SQLite persistence for Binance provider credentials."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_DB_PATH = Path("data/database/haruquantai.db")


def _get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    target = Path(db_path) if db_path is not None else _DEFAULT_DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target))
    conn.row_factory = sqlite3.Row
    return conn


def get_binance_credentials(
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Load Binance API credentials from central SQLite settings table."""
    conn = _get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='settings'"
        )
        if not cur.fetchone():
            return {"api_key": None, "api_secret": None}

        params = (
            "credentials.binance_api_key",
            "credentials.binance_api_secret",
        )
        cur.execute(
            "SELECT key, value FROM settings WHERE key IN (?, ?)",
            params,
        )
        rows = dict(cur.fetchall())
        return {
            "api_key": rows.get("credentials.binance_api_key"),
            "api_secret": rows.get("credentials.binance_api_secret"),
        }
    except Exception as exc:
        logger.warning("Failed to load Binance credentials from database: %s", exc)
        return {"api_key": None, "api_secret": None}
    finally:
        conn.close()
