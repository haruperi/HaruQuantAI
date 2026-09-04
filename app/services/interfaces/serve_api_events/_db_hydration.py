"""Database hydration and schema initialization for D-IFACE.

Ensures that 'watchlist', 'watchlist_items', 'instruments', 'trading_sessions',
'data_series', 'data_brokers', and 'data_bars' tables exist in
data/database/haruquantai.db and are seeded with initial data from
data/database/haruquant-dev.db when available.

Bar history is hydrated from the reference database's persisted market-data
cache: for every (symbol, timeframe) pair the dataset with the latest end
timestamp is retained. These are genuine broker-fetched records; no bars are
ever generated or interpolated here.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

logger = logging.getLogger(__name__)

_DEFAULT_PROD_DB: Final[Path] = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "data"
    / "database"
    / "haruquantai.db"
)
_DEFAULT_DEV_DB: Final[Path] = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "data"
    / "database"
    / "haruquant-dev.db"
)

_INSTRUMENTS_COLS: Final[int] = 34
_SESSIONS_COLS: Final[int] = 32

_WATCHLIST_INSERT: Final[str] = (
    "INSERT OR IGNORE INTO watchlist VALUES (?, ?, ?, ?, ?, ?, ?)"
)
_WATCHLIST_ITEMS_INSERT: Final[str] = (
    "INSERT OR IGNORE INTO watchlist_items VALUES (?, ?, ?, ?, ?, ?)"
)
_INSTRUMENTS_INSERT: Final[str] = (
    "INSERT OR IGNORE INTO instruments VALUES ("
    "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
    "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?"
    ")"
)
_SESSIONS_INSERT: Final[str] = (
    "INSERT OR IGNORE INTO trading_sessions VALUES ("
    "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
    "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?"
    ")"
)


def _create_tables(prod_cur: sqlite3.Cursor) -> None:
    """Create core tables if they do not exist.

    Args:
        prod_cur: Cursor on the production database connection.
    """
    prod_cur.execute(
        """
        CREATE TABLE IF NOT EXISTS watchlist (
            watchlist_id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL,
            name TEXT NOT NULL CHECK (name <> ''),
            is_default INTEGER NOT NULL CHECK (is_default IN (0, 1)),
            sort_order INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE (account_id, name)
        )
        """
    )

    prod_cur.execute(
        """
        CREATE TABLE IF NOT EXISTS watchlist_items (
            watchlist_id TEXT NOT NULL,
            source_id TEXT NOT NULL,
            symbol TEXT NOT NULL CHECK (symbol <> ''),
            sort_order INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            asset_class TEXT NOT NULL DEFAULT '',
            PRIMARY KEY (watchlist_id, source_id, symbol)
        )
        """
    )

    prod_cur.execute(
        """
        CREATE TABLE IF NOT EXISTS instruments (
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
        )
        """
    )

    prod_cur.execute(
        """
        CREATE TABLE IF NOT EXISTS trading_sessions (
            session_id TEXT PRIMARY KEY,
            principal_id TEXT NOT NULL,
            environment_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            mode TEXT NOT NULL CHECK(mode IN ('sim','demo','live')),
            provider TEXT NOT NULL,
            provider_account_ref TEXT,
            credential_ref TEXT,
            simulation_session_id TEXT,
            dataset_ref TEXT,
            dataset_revision TEXT,
            dataset_hash TEXT,
            lifecycle_state TEXT NOT NULL,
            recovery_state TEXT NOT NULL,
            is_default INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 0,
            auto_start INTEGER NOT NULL DEFAULT 1,
            metadata_json TEXT NOT NULL,
            last_error_code TEXT,
            last_reconciled_at TEXT,
            started_at TEXT,
            stopped_at TEXT,
            archived_at TEXT,
            version INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            sim_initial_balance_decimal TEXT,
            sim_leverage INTEGER,
            sim_account_currency TEXT,
            sim_sequence INTEGER,
            simulation_runtime_ref TEXT
        )
        """
    )

    prod_cur.execute(
        """
        CREATE TABLE IF NOT EXISTS data_series (
            series_id INTEGER PRIMARY KEY,
            source_data_id INTEGER,
            connection TEXT,
            symbol TEXT NOT NULL,
            instrument TEXT,
            timeframe TEXT,
            timezone TEXT,
            filename TEXT,
            date_from INTEGER,
            date_to INTEGER,
            data_type INTEGER,
            row_count INTEGER,
            decimals INTEGER,
            source INTEGER,
            seconds_records INTEGER,
            usymbol TEXT,
            usymbol_name TEXT,
            remove_weekends INTEGER,
            show INTEGER,
            basket_id INTEGER,
            broker_id INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    prod_cur.execute(
        """
        CREATE TABLE IF NOT EXISTS data_brokers (
            broker_id INTEGER PRIMARY KEY,
            provider_id TEXT NOT NULL,
            name TEXT,
            description TEXT,
            postfix TEXT,
            mt_timezone TEXT,
            mt_use INTEGER DEFAULT 1,
            is_system INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    prod_cur.execute(
        """
        CREATE TABLE IF NOT EXISTS data_bars (
            symbol TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            records_json TEXT NOT NULL,
            start TEXT,
            end TEXT,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (symbol, timeframe)
        )
        """
    )


def _hydrate_series(prod_cur: sqlite3.Cursor, dev_cur: sqlite3.Cursor) -> int:
    """Copy the market-data series reference catalogue from the dev database.

    Args:
        prod_cur: Cursor on the target production database.
        dev_cur: Cursor on the reference development database.

    Returns:
        Number of series rows hydrated.
    """
    prod_cur.execute("SELECT count(*) FROM data_series")
    if prod_cur.fetchone()[0] > 0:
        return 0
    rows = dev_cur.execute(
        """
        SELECT
            series_id, source_data_id, connection, symbol, instrument,
            timeframe, timezone, filename, date_from, date_to, data_type,
            row_count, decimals, source, seconds_records, usymbol,
            usymbol_name, remove_weekends, show, basket_id, broker_id,
            created_at, updated_at
        FROM data_market_series
        """
    ).fetchall()
    prod_cur.executemany(
        "INSERT OR IGNORE INTO data_series VALUES ("
        "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?"
        ")",
        rows,
    )
    return len(rows)


def _hydrate_brokers(prod_cur: sqlite3.Cursor, dev_cur: sqlite3.Cursor) -> int:
    """Copy broker profiles from the dev database.

    Args:
        prod_cur: Cursor on the target production database.
        dev_cur: Cursor on the reference development database.

    Returns:
        Number of broker rows hydrated.
    """
    prod_cur.execute("SELECT count(*) FROM data_brokers")
    if prod_cur.fetchone()[0] > 0:
        return 0
    rows = dev_cur.execute(
        """
        SELECT
            broker_id, provider_id, name, description, postfix, mt_timezone,
            mt_use, is_system, created_at, updated_at
        FROM data_brokers
        """
    ).fetchall()
    prod_cur.executemany(
        "INSERT OR IGNORE INTO data_brokers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    return len(rows)


def _hydrate_bars(prod_cur: sqlite3.Cursor, dev_cur: sqlite3.Cursor) -> int:
    """Persist the best cached bar dataset per (symbol, timeframe) pair.

    Only ``data_kind = 'bars'`` datasets carrying real records are
    considered; for each pair the dataset whose end timestamp is latest wins,
    so repeated hydration converges on one authoritative history per pair.

    Args:
        prod_cur: Cursor on the target production database.
        dev_cur: Cursor on the reference development database.

    Returns:
        Number of (symbol, timeframe) pairs hydrated.
    """
    prod_cur.execute("SELECT count(*) FROM data_bars")
    if prod_cur.fetchone()[0] > 0:
        return 0
    best: dict[tuple[str, str], dict[str, Any]] = {}
    for (payload,) in dev_cur.execute("SELECT dataset_json FROM data_cache").fetchall():
        try:
            dataset = json.loads(str(payload))
        except TypeError, ValueError:
            continue
        if dataset.get("data_kind") != "bars":
            continue
        records = dataset.get("records") or []
        if not records:
            continue
        symbol = str(dataset.get("symbol") or "")
        timeframe = str(dataset.get("timeframe") or "")
        if not symbol or not timeframe:
            continue
        end = str(dataset.get("end") or "")
        current = best.get((symbol, timeframe))
        if current is None or end > current["end"]:
            best[(symbol, timeframe)] = {
                "records": records,
                "start": dataset.get("start"),
                "end": end,
            }
    hydrated = 0
    for (symbol, timeframe), entry in sorted(best.items()):
        prod_cur.execute(
            """
            INSERT OR IGNORE INTO data_bars
                (symbol, timeframe, records_json, start, end, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                symbol,
                timeframe,
                json.dumps(entry["records"]),
                entry["start"],
                entry["end"],
                _utc_now_iso(),
            ),
        )
        hydrated += 1
    return hydrated


def _utc_now_iso() -> str:
    """Return the current UTC instant as a truncated ISO-8601 string."""
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _seed_from_dev(prod_cur: sqlite3.Cursor, dev_cur: sqlite3.Cursor) -> None:
    """Seed instruments, watchlists, and sessions from development database.

    Args:
        prod_cur: Cursor on the target production database.
        dev_cur: Cursor on the reference development database.
    """
    # Seed instruments
    prod_cur.execute("SELECT count(*) FROM instruments")
    if prod_cur.fetchone()[0] == 0:
        inst = dev_cur.execute("SELECT * FROM data_instruments").fetchall()
        if inst and len(inst[0]) == _INSTRUMENTS_COLS:
            prod_cur.executemany(_INSTRUMENTS_INSERT, inst)
            logger.info("Seeded %d instruments from reference DB", len(inst))

    # Seed watchlists
    prod_cur.execute("SELECT count(*) FROM watchlist")
    if prod_cur.fetchone()[0] == 0:
        wls = dev_cur.execute("SELECT * FROM api_watchlists").fetchall()
        if wls:
            prod_cur.executemany(_WATCHLIST_INSERT, wls)
        items = dev_cur.execute(
            """
            SELECT
                watchlist_id, source_id, symbol, sort_order,
                created_at, asset_class
            FROM api_watchlist_items
            """
        ).fetchall()
        if items:
            prod_cur.executemany(_WATCHLIST_ITEMS_INSERT, items)
        logger.info(
            "Seeded %d watchlists and %d items from reference DB",
            len(wls),
            len(items),
        )

    # Seed trading sessions
    prod_cur.execute("SELECT count(*) FROM trading_sessions")
    if prod_cur.fetchone()[0] == 0:
        sessions = dev_cur.execute("SELECT * FROM trading_sessions").fetchall()
        if sessions and len(sessions[0]) == _SESSIONS_COLS:
            prod_cur.executemany(_SESSIONS_INSERT, sessions)
            logger.info("Seeded %d sessions from reference DB", len(sessions))

    # Seed the Data reference catalogue (series, brokers, cached bars).
    series_count = _hydrate_series(prod_cur, dev_cur)
    brokers_count = _hydrate_brokers(prod_cur, dev_cur)
    bars_count = _hydrate_bars(prod_cur, dev_cur)
    if series_count or brokers_count or bars_count:
        logger.info(
            "Seeded Data reference: %d series, %d brokers, %d bar histories",
            series_count,
            brokers_count,
            bars_count,
        )


def ensure_database_hydrated(
    prod_path: Path | str | None = None,
    dev_path: Path | str | None = None,
) -> None:
    """Ensure required tables exist in haruquantai.db and seed them if empty.

    Args:
        prod_path: Optional explicit production database path.
        dev_path: Optional explicit development reference database path.
    """
    prod_file = Path(prod_path) if prod_path is not None else _DEFAULT_PROD_DB
    dev_file = Path(dev_path) if dev_path is not None else _DEFAULT_DEV_DB

    if not prod_file.exists():
        prod_file.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(str(prod_file)) as prod_conn:
        prod_cur = prod_conn.cursor()
        _create_tables(prod_cur)

        if dev_file.exists():
            try:
                with sqlite3.connect(str(dev_file)) as dev_conn:
                    dev_cur = dev_conn.cursor()
                    _seed_from_dev(prod_cur, dev_cur)
            except sqlite3.Error as err:
                logger.warning("Optional database seeding from dev DB skipped: %s", err)

        prod_conn.commit()
