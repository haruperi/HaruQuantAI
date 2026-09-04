"""Database-backed watchlist management for D-IFACE.

Reads and writes 'watchlist' and 'watchlist_items' tables in haruquantai.db,
enforcing exactly-one-default per account and seeding on first read.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final
from uuid import uuid4

_DEFAULT_DB_PATH: Final[Path] = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "data"
    / "database"
    / "haruquantai.db"
)

_SEED_SYMBOLS: Final[tuple[tuple[str, str, str], ...]] = (
    ("mt5", "EURUSD", "Forex"),
    ("mt5", "GBPUSD", "Forex"),
    ("mt5", "USDJPY", "Forex"),
    ("mt5", "AUDUSD", "Forex"),
    ("mt5", "USDCAD", "Forex"),
    ("mt5", "USDCHF", "Forex"),
    ("mt5", "NZDUSD", "Forex"),
    ("mt5", "XAUUSD", "Commodities"),
)


def _utc_now_iso() -> str:
    """Return current UTC timestamp as ISO-8601 string.

    Returns:
        ISO-8601 formatted datetime string.
    """
    return datetime.now(UTC).isoformat()


def _get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Obtain SQLite connection with row factory configured.

    Args:
        db_path: Optional explicit database path.

    Returns:
        Configured SQLite connection.
    """
    target = Path(db_path) if db_path is not None else _DEFAULT_DB_PATH
    conn = sqlite3.connect(str(target))
    conn.row_factory = sqlite3.Row
    return conn


def list_watchlists(
    account_id: str,
    db_path: Path | str | None = None,
) -> list[dict[str, Any]]:
    """List ordered watchlists with nested items for the given account_id.

    Args:
        account_id: Account identifier.
        db_path: Optional explicit database path.

    Returns:
        List of watchlist dictionaries including nested items.
    """
    conn = _get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                watchlist_id, account_id, name, is_default, sort_order,
                created_at, updated_at
            FROM watchlist
            WHERE account_id = ?
            ORDER BY sort_order, created_at
            """,
            (account_id,),
        )
        rows = cur.fetchall()

        if not rows:
            now = _utc_now_iso()
            wid = f"id-{uuid4().hex}"
            cur.execute(
                """
                INSERT INTO watchlist (
                    watchlist_id, account_id, name, is_default, sort_order,
                    created_at, updated_at
                ) VALUES (?, ?, 'default', 1, 0, ?, ?)
                """,
                (wid, account_id, now, now),
            )
            for idx, (source_id, symbol, asset_class) in enumerate(_SEED_SYMBOLS):
                cur.execute(
                    """
                    INSERT INTO watchlist_items (
                        watchlist_id, source_id, symbol, sort_order,
                        created_at, asset_class
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (wid, source_id, symbol, idx, now, asset_class),
                )
            conn.commit()

            cur.execute(
                """
                SELECT
                    watchlist_id, account_id, name, is_default, sort_order,
                    created_at, updated_at
                FROM watchlist
                WHERE account_id = ?
                ORDER BY sort_order, created_at
                """,
                (account_id,),
            )
            rows = cur.fetchall()

        result: list[dict[str, Any]] = []
        for row in rows:
            wid = str(row["watchlist_id"])
            cur.execute(
                """
                SELECT source_id, symbol, sort_order, asset_class
                FROM watchlist_items
                WHERE watchlist_id = ?
                ORDER BY sort_order
                """,
                (wid,),
            )
            items = [
                {
                    "source_id": str(item["source_id"]),
                    "symbol": str(item["symbol"]),
                    "sort_order": int(item["sort_order"]),
                    "asset_class": str(item["asset_class"]),
                }
                for item in cur.fetchall()
            ]
            result.append(
                {
                    "watchlist_id": wid,
                    "account_id": str(row["account_id"]),
                    "name": str(row["name"]),
                    "is_default": bool(row["is_default"]),
                    "sort_order": int(row["sort_order"]),
                    "items": items,
                    "created_at": str(row["created_at"]),
                    "updated_at": str(row["updated_at"]),
                }
            )
        return result
    finally:
        conn.close()


def create_watchlist(
    account_id: str,
    name: str,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Create a new non-default watchlist for the given account.

    Args:
        account_id: Account identifier.
        name: Watchlist display name.
        db_path: Optional explicit database path.

    Returns:
        Created watchlist dictionary.

    Raises:
        ValueError: If name is empty.
    """
    clean_name = name.strip()
    if not clean_name:
        raise ValueError("Watchlist name cannot be empty.")

    conn = _get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT coalesce(max(sort_order), -1) + 1
            FROM watchlist
            WHERE account_id = ?
            """,
            (account_id,),
        )
        next_sort = int(cur.fetchone()[0])

        now = _utc_now_iso()
        wid = f"id-{uuid4().hex}"
        cur.execute(
            """
            INSERT INTO watchlist (
                watchlist_id, account_id, name, is_default, sort_order,
                created_at, updated_at
            ) VALUES (?, ?, ?, 0, ?, ?, ?)
            """,
            (wid, account_id, clean_name, next_sort, now, now),
        )
        conn.commit()

        return {
            "watchlist_id": wid,
            "account_id": account_id,
            "name": clean_name,
            "is_default": False,
            "sort_order": next_sort,
            "items": [],
            "created_at": now,
            "updated_at": now,
        }
    finally:
        conn.close()


