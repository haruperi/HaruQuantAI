"""Internal SQLite persistence for Dukascopy provider credentials."""

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


def get_dukascopy_credentials(
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Load Dukascopy credentials from central SQLite settings table."""
    conn = _get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='settings'"
        )
        if not cur.fetchone():
            return {"username": None, "password": None, "account_id": None}

        params = (
            "credentials.dukascopy_username",
            "credentials.dukascopy_password",
            "credentials.dukascopy_account_id",
        )
        cur.execute(
            "SELECT key, value FROM settings WHERE key IN (?, ?, ?)",
            params,
        )
        rows = dict(cur.fetchall())
        return {
            "username": rows.get("credentials.dukascopy_username"),
            "password": rows.get("credentials.dukascopy_password"),
            "account_id": rows.get("credentials.dukascopy_account_id"),
        }
    except Exception as exc:
        logger.warning("Failed to load Dukascopy credentials from database: %s", exc)
        return {"username": None, "password": None, "account_id": None}
    finally:
        conn.close()
