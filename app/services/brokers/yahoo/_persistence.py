"""Internal SQLite persistence for Yahoo Finance provider preferences."""

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


def get_yahoo_preferences(
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Load Yahoo Finance preferences from central SQLite settings table."""
    conn = _get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='settings'"
        )
        if not cur.fetchone():
            return {"timeout": 30}

        cur.execute(
            "SELECT key, value FROM settings WHERE key = 'broker.yahoo.timeout'"
        )
        row = cur.fetchone()
        return {"timeout": int(row[1]) if row else 30}
    except Exception as exc:
        logger.warning("Failed to load Yahoo preferences from database: %s", exc)
        return {"timeout": 30}
    finally:
        conn.close()
