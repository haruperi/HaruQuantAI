"""Account watchlist management: the primary domain-logic module.

Purpose:
    Own the durable account-watchlist store: a standalone ``users``
    table (identity gap G2 remains open), ``api_watchlists``, and
    ``watchlist_items`` per the ratified legacy-compatible schema. The
    service enforces the exactly-one-default-per-account invariant,
    rejects deleting the current default, seeds one curated default
    watchlist per account on first read, and serves LIST / CREATE /
    UPDATE / DELETE through the workspace manage-watchlists capability.

Key capabilities:
    * Seed one curated default watchlist per account on first LIST.
    * Enforce unique (account_id, name) and exactly-one-default.
    * Replace the complete ordered item list on UPDATE.
    * Fail closed with typed WorkspaceFailure codes.

Python API usage:
    service = WatchlistService(ManageWatchlistsConfig())
    result = await service.manage_watchlists(request)

CLI usage:
    uv run python -m app.services.workspace.manage_watchlists.manage_watchlists
"""

from __future__ import annotations

import contextlib
import sqlite3
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from uuid import uuid7

from app.contracts.common.models import ProblemDetails
from app.contracts.workspace.errors import WorkspaceFailure
from app.contracts.workspace.models import (
    ManageWatchlistsRequest,
    ManageWatchlistsSuccess,
    WatchlistItemRecord,
    WatchlistRecord,
)
from app.services.workspace.manage_watchlists.config import ManageWatchlistsConfig

_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

# Curated seed set for a fresh account's default watchlist (legacy
# behaviour): the owner-traded forex majors.
_SEED_SYMBOLS = (
    ("local", "EURUSD", "Forex"),
    ("local", "GBPUSD", "Forex"),
    ("local", "USDJPY", "Forex"),
    ("local", "XAUUSD", "Commodities"),
)


def _utc_now() -> str:
    """Return the current instant as a canonical wire timestamp.

    Returns:
        Fixed-width UTC timestamp string.
    """
    return datetime.now(UTC).strftime(_TIMESTAMP_FORMAT)


def _failure(
    request_id: str,
    code: str,
    title: str,
    detail: str,
    status: int,
) -> WorkspaceFailure:
    """Build a typed workspace failure envelope.

    Args:
        request_id: Echoed request identifier.
        code: Closed workspace failure code.
        title: Short failure title.
        detail: Bounded human-readable detail.
        status: HTTP-equivalent status.

    Returns:
        Structured WorkspaceFailure envelope.
    """
    return WorkspaceFailure(
        request_id=request_id,
        code=code,  # type: ignore[arg-type]
        problem=ProblemDetails(
            title=title,
            status=status,
            code=code,
            detail=detail,
        ),
    )


