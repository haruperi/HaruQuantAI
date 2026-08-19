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


_WATCHLISTS_0008_STATEMENTS = (
    "ALTER TABLE api_watchlist_items ADD COLUMN asset_class TEXT NOT NULL DEFAULT ''",
)
_WATCHLISTS_0008_CHECKSUM = hashlib.sha256(
    canonical_json(
        {
            "domain": "api",
            "migration": "api-0008",
            "sql": _WATCHLISTS_0008_STATEMENTS,
        }
    ).encode("utf-8")
).hexdigest()


_WATCHLISTS_0009_STATEMENTS = (
    "UPDATE api_watchlist_items SET asset_class = 'Forex' WHERE asset_class = '' AND "
    "symbol IN ('AUDCAD', 'AUDCHF', 'AUDJPY', 'AUDNZD', 'AUDUSD', 'CADCHF', 'CADJPY', "
    "'CHFJPY', 'EURAUD', 'EURCAD', 'EURCHF', 'EURGBP', 'EURJPY', 'EURNZD', 'EURUSD', "
    "'GBPAUD', 'GBPCAD', 'GBPCHF', 'GBPJPY', 'GBPNZD', 'GBPUSD', 'NZDCAD', 'NZDCHF', "
    "'NZDJPY', 'NZDUSD', 'USDCHF', 'USDCAD', 'USDJPY')",
    "UPDATE api_watchlist_items SET asset_class = 'Commodities' WHERE asset_class = '' "
    "AND symbol IN ('XAUUSD', 'XAUEUR', 'XAUGBP', 'XAUJPY', 'XAUAUD', 'XAUCHF', "
    "'XAGUSD', 'XPDUSD', 'XPTUSD', 'Copper', 'SpotBrent', 'SpotCrude', 'NatGas', "
    "'Gasoline')",
    "UPDATE api_watchlist_items SET asset_class = 'Indices' WHERE asset_class = '' "
    "AND symbol IN ('US500', 'US30', 'UK100', 'GER40', 'NAS100', 'JPN225', 'USDX', "
    "'EURX', 'JPYX')",
    "UPDATE api_watchlist_items SET asset_class = 'Stocks' WHERE asset_class = '' "
    "AND symbol IN ('AMZN.US-24', 'AAPL.US-24')",
    "UPDATE api_watchlist_items SET asset_class = 'Cryptocurrencies' "
    "WHERE asset_class = '' AND symbol IN ('BTCUSD', 'ETHUSD', 'LTCUSD')",
)
_WATCHLISTS_0009_CHECKSUM = hashlib.sha256(
    canonical_json(
        {
            "domain": "api",
            "migration": "api-0009",
            "sql": _WATCHLISTS_0009_STATEMENTS,
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
        build_migration_step(
            domain="api",
            migration_id="api-0008",
            checksum=_WATCHLISTS_0008_CHECKSUM,
            statements=_WATCHLISTS_0008_STATEMENTS,
        ),
        build_migration_step(
            domain="api",
            migration_id="api-0009",
            checksum=_WATCHLISTS_0009_CHECKSUM,
            statements=_WATCHLISTS_0009_STATEMENTS,
        ),
    )


__all__ = ("get_watchlist_migration_steps",)
