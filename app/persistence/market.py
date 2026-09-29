"""Host-owned market-file catalog; schema creation is explicit and isolated."""

from __future__ import annotations

import sqlite3
from contextlib import closing, suppress
from datetime import UTC, datetime
from pathlib import Path

from app.host.logging import get_logger

logger = get_logger(__name__)


class MarketSchemaUnavailableError(ValueError):
    """The active database has not received an approved market migration."""


class BrokerSchemaUnavailableError(ValueError):
    """The existing read-only broker catalog is absent or incompatible."""


MAX_BROKER_TEXT = 80
MAX_BROKER_POSTFIX = 64


def read_broker_profiles(path: Path) -> tuple[tuple[int, str, str, str], ...]:
    """Read eligible broker rows without creating or modifying a database."""
    if not path.is_file():
        raise BrokerSchemaUnavailableError("Broker catalog is unavailable")
    try:
        with closing(
            sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
        ) as connection:
            columns = {
                row[1]
                for row in connection.execute("PRAGMA table_info(datamgr_broker)")
            }
            required = {"id", "name", "postfix", "server_timezone", "enabled", "mt_use"}
            if not required.issubset(columns):
                raise BrokerSchemaUnavailableError(
                    "Broker catalog schema is incompatible"
                )
            rows = connection.execute(
                "SELECT id,name,postfix,server_timezone FROM datamgr_broker "
                "WHERE enabled=1 AND mt_use=1 ORDER BY id"
            ).fetchall()
    except sqlite3.DatabaseError as error:
        raise BrokerSchemaUnavailableError("Broker catalog is unreadable") from error
    result: list[tuple[int, str, str, str]] = []
    for broker_id, name, postfix, timezone in rows:
        if (
            not isinstance(broker_id, int)
            or broker_id <= 0
            or not isinstance(name, str)
            or not 1 <= len(name) <= MAX_BROKER_TEXT
            or not (postfix is None or isinstance(postfix, str))
            or not (timezone is None or isinstance(timezone, str))
        ):
            raise BrokerSchemaUnavailableError("Broker catalog row is invalid")
        clean_postfix = postfix or ""
        clean_timezone = timezone or "UTC"
        if (
            len(clean_postfix) > MAX_BROKER_POSTFIX
            or len(clean_timezone) > MAX_BROKER_TEXT
        ):
            raise BrokerSchemaUnavailableError("Broker catalog row is invalid")
        result.append((broker_id, name, clean_postfix, clean_timezone))
    return tuple(result)


SCHEMA = """
CREATE TABLE datamgr_datasets (
  id TEXT PRIMARY KEY,
  source TEXT NOT NULL,
  symbol TEXT NOT NULL,
  underlying TEXT NOT NULL,
  instrument TEXT NOT NULL,
  timeframe TEXT NOT NULL,
  broker TEXT NOT NULL,
  broker_name TEXT NOT NULL,
  timezone TEXT NOT NULL,
  category TEXT NOT NULL,
  date_from TEXT NOT NULL,
  date_to TEXT NOT NULL,
  bars INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE market_files (
  source TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('ticks', 'm1')),
  symbol TEXT NOT NULL,
  period TEXT NOT NULL,
  relative_path TEXT NOT NULL,
  revision INTEGER NOT NULL CHECK (revision > 0),
  sha256 TEXT NOT NULL,
  byte_size INTEGER NOT NULL CHECK (byte_size >= 0),
  row_count INTEGER NOT NULL CHECK (row_count > 0),
  first_ms INTEGER NOT NULL,
  last_ms INTEGER NOT NULL,
  coverage_json TEXT NOT NULL,
  provider_mode TEXT NOT NULL,
  committed_at TEXT NOT NULL,
  PRIMARY KEY (source, kind, symbol, period)
);
CREATE TABLE market_ingestions (
  request_id TEXT PRIMARY KEY,
  owner TEXT NOT NULL,
  source TEXT NOT NULL,
  symbol TEXT NOT NULL,
  kind TEXT NOT NULL,
  mode TEXT NOT NULL,
  state TEXT NOT NULL,
  reason TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
"""


