"""Market Data Storage Facade, Catalog Persistence, and Dataset Operations.

Description:
    Provides the central storage facade, metadata cataloging, and physical
    Parquet file management for historical market data within HaruQuantAI.

    External relations and workflows:
    - Host capabilities: Injected into workspace plugins via MarketAccess
      (app.host.capabilities.MarketAccess) to query broker profiles, list
      registered datasets, stream ticks/bars, and ingest downloaded history.
    - Workspace DataManager: Backs DataManager action endpoints for symbol
      creation, parquet file discovery, dataset clearing/deletion, and
      audit operation logging (`datamgr_log`).
    - Ingestion plugins: Used by DataSource plugins (e.g. Dukascopy acquisition)
      to stream-append downloaded tick records or resampled M1 bars into
      canonical partition files and register dataset catalog definitions.

    Internal coordination:
    - MarketDataStore: High-performance typed facade executing atomic multi-file
      parquet ingestion, deduplication, streaming batch reading, and physical
      cleanup.
    - Catalog management: Schema migration, table creation (`datamgr_symbols`,
      `datamgr_datasets`, `datamgr_log`), and catalog connection validators.
    - Parquet integration: Integrates with `app.persistence.market_files` for
      strict PyArrow schemas, partition paths, and file integrity digests.

Purpose:
    FEAT-PERSIST-MARKET: Unified market data persistence, catalog management,
    parquet partition ingestion, and dataset operational lifecycle.

Key Capabilities:
    - FR-PERSIST-MARKET-SCHEMA: Initializes isolated SQLite schema or safely
      migrates existing database tables for dataset registries and audit logs
      via create_isolated_schema() and migrate_market_schema().
      * Verified via: logger.info("Created isolated market schema at %s")
    - FR-PERSIST-MARKET-STORE: Manages multi-threaded physical parquet ingestion,
      streaming partition reads, and atomic partition commits via
      MarketDataStore.
      * Verified via: logger.info("MarketDataStore committed revision %d...")
    - FR-PERSIST-MARKET-CATALOG: Manages dataset registry records, broker
      profile lookups, and native SQX symbol seeding via open_market_catalog(),
      read_broker_profiles(), and preseed_native_sqx_datasets().
      * Verified via: logger.info("Pre-seeded native SQX datasets at %s...")
    - FR-PERSIST-MARKET-OPERATIONS: Audits and executes symbol clearing, dataset
      deletion, and physical file purging via delete_market_symbol(),
      clear_market_symbol(), and log_datamgr_operation().
      * Verified via: logger.info("Purged market symbol %s from %s...")

Python API Usage:
    ```python
    from pathlib import Path

    from app.persistence.market import MarketDataStore

    store = MarketDataStore(
        catalog_path=Path("data/database/haruquantai.db"),
        data_root=Path("data"),
    )
    datasets = store.list_datasets()
    ```

CLI Usage:
    ```bash
    # Verified through persistence market test suite:
    uv run python -m pytest tests/persistence/test_market.py
    ```
"""

from __future__ import annotations

import hashlib
import heapq
import json
import re
import shutil
import sqlite3
from collections.abc import Iterator
from contextlib import closing, suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from uuid import uuid4

import pyarrow as pa  # type: ignore[import-untyped]
import pyarrow.parquet as pq  # type: ignore[import-untyped]

from app.host.logging import get_logger
from app.persistence.market_files import (
    BATCH_ROWS,
    M1_SCHEMA,
    MAX_DATASET_LABEL,
    MAX_DEFINITION_BATCH,
    TICK_SCHEMA,
    Kind,
    MarketFile,
    resolve_market_path,
    verify_market_file,
)

logger = get_logger(__name__)

