"""Data-owned market-reference schema migration.

Replaces the empty step-006 reference tables (``data_symbols``,
``data_providers``, ``data_market_sessions``) with a consolidated
market-reference catalog conforming to the schema model in
``app/services/data/README.md``. The FEAT-DATA-02 artifact catalog stays
intact: ``data_instruments``, ``data_brokers``, and ``data_sessions`` absorb
the exact catalog-facing columns of the dropped tables under their original
names, so catalog persistence keeps working against the new tables.

Legacy source columns use the house type mapping: LONG -> INTEGER, DOUBLE ->
REAL, BOOLEAN -> INTEGER CHECK (x IN (0, 1)), and legacy-only columns are
nullable or defaulted because catalog writes do not supply them.
"""

from __future__ import annotations

import hashlib

from app.services.data.persistence.contracts import MigrationStep

_STATEMENTS = (
    "DROP INDEX IF EXISTS idx_data_symbols_class",
    "DROP INDEX IF EXISTS idx_data_sessions_active",
    "DROP TABLE IF EXISTS data_symbols",
    "DROP TABLE IF EXISTS data_providers",
    "DROP TABLE IF EXISTS data_market_sessions",
    """
    CREATE TABLE data_instruments (
        symbol_id TEXT PRIMARY KEY,
        canonical_symbol TEXT NOT NULL UNIQUE,
        asset_class TEXT NOT NULL,
        base_currency TEXT NOT NULL,
        quote_currency TEXT NOT NULL,
        digits INTEGER NOT NULL,
        tick_size_decimal TEXT NOT NULL,
        min_volume_decimal TEXT NOT NULL,
        max_volume_decimal TEXT NOT NULL,
        volume_step_decimal TEXT NOT NULL,
        contract_size_decimal TEXT NOT NULL DEFAULT '1',
        spec_json TEXT NOT NULL DEFAULT '{}',
        state TEXT NOT NULL,
        request_id TEXT NOT NULL DEFAULT '',
        correlation_id TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        deleted_at TEXT,
        description TEXT,
        point_value REAL,
        tick_size REAL,
        tick_step REAL,
        default_spread REAL DEFAULT 0,
        commissions TEXT,
        data_type INTEGER,
        exchange TEXT,
        country TEXT,
        sector TEXT,
        default_slippage REAL DEFAULT 0,
        swap TEXT DEFAULT NULL,
        order_size_multiplier REAL DEFAULT 1,
        order_size_step REAL DEFAULT 0,
        broker_id INTEGER DEFAULT -1,
        min_distance REAL DEFAULT 0.0
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX idx_data_instruments_class "
        "ON data_instruments(asset_class, canonical_symbol)"
    ),
    """
    CREATE TABLE data_brokers (
        provider_id TEXT PRIMARY KEY,
        provider_code TEXT NOT NULL UNIQUE,
        provider_kind TEXT NOT NULL,
        priority INTEGER NOT NULL DEFAULT 100,
        trust_tier TEXT NOT NULL,
        rate_limit INTEGER NOT NULL DEFAULT 0,
        rate_window_seconds INTEGER NOT NULL DEFAULT 1,
        license_json TEXT NOT NULL DEFAULT '{}',
        enabled INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
        request_id TEXT NOT NULL DEFAULT '',
        correlation_id TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        broker_id INTEGER UNIQUE,
        name TEXT,
        is_system INTEGER CHECK (is_system IN (0, 1)),
        description TEXT,
        stockpicker_use INTEGER DEFAULT 0,
        mt_use INTEGER DEFAULT 0,
        mt_timezone TEXT,
        postfix TEXT
    ) STRICT
    """.strip(),
    """
    CREATE TABLE data_sessions (
        session_id TEXT PRIMARY KEY,
        symbol_id TEXT,
        session_name TEXT,
        day_of_week INTEGER CHECK (day_of_week BETWEEN 0 AND 6),
        open_time_utc TEXT,
        close_time_utc TEXT,
        is_trading INTEGER DEFAULT 1 CHECK (is_trading IN (0, 1)),
        effective_from TEXT,
        effective_to TEXT,
        request_id TEXT NOT NULL DEFAULT '',
        correlation_id TEXT NOT NULL DEFAULT '',
        created_at TEXT,
        updated_at TEXT,
        broker_id INTEGER DEFAULT -1
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX idx_data_sessions_active "
        "ON data_sessions(symbol_id, day_of_week) "
        "WHERE effective_to IS NULL"
    ),
    """
    CREATE TABLE data_session_elements (
        element_id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        day_from INTEGER NOT NULL,
        time_from INTEGER NOT NULL,
        day_to INTEGER NOT NULL,
        time_to INTEGER NOT NULL,
        eod INTEGER NOT NULL CHECK (eod IN (0, 1))
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX idx_data_session_elements_session "
        "ON data_session_elements(session_id, day_from)"
    ),
    """
    CREATE TABLE data_market_series (
        series_id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_data_id INTEGER DEFAULT 0,
        connection TEXT NOT NULL,
        symbol TEXT NOT NULL,
        instrument TEXT NOT NULL,
        timeframe TEXT,
        timezone TEXT,
        filename TEXT,
        date_from INTEGER,
        date_to INTEGER,
        data_type INTEGER,
        row_count INTEGER DEFAULT 0,
        decimals INTEGER,
        source INTEGER,
        seconds_records INTEGER DEFAULT 0,
        usymbol TEXT,
        usymbol_name TEXT,
        remove_weekends INTEGER DEFAULT 0 CHECK (remove_weekends IN (0, 1)),
        show INTEGER DEFAULT 1 CHECK (show IN (0, 1)),
        basket_id INTEGER DEFAULT -1,
        broker_id INTEGER DEFAULT -1,
        request_id TEXT NOT NULL DEFAULT '',
        correlation_id TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
        updated_at TEXT
    ) STRICT
    """.strip(),
    (
        "CREATE INDEX idx_data_market_series_lookup "
        "ON data_market_series(instrument, timeframe, date_from)"
    ),
    """
    CREATE TABLE data_broker_stocks (
        broker_stock_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        broker_id INTEGER NOT NULL
    ) STRICT
    """.strip(),
    "CREATE INDEX idx_data_broker_stocks_broker ON data_broker_stocks(broker_id)",
    """
    CREATE TABLE data_stock_groups (
        group_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        is_system INTEGER NOT NULL CHECK (is_system IN (0, 1)),
        description TEXT
    ) STRICT
    """.strip(),
    """
    CREATE TABLE data_stock_members (
        member_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        basket_id INTEGER NOT NULL,
        date_from INTEGER NOT NULL,
        date_to INTEGER
    ) STRICT
    """.strip(),
    "CREATE INDEX idx_data_stock_members_basket ON data_stock_members(basket_id)",
)


def _checksum() -> str:
    """Return the immutable statement checksum.

    Returns:
        The SHA-256 digest over the ordered migration statements.
    """
    return hashlib.sha256("\n-- statement --\n".join(_STATEMENTS).encode()).hexdigest()


MARKET_REFERENCE_MIGRATION_STEP = MigrationStep(
    domain="data",
    migration_id="011_market_reference_v1",
    checksum=_checksum(),
    statements=_STATEMENTS,
)

__all__ = ("MARKET_REFERENCE_MIGRATION_STEP",)
