"""Database hydration and schema initialization for D-IFACE.

Ensures that 'watchlist', 'watchlist_items', 'instruments', 'trading_sessions',
'data', and 'data_bars' tables exist in
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
_PROFILES_INSERT: Final[str] = (
    "INSERT OR IGNORE INTO trading_profiles VALUES ("
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
            name VARCHAR(64) PRIMARY KEY,
            description VARCHAR(255),
            path VARCHAR(255),
            category VARCHAR(64),
            exchange VARCHAR(64),
            bank VARCHAR(64),
            isin VARCHAR(32),
            basis VARCHAR(64),
            formula VARCHAR(255),
            page VARCHAR(255),
            currency_base VARCHAR(16),
            currency_profit VARCHAR(16),
            currency_margin VARCHAR(16),
            custom BOOLEAN DEFAULT FALSE,
            chart_mode INTEGER,
            select_mode BOOLEAN,
            visible BOOLEAN,
            time BIGINT,
            digits INTEGER,
            point DOUBLE PRECISION,
            spread INTEGER,
            spread_float BOOLEAN,
            ticks_bookdepth INTEGER,
            bid DOUBLE PRECISION,
            bidhigh DOUBLE PRECISION,
            bidlow DOUBLE PRECISION,
            ask DOUBLE PRECISION,
            askhigh DOUBLE PRECISION,
            asklow DOUBLE PRECISION,
            last DOUBLE PRECISION,
            lasthigh DOUBLE PRECISION,
            lastlow DOUBLE PRECISION,
            volume BIGINT,
            volumehigh BIGINT,
            volumelow BIGINT,
            volume_real DOUBLE PRECISION,
            volumehigh_real DOUBLE PRECISION,
            volumelow_real DOUBLE PRECISION,
            trade_calc_mode INTEGER,
            trade_mode INTEGER,
            trade_exemode INTEGER,
            trade_stops_level INTEGER,
            trade_freeze_level INTEGER,
            trade_contract_size DOUBLE PRECISION,
            trade_tick_size DOUBLE PRECISION,
            trade_tick_value DOUBLE PRECISION,
            trade_tick_value_profit DOUBLE PRECISION,
            trade_tick_value_loss DOUBLE PRECISION,
            trade_accrued_interest DOUBLE PRECISION,
            trade_face_value DOUBLE PRECISION,
            trade_liquidity_rate DOUBLE PRECISION,
            volume_min DOUBLE PRECISION,
            volume_max DOUBLE PRECISION,
            volume_step DOUBLE PRECISION,
            volume_limit DOUBLE PRECISION,
            order_mode INTEGER,
            order_gtc_mode INTEGER,
            filling_mode INTEGER,
            expiration_mode INTEGER,
            start_time BIGINT,
            expiration_time BIGINT,
            swap_mode INTEGER,
            swap_rollover3days INTEGER,
            swap_long DOUBLE PRECISION,
            swap_short DOUBLE PRECISION,
            margin_initial DOUBLE PRECISION,
            margin_maintenance DOUBLE PRECISION,
            margin_hedged DOUBLE PRECISION,
            margin_hedged_use_leg BOOLEAN,
            session_deals INTEGER,
            session_buy_orders INTEGER,
            session_sell_orders INTEGER,
            session_volume DOUBLE PRECISION,
            session_turnover DOUBLE PRECISION,
            session_interest DOUBLE PRECISION,
            session_buy_orders_volume DOUBLE PRECISION,
            session_sell_orders_volume DOUBLE PRECISION,
            session_open DOUBLE PRECISION,
            session_close DOUBLE PRECISION,
            session_aw DOUBLE PRECISION,
            session_price_settlement DOUBLE PRECISION,
            session_price_limit_min DOUBLE PRECISION,
            session_price_limit_max DOUBLE PRECISION,
            option_mode INTEGER,
            option_right INTEGER,
            option_strike DOUBLE PRECISION,
            price_change DOUBLE PRECISION,
            price_volatility DOUBLE PRECISION,
            price_theoretical DOUBLE PRECISION,
            price_sensitivity DOUBLE PRECISION,
            price_greeks_delta DOUBLE PRECISION,
            price_greeks_theta DOUBLE PRECISION,
            price_greeks_gamma DOUBLE PRECISION,
            price_greeks_vega DOUBLE PRECISION,
            price_greeks_rho DOUBLE PRECISION,
            price_greeks_omega DOUBLE PRECISION
        )
        """
    )

    prod_cur.execute(
        """
        CREATE TABLE IF NOT EXISTS trading_profiles (
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
        CREATE TABLE IF NOT EXISTS user_sessions (
            session_digest TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            csrf_digest TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            revoked_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
        """
    )

    prod_cur.execute(
        """
        CREATE TABLE IF NOT EXISTS market_sessions (
            name VARCHAR(64) PRIMARY KEY,
            display_name VARCHAR(128) NOT NULL,
            asset_class VARCHAR(32) NOT NULL,
            timezone VARCHAR(64) NOT NULL,
            open_time TIME NOT NULL,
            close_time TIME NOT NULL,
            days_open VARCHAR(32) NOT NULL DEFAULT 'Mon-Fri',
            break_start TIME,
            break_end TIME,
            is_24_7 BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            description VARCHAR(255)
        )
        """
    )

    prod_cur.execute(
        """
        CREATE TABLE IF NOT EXISTS data (
            id INTEGER PRIMARY KEY,
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
    prod_cur.execute("SELECT count(*) FROM data")
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
        "INSERT OR IGNORE INTO data VALUES ("
        "?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?"
        ")",
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

    # Seed trading profiles
    prod_cur.execute("SELECT count(*) FROM trading_profiles")
    if prod_cur.fetchone()[0] == 0:
        sessions = dev_cur.execute("SELECT * FROM trading_sessions").fetchall()
        if sessions and len(sessions[0]) == _SESSIONS_COLS:
            prod_cur.executemany(_PROFILES_INSERT, sessions)
            logger.info("Seeded %d profiles from reference DB", len(sessions))

    # Seed the Data reference catalogue (series, cached bars).
    series_count = _hydrate_series(prod_cur, dev_cur)
    bars_count = _hydrate_bars(prod_cur, dev_cur)
    if series_count or bars_count:
        logger.info(
            "Seeded Data reference: %d series, %d bar histories",
            series_count,
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
