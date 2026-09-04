"""Database-backed market directory and instrument browsing for D-IFACE.

Reads 'instruments' table in haruquantai.db and projects rows into MarketDirectory.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

_DEFAULT_DB_PATH: Final[Path] = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "data"
    / "database"
    / "haruquantai.db"
)


def _utc_now_iso() -> str:
    """Return current UTC time formatted as an ISO-8601 string.

    Returns:
        ISO-8601 timestamp string.
    """
    return datetime.now(UTC).isoformat()


def _get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Obtain a SQLite database connection with row factory configured.

    Args:
        db_path: Optional explicit database path.

    Returns:
        Active SQLite connection.
    """
    target = Path(db_path) if db_path is not None else _DEFAULT_DB_PATH
    conn = sqlite3.connect(str(target))
    conn.row_factory = sqlite3.Row
    return conn


def list_market_directory(
    query: str | None = None,
    cursor: str | None = None,
    limit: int = 50,
    request_id: str = "req-markets",
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Read bounded categorized market directory rows from instruments table.

    Args:
        query: Optional substring match on symbol or description.
        cursor: Optional cursor representing the last symbol on previous page.
        limit: Maximum number of rows to return per page.
        request_id: Identifier of the invoking request.
        db_path: Optional explicit database path.

    Returns:
        Dictionary conforming to MarketDirectory schema.
    """
    conn = _get_connection(db_path)
    try:
        cur = conn.cursor()
        sql = """
            SELECT
                canonical_symbol AS symbol,
                coalesce(description, canonical_symbol) AS name,
                asset_class,
                digits,
                default_spread AS spread
            FROM instruments
        """
        params: list[Any] = []
        conditions: list[str] = []

        if query and query.strip():
            conditions.append("(canonical_symbol LIKE ? OR description LIKE ?)")
            q = f"%{query.strip()}%"
            params.extend([q, q])

        if cursor and cursor.strip():
            conditions.append("canonical_symbol > ?")
            params.append(cursor.strip())

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        sql += " ORDER BY canonical_symbol LIMIT ?"
        params.append(limit + 1)

        cur.execute(sql, params)
        raw_rows = cur.fetchall()

        has_more = len(raw_rows) > limit
        selected_rows = raw_rows[:limit]
        next_cursor = None
        if has_more and selected_rows:
            next_cursor = str(selected_rows[-1]["symbol"])

        rows: list[dict[str, Any]] = []
        for r in selected_rows:
            rows.append(
                {
                    "symbol": str(r["symbol"]),
                    "name": str(r["name"]),
                    "asset_class": str(r["asset_class"]),
                    "source_id": "mt5",
                    "digits": int(r["digits"]) if r["digits"] is not None else 5,
                    "last": None,
                    "bid": None,
                    "ask": None,
                    "spread": float(r["spread"]) if r["spread"] is not None else None,
                    "volume": None,
                    "open": None,
                    "high": None,
                    "low": None,
                    "close": None,
                    "change": None,
                    "change_percent": None,
                }
            )

        return {
            "source_id": "mt5",
            "rows": rows,
            "limit": limit,
            "next_cursor": next_cursor,
            "revision": "v1",
            "generated_at": _utc_now_iso(),
            "request_id": request_id,
        }
    finally:
        conn.close()