__all__ = [
    "BATCH_ROWS",
    "DATASET_TABLE_SCHEMA",
    "M1_SCHEMA",
    "MARKET_TABLES_SCHEMA",
    "MAX_BROKER_POSTFIX",
    "MAX_BROKER_TEXT",
    "MAX_DATASET_LABEL",
    "MAX_DEFINITION_BATCH",
    "SCHEMA",
    "TICK_SCHEMA",
    "BrokerSchemaUnavailableError",
    "DefinitionRequest",
    "Kind",
    "MarketBroker",
    "MarketDataStore",
    "MarketDataset",
    "MarketFile",
    "MarketSchemaUnavailableError",
    "clear_datamgr_log",
    "clear_market_symbol",
    "create_isolated_schema",
    "delete_market_symbol",
    "log_datamgr_operation",
    "migrate_market_schema",
    "open_definition_catalog",
    "open_market_catalog",
    "preseed_native_sqx_datasets",
    "read_broker_profiles",
    "read_datamgr_log",
    "resolve_market_path",
    "verify_market_file",
]


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
    logger.info("Read %d eligible broker profiles from %s", len(result), path)
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
        cursor = connection.execute(
            "SELECT id, symbol, underlying FROM datamgr_datasets "
            "WHERE lower(symbol)=? OR lower(underlying)=?",
            (sym_lower, underlying),
        )
        matched = cursor.fetchall()
        if not matched:
            return False

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
        cursor = connection.execute(
            "SELECT id, symbol, underlying FROM datamgr_datasets "
            "WHERE lower(symbol)=? OR lower(underlying)=?",
            (sym_lower, underlying),
        )
        matched = cursor.fetchall()
        if not matched:
            return False

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


@dataclass(frozen=True)
class MarketDataset:
    """A registered market definition, separate from downloaded coverage."""

    id: str
    source: str
    symbol: str
    kind: Kind
    instrument: str
    broker: str
    timezone: str


@dataclass(frozen=True)
class MarketBroker:
    """Read-only eligible broker profile from the unified catalog."""

    id: str
    name: str
    postfix: str
    timezone: str


@dataclass(frozen=True)
class DefinitionRequest:
    """One immutable provider identity and its user-facing definition."""

    symbol: str
    kind: Kind
    broker: str = "-1"
    postfix: str = ""
    instrument: str = "-1"


