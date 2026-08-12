"""Authoritative Watchlists-owned persistence migration manifest."""

import hashlib

from app.services.data import build_migration_step
from app.utils import canonical_json

_WATCHLISTS_STATEMENTS = (
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
        FOREIGN KEY (account_id) REFERENCES api_accounts(user_id)
            ON DELETE RESTRICT
    ) STRICT
    """.strip(),
    # The database enforces at most one default watchlist per account.
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_api_watchlists_one_default "
    "ON api_watchlists(account_id) WHERE is_default = 1",
    "CREATE INDEX IF NOT EXISTS idx_api_watchlists_account "
    "ON api_watchlists(account_id)",
    """
    CREATE TABLE IF NOT EXISTS api_watchlist_items (
        watchlist_id TEXT NOT NULL,
        source_id TEXT NOT NULL,
        symbol TEXT NOT NULL CHECK (symbol <> ''),
        sort_order INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (watchlist_id, source_id, symbol),
        FOREIGN KEY (watchlist_id) REFERENCES api_watchlists(watchlist_id)
            ON DELETE RESTRICT
    ) STRICT, WITHOUT ROWID
    """.strip(),
    "CREATE INDEX IF NOT EXISTS idx_api_watchlist_items_watchlist "
    "ON api_watchlist_items(watchlist_id)",
)
_WATCHLISTS_CHECKSUM = hashlib.sha256(
    canonical_json(
        {
            "domain": "api",
            "migration": "api-0007",
            "sql": _WATCHLISTS_STATEMENTS,
        }
    ).encode("utf-8")
).hexdigest()


def get_watchlist_migration_steps() -> tuple[object, ...]:
    """Return the immutable Watchlists migration definitions."""
    return (
        build_migration_step(
            domain="api",
            migration_id="api-0007",
            checksum=_WATCHLISTS_CHECKSUM,
            statements=_WATCHLISTS_STATEMENTS,
        ),
    )


__all__ = ("get_watchlist_migration_steps",)