def update_watchlist(
    watchlist_id: str,
    _account_id: str | None = None,
    name: str | None = None,
    symbols: list[str] | tuple[str, ...] | None = None,
    is_default: bool | None = None,
    sort_order: int | None = None,
    db_path: Path | str | None = None,
) -> dict[str, Any]:
    """Update name, symbols, is_default, or sort_order for a watchlist.

    Args:
        watchlist_id: Watchlist identifier.
        _account_id: Optional account identifier.
        name: Optional updated name.
        symbols: Optional updated list of symbol strings.
        is_default: Optional flag to promote this watchlist to default.
        sort_order: Optional display sort order integer.
        db_path: Optional explicit database path.

    Returns:
        Refreshed watchlist dictionary.

    Raises:
        LookupError: If watchlist does not exist.
    """
    conn = _get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT watchlist_id, account_id, name, is_default, sort_order
            FROM watchlist
            WHERE watchlist_id = ?
            """,
            (watchlist_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise LookupError("WATCHLIST_NOT_FOUND")

        actual_account_id = str(row["account_id"])
        now = _utc_now_iso()

        if is_default is True:
            cur.execute(
                "UPDATE watchlist SET is_default = 0 WHERE account_id = ?",
                (actual_account_id,),
            )
            cur.execute(
                """
                UPDATE watchlist
                SET is_default = 1, updated_at = ?
                WHERE watchlist_id = ?
                """,
                (now, watchlist_id),
            )

        if name is not None and name.strip():
            cur.execute(
                """
                UPDATE watchlist
                SET name = ?, updated_at = ?
                WHERE watchlist_id = ?
                """,
                (name.strip(), now, watchlist_id),
            )

        if sort_order is not None:
            cur.execute(
                """
                UPDATE watchlist
                SET sort_order = ?, updated_at = ?
                WHERE watchlist_id = ?
                """,
                (sort_order, now, watchlist_id),
            )

        if symbols is not None:
            cur.execute(
                "DELETE FROM watchlist_items WHERE watchlist_id = ?",
                (watchlist_id,),
            )
            for idx, symbol in enumerate(symbols):
                clean_sym = symbol.strip()
                if clean_sym:
                    cur.execute(
                        """
                        INSERT INTO watchlist_items (
                            watchlist_id, source_id, symbol, sort_order,
                            created_at, asset_class
                        ) VALUES (?, 'mt5', ?, ?, ?, '')
                        """,
                        (watchlist_id, clean_sym, idx, now),
                    )
            cur.execute(
                "UPDATE watchlist SET updated_at = ? WHERE watchlist_id = ?",
                (now, watchlist_id),
            )

        conn.commit()

        cur.execute(
            """
            SELECT
                watchlist_id, account_id, name, is_default, sort_order,
                created_at, updated_at
            FROM watchlist
            WHERE watchlist_id = ?
            """,
            (watchlist_id,),
        )
        updated_row = cur.fetchone()
        cur.execute(
            """
            SELECT source_id, symbol, sort_order, asset_class
            FROM watchlist_items
            WHERE watchlist_id = ?
            ORDER BY sort_order
            """,
            (watchlist_id,),
        )
        items = [
            {
                "source_id": str(item["source_id"]),
                "symbol": str(item["symbol"]),
                "sort_order": int(item["sort_order"]),
                "asset_class": str(item["asset_class"]),
            }
            for item in cur.fetchall()
        ]
        return {
            "watchlist_id": str(updated_row["watchlist_id"]),
            "account_id": str(updated_row["account_id"]),
            "name": str(updated_row["name"]),
            "is_default": bool(updated_row["is_default"]),
            "sort_order": int(updated_row["sort_order"]),
            "items": items,
            "created_at": str(updated_row["created_at"]),
            "updated_at": str(updated_row["updated_at"]),
        }
    finally:
        conn.close()


def delete_watchlist(
    watchlist_id: str,
    db_path: Path | str | None = None,
) -> bool:
    """Delete one non-default watchlist.

    Args:
        watchlist_id: Watchlist unique identifier.
        db_path: Optional explicit database path.

    Returns:
        True upon successful deletion.

    Raises:
        ValueError: If attempting to delete the default watchlist.
        LookupError: If watchlist does not exist.
    """
    conn = _get_connection(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT is_default FROM watchlist WHERE watchlist_id = ?",
            (watchlist_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise LookupError("WATCHLIST_NOT_FOUND")
        if bool(row["is_default"]):
            raise ValueError("CANNOT_DELETE_DEFAULT_WATCHLIST")

        cur.execute(
            "DELETE FROM watchlist_items WHERE watchlist_id = ?",
            (watchlist_id,),
        )
        cur.execute(
            "DELETE FROM watchlist WHERE watchlist_id = ?",
            (watchlist_id,),
        )
        conn.commit()
        return True
    finally:
        conn.close()