def create_isolated_schema(path: Path) -> None:
    """Create a fresh test/research store; refuse to alter an existing database."""
    if path.exists():
        raise FileExistsError("Market schema creation requires a new database")
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as connection:
        connection.executescript(SCHEMA)
    logger.info("Created isolated market schema at %s", path)


DATASET_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS datamgr_datasets (
  id TEXT PRIMARY KEY,
  source TEXT NOT NULL,
  symbol TEXT NOT NULL,
  underlying TEXT NOT NULL,
  instrument TEXT NOT NULL,
  timeframe TEXT NOT NULL,
  broker TEXT NOT NULL,
  broker_name TEXT NOT NULL,
  timezone TEXT NOT NULL,
  category TEXT NOT NULL,
  date_from TEXT NOT NULL,
  date_to TEXT NOT NULL,
  bars INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
"""

MARKET_TABLES_SCHEMA = """
CREATE TABLE IF NOT EXISTS market_files (
  source TEXT NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('ticks', 'm1')),
  symbol TEXT NOT NULL,
  period TEXT NOT NULL,
  relative_path TEXT NOT NULL,
  revision INTEGER NOT NULL CHECK (revision > 0),
  sha256 TEXT NOT NULL,
  byte_size INTEGER NOT NULL CHECK (byte_size >= 0),
  row_count INTEGER NOT NULL CHECK (row_count > 0),
  first_ms INTEGER NOT NULL,
  last_ms INTEGER NOT NULL,
  coverage_json TEXT NOT NULL,
  provider_mode TEXT NOT NULL,
  committed_at TEXT NOT NULL,
  PRIMARY KEY (source, kind, symbol, period)
);
CREATE TABLE IF NOT EXISTS market_ingestions (
  request_id TEXT PRIMARY KEY,
  owner TEXT NOT NULL,
  source TEXT NOT NULL,
  symbol TEXT NOT NULL,
  kind TEXT NOT NULL,
  mode TEXT NOT NULL,
  state TEXT NOT NULL,
  reason TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
"""


def migrate_market_schema(path: Path) -> Path | None:
    """Back up an authorized existing store and provision market catalog tables.

    Args:
        path: Path to existing SQLite database approved for migration.

    Returns:
        Path to the verified backup file created before migration, or None if already
        provisioned.
    """
    if not path.is_file():
        raise MarketSchemaUnavailableError("Market catalog database is unavailable")

    with closing(sqlite3.connect(path)) as connection:
        names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if {"datamgr_datasets", "market_files", "market_ingestions"}.issubset(names):
            return None

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    backup_path = path.parent / f"{path.stem}_backup_{timestamp}.db"
    with (
        closing(sqlite3.connect(path)) as src,
        closing(sqlite3.connect(backup_path)) as dst,
    ):
        src.backup(dst)

    with closing(sqlite3.connect(path)) as connection:
        connection.executescript(DATASET_TABLE_SCHEMA)
        connection.executescript(MARKET_TABLES_SCHEMA)

    logger.info("Migrated market catalog schema for %s (backup=%s)", path, backup_path)
    return backup_path


def open_market_catalog(path: Path) -> sqlite3.Connection:
    """Open only an already provisioned compatible catalog, without migration."""
    if not path.is_file():
        raise MarketSchemaUnavailableError("Market catalog is unavailable")
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        required_tables = {"datamgr_datasets", "market_files", "market_ingestions"}
        if not required_tables.issubset(names):
            raise MarketSchemaUnavailableError("Market catalog migration is required")  # noqa: TRY301
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(market_files)")
        }
        required = {
            "source",
            "kind",
            "symbol",
            "period",
            "relative_path",
            "revision",
            "sha256",
            "byte_size",
            "row_count",
            "first_ms",
            "last_ms",
            "coverage_json",
            "provider_mode",
            "committed_at",
        }
        if not required.issubset(columns):
            raise MarketSchemaUnavailableError("Market catalog schema is incompatible")  # noqa: TRY301
        return connection
    except BaseException:
        connection.close()
        raise


def open_definition_catalog(path: Path) -> sqlite3.Connection:
    """Open existing definition storage without requiring price-file tables."""
    try:
        connection = sqlite3.connect(path.resolve().as_uri() + "?mode=rw", uri=True)
    except sqlite3.Error as error:
        raise MarketSchemaUnavailableError("Dataset catalog is unavailable") from error
    connection.row_factory = sqlite3.Row
    required = {
        "id",
        "source",
        "symbol",
        "underlying",
        "instrument",
        "timeframe",
        "broker",
        "broker_name",
        "timezone",
        "category",
        "date_from",
        "date_to",
        "bars",
        "created_at",
        "updated_at",
    }
    try:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(datamgr_datasets)")
        }
        if not required.issubset(columns):
            raise MarketSchemaUnavailableError("Dataset catalog schema is incompatible")  # noqa: TRY301 -- close on failed validation.
        return connection
    except BaseException:
        connection.close()
        raise


def preseed_native_sqx_datasets(
    database_path: Path, source_csv: Path | None = None
) -> int:
    """Pre-seed native SQX Build 144 symbol records into datamgr_datasets."""
    if source_csv is None:
        source_csv = database_path.parents[1] / "market" / "dukascopy" / "dukascopy.csv"
    if not source_csv.is_file():
        return 0

    from uuid import uuid4

    now_iso = datetime.now(UTC).isoformat()
    inserted = 0

    with source_csv.open("r", encoding="latin-1") as stream:
        lines = [line.strip() for line in stream if line.strip()]

    with closing(sqlite3.connect(database_path)) as connection, connection:
        existing = {
            str(row[0]).lower()
            for row in connection.execute("SELECT symbol FROM datamgr_datasets")
        }
        min_csv_parts = 4
        for line in lines:
            parts = [p.strip() for p in line.split(";")]
            if len(parts) < min_csv_parts:
                continue
            symbol = parts[0]
            category = parts[2]
            ds_symbol = f"{symbol}_dukascopy"
            if ds_symbol.lower() in existing:
                continue
            ds_id = uuid4().hex
            cursor = connection.execute(
                "INSERT OR IGNORE INTO datamgr_datasets ("
                "id, source, symbol, underlying, instrument, timeframe, "
                "broker, broker_name, timezone, category, date_from, date_to, "
                "bars, created_at, updated_at"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    ds_id,
                    "Dukascopy",
                    ds_symbol,
                    symbol,
                    symbol,
                    "M1",
                    "3",
                    "Dukascopy",
                    "UTC",
                    category,
                    "",
                    "",
                    0,
                    now_iso,
                    now_iso,
                ),
            )
            if cursor.rowcount > 0:
                inserted += 1
                existing.add(ds_symbol.lower())
    logger.info(
        "Pre-seeded native SQX datasets at %s (inserted=%d)",
        database_path,
        inserted,
    )
    return inserted


def delete_market_symbol(database_path: Path, data_root: Path, symbol: str) -> bool:
    """Purge physical parquet files and delete dataset definition."""
    clean_sym = symbol.strip()
    underlying = clean_sym.removesuffix("_dukascopy").lower()
    sym_lower = clean_sym.lower()

    with closing(sqlite3.connect(database_path)) as connection, connection:
        # Check if dataset exists
        cursor = connection.execute(
            "SELECT id, symbol, underlying FROM datamgr_datasets "
            "WHERE lower(symbol)=? OR lower(underlying)=?",
            (sym_lower, underlying),
        )
        matched = cursor.fetchall()
        if not matched:
            return False

        # Gather any market files to remove
        file_cursor = connection.execute(
            "SELECT relative_path FROM market_files "
            "WHERE lower(symbol)=? OR lower(symbol)=?",
            (sym_lower, underlying),
        )
        file_paths = [row[0] for row in file_cursor.fetchall()]
        for rel_path in file_paths:
            full_path = data_root / rel_path
            if full_path.is_file():
                with suppress(OSError):
                    full_path.unlink()

        # Purge records
        connection.execute(
            "DELETE FROM market_files WHERE lower(symbol)=? OR lower(symbol)=?",
            (sym_lower, underlying),
        )
        connection.execute(
            "DELETE FROM market_ingestions WHERE lower(symbol)=? OR lower(symbol)=?",
            (sym_lower, underlying),
        )
        connection.execute(
            "DELETE FROM datamgr_datasets WHERE lower(symbol)=? OR lower(underlying)=?",
            (sym_lower, underlying),
        )
    logger.info(
        "Deleted market symbol %s from %s (files_removed=%d)",
        symbol,
        database_path,
        len(file_paths),
    )
    return True


def clear_market_symbol(database_path: Path, data_root: Path, symbol: str) -> bool:
    """Purge physical market files and reset dataset coverage, retaining definition."""
    clean_sym = symbol.strip()
    underlying = clean_sym.removesuffix("_dukascopy").lower()
    sym_lower = clean_sym.lower()
    now_iso = datetime.now(UTC).isoformat()

    with closing(sqlite3.connect(database_path)) as connection, connection:
        # Check if dataset exists
        cursor = connection.execute(
            "SELECT id, symbol, underlying FROM datamgr_datasets "
            "WHERE lower(symbol)=? OR lower(underlying)=?",
            (sym_lower, underlying),
        )
        matched = cursor.fetchall()
        if not matched:
            return False

        # Gather any market files to remove
        file_cursor = connection.execute(
            "SELECT relative_path FROM market_files "
            "WHERE lower(symbol)=? OR lower(symbol)=?",
            (sym_lower, underlying),
        )
        file_paths = [row[0] for row in file_cursor.fetchall()]
        for rel_path in file_paths:
            full_path = data_root / rel_path
            if full_path.is_file():
                with suppress(OSError):
                    full_path.unlink()

        # Purge file records and reset dataset coverage
        connection.execute(
            "DELETE FROM market_files WHERE lower(symbol)=? OR lower(symbol)=?",
            (sym_lower, underlying),
        )
        connection.execute(
            "DELETE FROM market_ingestions WHERE lower(symbol)=? OR lower(symbol)=?",
            (sym_lower, underlying),
        )
        connection.execute(
            "UPDATE datamgr_datasets "
            "SET date_from='', date_to='', bars=0, updated_at=? "
            "WHERE lower(symbol)=? OR lower(underlying)=?",
            (now_iso, sym_lower, underlying),
        )
    logger.info(
        "Cleared market symbol %s from %s (files_removed=%d)",
        symbol,
        database_path,
        len(file_paths),
    )
    return True


def log_datamgr_operation(
    database_path: Path,
    symbol: str,
    operation: str,
    status: str,
    message: str,
) -> None:
    """Log an operational event in the datamgr_operation_log table."""
    now_iso = datetime.now(UTC).isoformat()
    with closing(sqlite3.connect(database_path)) as connection, connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS datamgr_operation_log ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "timestamp_utc TEXT NOT NULL, "
            "symbol TEXT NOT NULL, "
            "operation TEXT NOT NULL, "
            "status TEXT NOT NULL, "
            "message TEXT NOT NULL"
            ")"
        )
        connection.execute(
            "INSERT INTO datamgr_operation_log "
            "(timestamp_utc, symbol, operation, status, message) "
            "VALUES (?, ?, ?, ?, ?)",
            (now_iso, symbol, operation, status, message),
        )
    logger.info(
        "Data Manager DB audit log: operation=%s, symbol=%s, status=%s, message=%s",
        operation,
        symbol,
        status,
        message,
    )


def read_datamgr_log(database_path: Path) -> list[dict[str, str]]:
    """Read all entries from the datamgr_operation_log table."""
    with closing(sqlite3.connect(database_path)) as connection:
        cursor = connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='datamgr_operation_log'"
        )
        if not cursor.fetchone():
            return []
        rows = connection.execute(
            "SELECT timestamp_utc, symbol, operation, status, message "
            "FROM datamgr_operation_log ORDER BY id ASC"
        ).fetchall()
    return [
        {
            "timestamp": row[0],
            "symbol": row[1],
            "operation": row[2],
            "status": row[3],
            "message": row[4],
        }
        for row in rows
    ]


def clear_datamgr_log(database_path: Path) -> int:
    """Clear all operational log entries."""
    with closing(sqlite3.connect(database_path)) as connection, connection:
        cursor = connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='datamgr_operation_log'"
        )
        if not cursor.fetchone():
            return 0
        return connection.execute("DELETE FROM datamgr_operation_log").rowcount