class MarketDataStore:
    """Publish and read validated current files under an injected data root."""

    def __init__(self, data_root: Path, database_path: Path) -> None:
        self.data_root = data_root
        self.database_path = database_path

    def available(self) -> bool:
        """Report whether an approved catalog schema already exists."""
        try:
            connection = open_market_catalog(self.database_path)
        except ValueError:
            return False
        connection.close()
        return True

    def list_brokers(self) -> tuple[MarketBroker, ...]:
        """List eligible profiles independently of market-file migration."""
        return tuple(
            MarketBroker(str(broker_id), name, postfix, timezone)
            for broker_id, name, postfix, timezone in read_broker_profiles(
                self.database_path
            )
        )

    def definitions_available(self) -> bool:
        """Check definition storage independently of acquisition storage."""
        try:
            with closing(open_definition_catalog(self.database_path)):
                return True
        except ValueError, sqlite3.Error:
            return False

    def register_definitions(
        self, requests: tuple[DefinitionRequest, ...]
    ) -> tuple[MarketDataset, ...]:
        """Insert a bounded batch atomically, retaining provider identity."""
        if not 1 <= len(requests) <= MAX_DEFINITION_BATCH:
            raise ValueError("Choose between one and 725 symbols")
        brokers = (
            {row.id: row for row in self.list_brokers()}
            if any(row.broker != "-1" for row in requests)
            else {}
        )
        datasets: list[MarketDataset] = []
        now = datetime.now(UTC).isoformat()
        with (
            closing(open_definition_catalog(self.database_path)) as connection,
            connection,
        ):
            connection.execute("BEGIN IMMEDIATE")
            for request in requests:
                if (
                    not re.fullmatch(r"[A-Z0-9_]{2,40}", request.symbol)
                    or request.kind not in ("ticks", "m1")
                    or not re.fullmatch(r"[A-Za-z0-9_.-]{0,40}", request.postfix)
                    or request.instrument not in ("-1", request.symbol)
                    or (request.broker != "-1" and request.broker not in brokers)
                ):
                    raise ValueError(
                        "Invalid symbol, broker, postfix or instrument mapping"
                    )
                name = request.symbol + request.postfix
                timeframe = "M1" if request.kind == "m1" else "TICK"
                if connection.execute(
                    "SELECT 1 FROM datamgr_datasets WHERE source=? AND symbol=? "
                    "AND timeframe=? AND broker=?",
                    ("Dukascopy", name, timeframe, request.broker),
                ).fetchone():
                    raise ValueError("Dukascopy dataset definition already exists")
                dataset = MarketDataset(
                    uuid4().hex,
                    "dukascopy",
                    request.symbol.lower(),
                    request.kind,
                    request.symbol,
                    request.broker,
                    "UTC",
                )
                connection.execute(
                    "INSERT INTO datamgr_datasets "
                    "(id,source,symbol,underlying,instrument,timeframe,broker,broker_name,"
                    "timezone,category,date_from,date_to,bars,created_at,updated_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        dataset.id,
                        "Dukascopy",
                        name,
                        request.symbol,
                        request.symbol,
                        timeframe,
                        request.broker,
                        "Default"
                        if request.broker == "-1"
                        else brokers[request.broker].name,
                        "UTC",
                        "",
                        "",
                        "",
                        0,
                        now,
                        now,
                    ),
                )
                datasets.append(dataset)
        logger.info("Registered %d dataset definitions", len(datasets))
        return tuple(datasets)

    def register_dataset(
        self,
        *,
        source: str,
        symbol: str,
        kind: Kind,
        instrument: str,
        broker: str = "-1",
        timezone: str = "UTC",
    ) -> MarketDataset:
        """Register a definition in the pre-existing Data Manager table."""
        self.path(source, kind, symbol, "2000" if kind == "m1" else "2000-01")
        if (
            not instrument
            or len(instrument) > MAX_DATASET_LABEL
            or not broker
            or len(broker) > MAX_DATASET_LABEL
        ):
            raise ValueError("Invalid dataset instrument or broker")
        if timezone != "UTC":
            raise ValueError("Canonical Dukascopy datasets must use UTC")
        dataset = MarketDataset(
            uuid4().hex, source, symbol, kind, instrument, broker, timezone
        )
        now = datetime.now(UTC).isoformat()
        timeframe = "M1" if kind == "m1" else "TICK"
        with closing(open_market_catalog(self.database_path)) as connection, connection:
            existing = connection.execute(
                "SELECT id FROM datamgr_datasets WHERE source=? AND symbol=? "
                "AND timeframe=? AND broker=? AND instrument=?",
                ("Dukascopy", symbol.upper(), timeframe, broker, instrument),
            ).fetchone()
            if existing is not None:
                raise ValueError("Dukascopy dataset definition already exists")
            connection.execute(
                "INSERT INTO datamgr_datasets "
                "(id,source,symbol,underlying,instrument,timeframe,broker,broker_name,"
                "timezone,category,date_from,date_to,bars,created_at,updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    dataset.id,
                    "Dukascopy",
                    symbol.upper(),
                    symbol.upper(),
                    instrument,
                    timeframe,
                    broker,
                    "Default" if broker == "-1" else broker,
                    timezone,
                    "Forex",
                    "",
                    "",
                    0,
                    now,
                    now,
                ),
            )
        logger.info(
            "Registered dataset %s/%s (%s, broker=%s)",
            source,
            symbol,
            kind,
            broker,
        )
        return dataset

    def get_dataset(self, dataset_id: str) -> MarketDataset:
        """Resolve a Data Manager ID to a checked Dukascopy source definition."""
        if not re.fullmatch(r"[0-9a-f]{32}", dataset_id):
            raise ValueError("Invalid dataset ID")
        with closing(open_definition_catalog(self.database_path)) as connection:
            row = connection.execute(
                "SELECT id,source,symbol,underlying,instrument,timeframe,"
                "broker,timezone "
                "FROM datamgr_datasets WHERE id=?",
                (dataset_id,),
            ).fetchone()
        if row is None or row["source"] != "Dukascopy":
            raise ValueError("Dukascopy dataset unavailable")
        kind: Kind = "m1" if row["timeframe"] == "M1" else "ticks"
        if row["timeframe"] not in ("M1", "TICK"):
            raise ValueError("Unsupported Dukascopy dataset kind")
        symbol = (row["underlying"] or row["symbol"]).lower()
        self.path("dukascopy", kind, symbol, "2000" if kind == "m1" else "2000-01")
        return MarketDataset(
            row["id"],
            "dukascopy",
            symbol,
            kind,
            row["instrument"],
            row["broker"],
            row["timezone"],
        )

    def list_datasets(self, source: str) -> tuple[dict[str, Any], ...]:
        """List definitions with coverage from committed files only."""
        if source != "dukascopy":
            raise ValueError("Unsupported market source")
        with closing(open_definition_catalog(self.database_path)) as connection:
            rows = connection.execute(
                "SELECT id,symbol,underlying,instrument,timeframe,broker,broker_name,"
                "timezone,category "
                "FROM datamgr_datasets WHERE source=? ORDER BY symbol,id",
                ("Dukascopy",),
            ).fetchall()
        file_stats: dict[tuple[str, str], tuple[int | None, int | None, int]] = {}
        if self.available():
            with closing(open_market_catalog(self.database_path)) as m_conn:
                f_rows = m_conn.execute(
                    "SELECT kind, lower(symbol), min(first_ms), max(last_ms), "
                    "sum(row_count) FROM market_files WHERE source=? "
                    "GROUP BY kind, lower(symbol)",
                    (source,),
                ).fetchall()
                for f_kind, f_sym, f_first, f_last, f_bars in f_rows:
                    file_stats[(f_kind, f_sym)] = (f_first, f_last, f_bars or 0)
        result: list[dict[str, Any]] = []
        for row in rows:
            kind: Kind = "m1" if row["timeframe"] == "M1" else "ticks"
            if row["timeframe"] not in ("M1", "TICK"):
                continue
            sym_key = (kind, (row["underlying"] or row["symbol"]).lower())
            stat = file_stats.get(sym_key)
            first = stat[0] if stat else None
            last = stat[1] if stat else None
            bars = stat[2] if stat else 0
            result.append(
                {
                    "id": row["id"],
                    "symbol": row["symbol"],
                    "source": "Dukascopy",
                    "underlying": row["underlying"] or row["symbol"],
                    "instrument": row["instrument"],
                    "timeframe": row["timeframe"],
                    "broker": row["broker"],
                    "brokerName": row["broker_name"],
                    "timezone": row["timezone"],
                    "category": row["category"],
                    "from": datetime.fromtimestamp(first / 1000, tz=UTC)
                    .date()
                    .isoformat()
                    if first is not None
                    else "",
                    "to": datetime.fromtimestamp(last / 1000, tz=UTC).date().isoformat()
                    if last is not None
                    else "",
                    "bars": bars,
                }
            )
        return tuple(result)

    def delete_dataset(self, symbol: str) -> bool:
        """Purge market files and delete dataset definition."""
        logger.info("MarketDataStore deleting dataset: %s", symbol)
        return delete_market_symbol(self.database_path, self.data_root, symbol)

    def clear_dataset(self, symbol: str) -> bool:
        """Purge market files and reset coverage, retaining dataset definition."""
        logger.info("MarketDataStore clearing dataset: %s", symbol)
        return clear_market_symbol(self.database_path, self.data_root, symbol)

    def path(self, source: str, kind: Kind, symbol: str, period: str) -> Path:
        """Construct one canonical relative path from checked components."""
        return resolve_market_path(self.data_root, source, kind, symbol, period)

    def list_files(
        self, source: str, kind: Kind, symbol: str
    ) -> tuple[MarketFile, ...]:
        """List only committed catalog entries in period order."""
        self.path(source, kind, symbol, "2000" if kind == "m1" else "2000-01")
        with closing(open_market_catalog(self.database_path)) as connection:
            rows = connection.execute(
                "SELECT * FROM market_files WHERE source=? AND kind=? AND symbol=? "
                "ORDER BY period",
                (source, kind, symbol),
            ).fetchall()
        return tuple(self._file(row) for row in rows)

    @staticmethod
    def _file(row: Any) -> MarketFile:
        """Build an immutable descriptor from a checked catalog row."""
        return MarketFile(
            source=row["source"],
            kind=row["kind"],
            symbol=row["symbol"],
            period=row["period"],
            relative_path=row["relative_path"],
            revision=row["revision"],
            sha256=row["sha256"],
            byte_size=row["byte_size"],
            row_count=row["row_count"],
            first_ms=row["first_ms"],
            last_ms=row["last_ms"],
            coverage=tuple(tuple(item) for item in json.loads(row["coverage_json"])),
            provider_mode=row["provider_mode"],
        )

    def _verified_path(self, record: MarketFile) -> Path:
        """Resolve and digest-check one catalog entry before handing it to readers."""
        return verify_market_file(self.data_root, record)

    def lazy_scan(self, record: MarketFile) -> Any:
        """Expose a Polars lazy scan of a verified committed file."""
        import polars as pl

        return pl.scan_parquet(self._verified_path(record))

    def query(self, record: MarketFile, sql: str) -> list[tuple[Any, ...]]:
        """Query one verified file as `market_data` in an ephemeral DuckDB view."""
        import duckdb

        path = self._verified_path(record)
        with duckdb.connect(":memory:") as connection:
            connection.read_parquet(str(path)).create_view("market_data")
            return connection.execute(sql).fetchall()

    def publish(
        self,
        *,
        source: str,
        kind: Kind,
        symbol: str,
        period: str,
        table: pa.Table,
        coverage: tuple[tuple[int, int], ...],
        provider_mode: str,
    ) -> MarketFile:
        """Write a validated period, retaining a snapshot of prior revisions."""
        path = self.path(source, kind, symbol, period)
        expected = TICK_SCHEMA if kind == "ticks" else M1_SCHEMA
        if not table.schema.equals(expected) or table.num_rows == 0:
            raise ValueError("Market table schema or row count is invalid")
        stamps = table.column("DateTime").cast(pa.int64()).to_pylist()
        if stamps != sorted(stamps):
            raise ValueError("Market timestamps are not ordered")
        if kind == "m1" and len(set(stamps)) != len(stamps):
            raise ValueError("Duplicate M1 timestamps")
        for stamp in (stamps[0], stamps[-1]):
            instant = datetime.fromtimestamp(stamp / 1000, tz=UTC)
            actual = (
                f"{instant.year:04d}"
                if kind == "m1"
                else f"{instant.year:04d}-{instant.month:02d}"
            )
            if actual != period:
                raise ValueError("Market row lies outside its period")
        if not coverage or any(start > end for start, end in coverage):
            raise ValueError("Invalid covered intervals")
        path.parent.mkdir(parents=True, exist_ok=True)
        previous = next(
            (
                item
                for item in self.list_files(source, kind, symbol)
                if item.period == period
            ),
            None,
        )
        with NamedTemporaryFile(
            dir=path.parent, suffix=".parquet.tmp", delete=False
        ) as stream:
            staged = Path(stream.name)
        try:
            pq.write_table(table, staged, compression="zstd", compression_level=6)
            metadata = pq.read_metadata(staged)
            if (
                metadata.num_rows != table.num_rows
                or metadata.schema.to_arrow_schema() != expected
            ):
                raise ValueError("Staged Parquet verification failed")
            data = staged.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            revision = previous.revision + 1 if previous else 1
            if previous:
                self._verified_path(previous)
                revisions = self.data_root / "market-revisions" / source / kind / symbol
                revisions.mkdir(parents=True, exist_ok=True)
                snapshot = revisions / f"{period}-{previous.revision}.parquet"
                if snapshot.exists():
                    raise ValueError("Prior revision already archived")
                snapshot.write_bytes(path.read_bytes())
            Path(staged).replace(path)
            now = datetime.now(UTC).isoformat()
            relative = path.relative_to(self.data_root).as_posix()
            with (
                closing(open_market_catalog(self.database_path)) as connection,
                connection,
            ):
                connection.execute(
                    "INSERT OR REPLACE INTO market_files "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        source,
                        kind,
                        symbol,
                        period,
                        relative,
                        revision,
                        digest,
                        len(data),
                        table.num_rows,
                        stamps[0],
                        stamps[-1],
                        json.dumps(coverage),
                        provider_mode,
                        now,
                    ),
                )
            logger.info(
                "MarketDataStore published file %s/%s/%s period=%s (%d rows, %d bytes)",
                source,
                kind,
                symbol,
                period,
                table.num_rows,
                len(data),
            )
            return MarketFile(
                source,
                kind,
                symbol,
                period,
                relative,
                revision,
                digest,
                len(data),
                table.num_rows,
                stamps[0],
                stamps[-1],
                coverage,
                provider_mode,
            )
        finally:
            staged.unlink(missing_ok=True)

    def replace_interval(  # noqa: C901, PLR0912, PLR0915
        self,
        *,
        source: str,
        kind: Kind,
        symbol: str,
        period: str,
        incoming: pa.Table,
        start_ms: int,
        end_ms: int,
        provider_mode: str,
    ) -> MarketFile:
        """Replace one interval by streaming an immutable period rewrite."""
        path = self.path(source, kind, symbol, period)
        schema = TICK_SCHEMA if kind == "ticks" else M1_SCHEMA
        if not incoming.schema.equals(schema) or start_ms > end_ms:
            raise ValueError("Invalid market interval")
        logger.info(
            "MarketDataStore replacing interval %s/%s/%s period=%s "
            "[%d - %d ms] with %d rows",
            source,
            kind,
            symbol,
            period,
            start_ms,
            end_ms,
            incoming.num_rows,
        )

        def stamp(row: dict[str, Any]) -> int:
            return int(row["DateTime"].timestamp() * 1000)

        fresh: list[dict[str, Any]] = incoming.to_pylist()
        if any(not start_ms <= stamp(row) <= end_ms for row in fresh):
            raise ValueError("Incoming market row outside requested interval")
        if fresh != sorted(fresh, key=stamp):
            raise ValueError("Incoming market rows are unordered")
        if kind == "m1" and len({stamp(row) for row in fresh}) != len(fresh):
            raise ValueError("Duplicate M1 timestamps")
        previous = next(
            (
                item
                for item in self.list_files(source, kind, symbol)
                if item.period == period
            ),
            None,
        )

        def retained() -> Iterator[dict[str, Any]]:
            if previous is None:
                return
            parquet = pq.ParquetFile(self._verified_path(previous))
            if not parquet.schema_arrow.equals(schema):
                raise ValueError("Prior market schema mismatch")
            for batch in parquet.iter_batches(batch_size=BATCH_ROWS):
                for row in batch.to_pylist():
                    if not start_ms <= stamp(row) <= end_ms:
                        yield row

        staging = self.data_root / "market-staging"
        staging.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(dir=staging, suffix=".parquet", delete=False) as stream:
            staged = Path(stream.name)
        count = first_ms = last_ms = 0
        try:
            merged = heapq.merge(retained(), fresh, key=stamp)
            buffered: list[dict[str, Any]] = []

            def append_row(row: dict[str, Any], writer: pq.ParquetWriter) -> None:
                nonlocal count, first_ms, last_ms
                current = stamp(row)
                instant = datetime.fromtimestamp(current / 1000, tz=UTC)
                actual = (
                    f"{instant.year:04d}"
                    if kind == "m1"
                    else f"{instant.year:04d}-{instant.month:02d}"
                )
                if actual != period:
                    raise ValueError("Market row lies outside period")
                if count == 0:
                    first_ms = current
                last_ms = current
                count += 1
                buffered.append(row)
                if len(buffered) >= BATCH_ROWS:
                    writer.write_table(pa.Table.from_pylist(buffered, schema=schema))
                    buffered.clear()

            with pq.ParquetWriter(
                staged, schema, compression="zstd", compression_level=6
            ) as writer:
                pending: dict[str, Any] | None = None
                for row in merged:
                    if kind == "ticks":
                        append_row(row, writer)
                        continue
                    if pending is not None and stamp(row) != stamp(pending):
                        append_row(pending, writer)
                    pending = row
                if pending is not None:
                    append_row(pending, writer)
                if buffered:
                    writer.write_table(pa.Table.from_pylist(buffered, schema=schema))
            if count == 0:
                raise ValueError("No market rows to publish")
            metadata = pq.read_metadata(staged)
            if (
                metadata.num_rows != count
                or not metadata.schema.to_arrow_schema().equals(schema)
            ):
                raise ValueError("Staged market file verification failed")
            digest = hashlib.sha256()
            with staged.open("rb") as staged_file:
                for block in iter(lambda: staged_file.read(1024 * 1024), b""):
                    digest.update(block)
            revision = previous.revision + 1 if previous else 1
            if previous:
                revisions = self.data_root / "market-revisions" / source / kind / symbol
                revisions.mkdir(parents=True, exist_ok=True)
                snapshot = revisions / f"{period}-{previous.revision}.parquet"
                with path.open("rb") as old_file, snapshot.open("xb") as saved_file:
                    shutil.copyfileobj(old_file, saved_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            staged.replace(path)
            coverage = (
                tuple(sorted((*previous.coverage, (start_ms, end_ms))))
                if previous
                else ((start_ms, end_ms),)
            )
            relative = path.relative_to(self.data_root).as_posix()
            size = path.stat().st_size
            digest_hex = digest.hexdigest()
            with (
                closing(open_market_catalog(self.database_path)) as connection,
                connection,
            ):
                connection.execute(
                    "INSERT OR REPLACE INTO market_files "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        source,
                        kind,
                        symbol,
                        period,
                        relative,
                        revision,
                        digest_hex,
                        size,
                        count,
                        first_ms,
                        last_ms,
                        json.dumps(coverage),
                        provider_mode,
                        datetime.now(UTC).isoformat(),
                    ),
                )
            return MarketFile(
                source,
                kind,
                symbol,
                period,
                relative,
                revision,
                digest_hex,
                size,
                count,
                first_ms,
                last_ms,
                coverage,
                provider_mode,
            )
        finally:
            staged.unlink(missing_ok=True)