class WatchlistService:
    """ManageWatchlistsCapability provider over the durable store."""

    def __init__(self, config: ManageWatchlistsConfig | None = None) -> None:
        """Open (or create) the watchlist database.

        Args:
            config: Optional configuration dataclass.
        """
        self._config = config or ManageWatchlistsConfig()
        if self._config.database_path is not None:
            self._conn = sqlite3.connect(
                self._config.database_path, check_same_thread=False
            )
        else:
            self._conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        if self._config.auto_migrate:
            self._init_db()

    def _init_db(self) -> None:
        """Create the standalone users and watchlist tables."""
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL
                ) STRICT
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS api_watchlists (
                    watchlist_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    name TEXT NOT NULL CHECK (name <> ''),
                    is_default INTEGER NOT NULL CHECK (is_default IN (0, 1)),
                    sort_order INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE (account_id, name),
                    FOREIGN KEY (account_id) REFERENCES users(user_id)
                        ON DELETE RESTRICT
                ) STRICT
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS watchlist_items (
                    watchlist_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    symbol TEXT NOT NULL CHECK (symbol <> ''),
                    sort_order INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    asset_class TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY (watchlist_id, source_id, symbol),
                    FOREIGN KEY (watchlist_id) REFERENCES api_watchlists(watchlist_id)
                        ON DELETE RESTRICT
                ) STRICT, WITHOUT ROWID
                """
            )

    def _ensure_account(self, account_id: str) -> None:
        """Create the standalone account row when absent.

        Args:
            account_id: Account identifier (a standalone users row).
        """
        with self._conn:
            self._conn.execute(
                "INSERT OR IGNORE INTO users (user_id, username, created_at) "
                "VALUES (?, ?, ?)",
                (account_id, account_id, _utc_now()),
            )

    def _seed_default(self, account_id: str) -> None:
        """Seed one curated default watchlist for a fresh account.

        Args:
            account_id: Account identifier.
        """
        row = self._conn.execute(
            "SELECT COUNT(*) AS count FROM api_watchlists WHERE account_id = ?",
            (account_id,),
        ).fetchone()
        if row["count"] > 0:
            return
        now = _utc_now()
        watchlist_id = str(uuid7())
        with self._conn:
            self._conn.execute(
                "INSERT INTO api_watchlists (watchlist_id, account_id, name, "
                "is_default, sort_order, created_at, updated_at) "
                "VALUES (?, ?, 'Default', 1, 0, ?, ?)",
                (watchlist_id, account_id, now, now),
            )
            self._conn.executemany(
                "INSERT INTO watchlist_items (watchlist_id, source_id, symbol, "
                "sort_order, created_at, asset_class) VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (
                        watchlist_id,
                        source_id,
                        symbol,
                        index,
                        now,
                        asset_class,
                    )
                    for index, (source_id, symbol, asset_class) in enumerate(
                        _SEED_SYMBOLS
                    )
                ],
            )

    def _load_watchlist(self, row: sqlite3.Row) -> WatchlistRecord:
        """Project one stored row (plus items) into a watchlist record.

        Args:
            row: The api_watchlists row.

        Returns:
            Complete watchlist record with ordered items.
        """
        items = self._conn.execute(
            "SELECT source_id, symbol, sort_order, asset_class FROM "
            "watchlist_items WHERE watchlist_id = ? ORDER BY sort_order, symbol",
            (row["watchlist_id"],),
        ).fetchall()
        return WatchlistRecord(
            watchlist_id=row["watchlist_id"],
            account_id=row["account_id"],
            name=row["name"],
            is_default=bool(row["is_default"]),
            sort_order=row["sort_order"],
            items=tuple(
                WatchlistItemRecord(
                    source_id=item["source_id"],
                    symbol=item["symbol"],
                    sort_order=item["sort_order"],
                    asset_class=item["asset_class"],
                )
                for item in items
            ),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _find(
        self, account: str, watchlist_id: str, request_id: str = ""
    ) -> sqlite3.Row | WorkspaceFailure:
        """Fetch one owned watchlist row or a typed not-found failure.

        Args:
            account: Owning account.
            watchlist_id: Target watchlist.
            request_id: Request identifier echoed into failures.

        Returns:
            The stored row, or a WorkspaceFailure.
        """
        row: sqlite3.Row | None = self._conn.execute(
            "SELECT * FROM api_watchlists WHERE account_id = ? AND watchlist_id = ?",
            (account, watchlist_id),
        ).fetchone()
        if row is None:
            return _failure(
                request_id,
                "WORKSPACE_NOT_FOUND",
                "Watchlist not found",
                f"No watchlist {watchlist_id} owned by this account.",
                404,
            )
        return row

    async def manage_watchlists(
        self,
        request: ManageWatchlistsRequest,
    ) -> ManageWatchlistsSuccess | WorkspaceFailure:
        """Serve one operation-discriminated watchlist request.

        Args:
            request: LIST, CREATE, UPDATE, or DELETE request.

        Returns:
            The operation result on success, otherwise a typed failure.
        """
        account = request.account_id or self._config.default_account_id
        self._ensure_account(account)
        handler: Callable[
            [str, ManageWatchlistsRequest],
            Awaitable[ManageWatchlistsSuccess | WorkspaceFailure],
        ]
        if request.operation == "LIST":
            handler = self._list
        elif request.operation == "CREATE":
            handler = self._create
        elif request.operation == "UPDATE":
            handler = self._update
        else:
            handler = self._delete
        return await handler(account, request)

    async def _list(
        self, account: str, request: ManageWatchlistsRequest
    ) -> ManageWatchlistsSuccess | WorkspaceFailure:
        """List every watchlist owned by the account.

        Returns:
            Every owned watchlist with its ordered items.
        """
        self._seed_default(account)
        rows = self._conn.execute(
            "SELECT * FROM api_watchlists WHERE account_id = ? "
            "ORDER BY sort_order, created_at",
            (account,),
        ).fetchall()
        return ManageWatchlistsSuccess(
            request_id=request.request_id,
            watchlists=tuple(self._load_watchlist(row) for row in rows),
        )

    async def _create(
        self, account: str, request: ManageWatchlistsRequest
    ) -> ManageWatchlistsSuccess | WorkspaceFailure:
        """Create one new empty, non-default watchlist.

        Returns:
            The created watchlist record.

        Raises:
            ValueError: If the request omits the name.
        """
        if request.name is None:
            message = "CREATE requires name"
            raise ValueError(message)
        name = request.name
        existing = self._conn.execute(
            "SELECT 1 FROM api_watchlists WHERE account_id = ? AND name = ?",
            (account, name),
        ).fetchone()
        if existing is not None:
            return _failure(
                request.request_id,
                "WORKSPACE_VALIDATION_FAILED",
                "Name already used",
                f"A watchlist named {name!r} already exists.",
                409,
            )
        now = _utc_now()
        watchlist_id = str(uuid7())
        count_row = self._conn.execute(
            "SELECT COUNT(*) AS count FROM api_watchlists WHERE account_id = ?",
            (account,),
        ).fetchone()
        with self._conn:
            self._conn.execute(
                "INSERT INTO api_watchlists (watchlist_id, account_id, name, "
                "is_default, sort_order, created_at, updated_at) "
                "VALUES (?, ?, ?, 0, ?, ?, ?)",
                (
                    watchlist_id,
                    account,
                    name,
                    count_row["count"],
                    now,
                    now,
                ),
            )
        row = self._find(account, watchlist_id, request.request_id)
        if not isinstance(row, sqlite3.Row):
            return row
        return ManageWatchlistsSuccess(
            request_id=request.request_id,
            watchlist=self._load_watchlist(row),
        )

    def _rename_clash(
        self,
        account: str,
        request: ManageWatchlistsRequest,
        found: sqlite3.Row,
    ) -> WorkspaceFailure | None:
        """Check whether the requested rename collides with another name.

        Args:
            account: Owning account.
            request: UPDATE request carrying the optional new name.
            found: Current stored row.

        Returns:
            A typed collision failure, or None when the rename is safe.

        Raises:
            ValueError: If the request omits watchlist_id.
        """
        if request.name is None or request.name == found["name"]:
            return None
        if request.watchlist_id is None:
            message = "UPDATE requires watchlist_id"
            raise ValueError(message)
        clash = self._conn.execute(
            "SELECT 1 FROM api_watchlists WHERE account_id = ? AND name = ? "
            "AND watchlist_id <> ?",
            (account, request.name, request.watchlist_id),
        ).fetchone()
        if clash is None:
            return None
        return _failure(
            request.request_id,
            "WORKSPACE_VALIDATION_FAILED",
            "Name already used",
            f"A watchlist named {request.name!r} already exists.",
            409,
        )

    async def _update(
        self, account: str, request: ManageWatchlistsRequest
    ) -> ManageWatchlistsSuccess | WorkspaceFailure:
        """Apply present fields independently to one watchlist.

        Returns:
            The updated watchlist record.

        Raises:
            ValueError: If the request omits watchlist_id.
        """
        if request.watchlist_id is None:
            message = "UPDATE requires watchlist_id"
            raise ValueError(message)
        found = self._find(account, request.watchlist_id, request.request_id)
        if not isinstance(found, sqlite3.Row):
            return found
        clash = self._rename_clash(account, request, found)
        if clash is not None:
            return clash
        now = _utc_now()
        with self._conn:
            if request.name is not None:
                self._conn.execute(
                    "UPDATE api_watchlists SET name = ?, updated_at = ? "
                    "WHERE watchlist_id = ?",
                    (request.name, now, request.watchlist_id),
                )
            if request.sort_order is not None:
                self._conn.execute(
                    "UPDATE api_watchlists SET sort_order = ?, updated_at = ? "
                    "WHERE watchlist_id = ?",
                    (request.sort_order, now, request.watchlist_id),
                )
            if request.symbols:
                existing_classes = {
                    row["symbol"]: row["asset_class"]
                    for row in self._conn.execute(
                        "SELECT symbol, asset_class FROM watchlist_items "
                        "WHERE watchlist_id = ?",
                        (request.watchlist_id,),
                    ).fetchall()
                }
                self._conn.execute(
                    "DELETE FROM watchlist_items WHERE watchlist_id = ?",
                    (request.watchlist_id,),
                )
                self._conn.executemany(
                    "INSERT INTO watchlist_items (watchlist_id, source_id, "
                    "symbol, sort_order, created_at, asset_class) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    [
                        (
                            request.watchlist_id,
                            "local",
                            symbol,
                            index,
                            now,
                            existing_classes.get(symbol, ""),
                        )
                        for index, symbol in enumerate(request.symbols)
                    ],
                )
                self._conn.execute(
                    "UPDATE api_watchlists SET updated_at = ? WHERE watchlist_id = ?",
                    (now, request.watchlist_id),
                )
            if request.is_default is True and not found["is_default"]:
                self._conn.execute(
                    "UPDATE api_watchlists SET is_default = 0, updated_at = ? "
                    "WHERE account_id = ? AND is_default = 1",
                    (now, account),
                )
                self._conn.execute(
                    "UPDATE api_watchlists SET is_default = 1, updated_at = ? "
                    "WHERE watchlist_id = ?",
                    (now, request.watchlist_id),
                )
            if request.is_default is False and found["is_default"]:
                return _failure(
                    request.request_id,
                    "WORKSPACE_VALIDATION_FAILED",
                    "Cannot demote the default",
                    "Promote another watchlist to default instead.",
                    409,
                )
        row = self._find(account, request.watchlist_id, request.request_id)
        if not isinstance(row, sqlite3.Row):
            return row
        return ManageWatchlistsSuccess(
            request_id=request.request_id,
            watchlist=self._load_watchlist(row),
        )

    async def _delete(
        self, account: str, request: ManageWatchlistsRequest
    ) -> ManageWatchlistsSuccess | WorkspaceFailure:
        """Delete one non-default watchlist.

        Returns:
            A deletion confirmation result.

        Raises:
            ValueError: If the request omits watchlist_id.
        """
        if request.watchlist_id is None:
            message = "UPDATE requires watchlist_id"
            raise ValueError(message)
        found = self._find(account, request.watchlist_id, request.request_id)
        if not isinstance(found, sqlite3.Row):
            return found
        if found["is_default"]:
            return _failure(
                request.request_id,
                "WORKSPACE_VALIDATION_FAILED",
                "Cannot delete the default",
                "Promote another watchlist to default first.",
                409,
            )
        with self._conn:
            self._conn.execute(
                "DELETE FROM watchlist_items WHERE watchlist_id = ?",
                (request.watchlist_id,),
            )
            self._conn.execute(
                "DELETE FROM api_watchlists WHERE watchlist_id = ?",
                (request.watchlist_id,),
            )
        return ManageWatchlistsSuccess(
            request_id=request.request_id,
            deleted=True,
        )

    def close(self) -> None:
        """Close the underlying SQLite connection."""
        with contextlib.suppress(sqlite3.Error):
            self._conn.close()


def _run_usage_example() -> None:
    """Run the bounded public usage demonstration.

    Raises:
        RuntimeError: If any verified behavior differs from the contract.
    """
    import asyncio

    async def demo() -> None:
        service = WatchlistService(ManageWatchlistsConfig())
        account = ManageWatchlistsConfig().default_account_id
        listing = await service.manage_watchlists(
            ManageWatchlistsRequest(
                request_id=str(uuid7()),
                capability_snapshot_id=str(uuid7()),
                account_id=account,
                operation="LIST",
            )
        )
        if not isinstance(listing, ManageWatchlistsSuccess):
            raise TypeError("usage verification: seeded LIST failed")
        if len(listing.watchlists) != 1 or not listing.watchlists[0].is_default:
            raise RuntimeError("usage verification: seeding invariant failed")
        if len(listing.watchlists[0].items) != len(_SEED_SYMBOLS):
            raise RuntimeError("usage verification: seed items missing")

        created = await service.manage_watchlists(
            ManageWatchlistsRequest(
                request_id=str(uuid7()),
                capability_snapshot_id=str(uuid7()),
                account_id=account,
                operation="CREATE",
                name="Scalping",
            )
        )
        if (
            not isinstance(created, ManageWatchlistsSuccess)
            or created.watchlist is None
        ):
            raise TypeError("usage verification: CREATE failed")

        duplicate = await service.manage_watchlists(
            ManageWatchlistsRequest(
                request_id=str(uuid7()),
                capability_snapshot_id=str(uuid7()),
                account_id=account,
                operation="CREATE",
                name="Scalping",
            )
        )
        if not isinstance(duplicate, WorkspaceFailure):
            raise TypeError("usage verification: uniqueness not enforced")

        delete_default = await service.manage_watchlists(
            ManageWatchlistsRequest(
                request_id=str(uuid7()),
                capability_snapshot_id=str(uuid7()),
                account_id=account,
                operation="DELETE",
                watchlist_id=listing.watchlists[0].watchlist_id,
            )
        )
        if not isinstance(delete_default, WorkspaceFailure):
            raise TypeError("usage verification: default deletion allowed")

        service.close()
        print(
            "Usage verification passed: "
            f"seeded={len(listing.watchlists[0].items)} "
            f"created={created.watchlist.name} "
            "invariants=enforced"
        )

    asyncio.run(demo())


if __name__ == "__main__":
    _run_usage_example()
