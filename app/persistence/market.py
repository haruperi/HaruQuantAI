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
import os
import re
import shutil
import sqlite3
from collections.abc import Iterator
from contextlib import ExitStack, closing, suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import pairwise
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
MARKET_PAGE_ROWS = 2000

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
    "read_all_broker_profiles",
    "read_broker_profiles",
    "read_datamgr_log",
    "resolve_market_path",
    "verify_market_file",
]


class MarketSchemaUnavailableError(ValueError):
    """The active database has not received an approved market migration."""


class BrokerSchemaUnavailableError(ValueError):
    """The existing read-only broker catalog is absent or incompatible."""


MAX_SOURCE_LABEL = 160
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


def read_all_broker_profiles(path: Path) -> tuple[dict[str, Any], ...]:
    """Read enabled datamgr_broker records without modifying the database."""
    if not path.is_file():
        return ()
    try:
        with closing(
            sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
        ) as connection:
            connection.row_factory = sqlite3.Row
            columns = {
                row["name"]
                for row in connection.execute(
                    "PRAGMA table_info(datamgr_broker)"
                ).fetchall()
            }
            if not {"id", "name", "postfix"}.issubset(columns):
                return ()
            rows = connection.execute(
                "SELECT * FROM datamgr_broker WHERE enabled=1 ORDER BY id"
            ).fetchall()
    except sqlite3.DatabaseError:
        return ()
    result: list[dict[str, Any]] = []
    for row in rows:
        r = dict(row)
        clean_name = str(r.get("name") or "")
        if not clean_name:
            continue
        result.append(
            {
                "id": str(r.get("id", "")),
                "name": clean_name,
                "desc": str(r.get("description", "") or ""),
                "postfix": str(r.get("postfix", "") or ""),
                "timezone": str(r.get("server_timezone", "") or "UTC"),
                "mtUse": bool(r.get("mt_use", 0)),
                "stockPickerUse": bool(r.get("stockpicker_use", 0)),
                "system": bool(r.get("is_system", 0)),
                "stocks": (),
                "instruments": (),
            }
        )
    logger.info("Read %d full broker profiles from %s", len(result), path)
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

# Immutable script-backed partitions are indexed independently of the legacy
# tick/M1 tables. Provisioning remains explicit, never part of host startup.
SOURCE_SCHEMA = """
CREATE TABLE source_datasets (
  id TEXT PRIMARY KEY REFERENCES datamgr_datasets(id),
  owner TEXT NOT NULL,
  identity_json TEXT NOT NULL,
  options_json TEXT NOT NULL,
  UNIQUE(owner, identity_json)
);
CREATE TABLE source_partitions (
  dataset_id TEXT NOT NULL REFERENCES source_datasets(id),
  period TEXT NOT NULL,
  revision INTEGER NOT NULL CHECK(revision > 0),
  relative_path TEXT NOT NULL UNIQUE,
  sha256 TEXT NOT NULL,
  row_count INTEGER NOT NULL CHECK(row_count > 0),
  first_ms INTEGER NOT NULL,
  last_ms INTEGER NOT NULL,
  schema_json TEXT NOT NULL,
  committed_at TEXT NOT NULL,
  PRIMARY KEY(dataset_id, period, revision)
);
"""


def create_isolated_schema(path: Path) -> None:
    """Create a fresh test/research store; refuse to alter an existing database."""
    if path.exists():
        raise FileExistsError("Market schema creation requires a new database")
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as connection:
        connection.executescript(SCHEMA)
        connection.executescript(SOURCE_SCHEMA)
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


def migrate_source_schema(path: Path) -> Path | None:
    """Provision explicitly authorized source tables after a verified backup.

    The caller must stop every writer sharing this database and obtain separate
    authorization for operational storage. Startup never invokes this function.
    Existing incompatible or partially provisioned source tables are rejected.
    """
    with closing(open_market_catalog(path)) as connection:
        names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        if {"source_datasets", "source_partitions"}.intersection(names):
            if MarketDataStore(path.parent, path).source_available():
                return None
            raise MarketSchemaUnavailableError(
                "Existing source catalog is incompatible"
            )
        backup = path.with_name(f"{path.stem}_source_backup_{uuid4().hex}.db")
        with closing(sqlite3.connect(backup)) as target:
            connection.backup(target)
            if target.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise MarketSchemaUnavailableError(
                    "Source migration backup failed validation"
                )
        with connection:
            connection.executescript("BEGIN IMMEDIATE;\n" + SOURCE_SCHEMA + "\nCOMMIT;")
    logger.info("Provisioned source catalog after verified backup")
    return backup


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

    def source_available(self) -> bool:
        """Check script-backed storage without creating or migrating tables."""
        try:
            with closing(open_definition_catalog(self.database_path)) as connection:
                connection.execute(
                    "SELECT id,owner,identity_json,options_json FROM "
                    "source_datasets LIMIT 0"
                )
                connection.execute(
                    "SELECT dataset_id,period,revision,relative_path,sha256,row_count,"
                    "first_ms,last_ms,schema_json,committed_at FROM "
                    "source_partitions LIMIT 0"
                )
        except ValueError, sqlite3.Error:
            return False
        return True

    def inventory(self) -> tuple[dict[str, Any], ...]:
        """Read durable definitions without assigning invented quality or readiness."""
        with closing(open_definition_catalog(self.database_path)) as connection:
            rows = connection.execute(
                "SELECT * FROM datamgr_datasets ORDER BY symbol,id"
            ).fetchall()
        legacy = {row["id"]: row for row in self.list_datasets("dukascopy")}
        inventory: list[dict[str, Any]] = []
        for item in rows:
            row = dict(item)
            if row["id"] in legacy:
                actual = legacy[row["id"]]
                row.update(
                    bars=actual["bars"], date_from=actual["from"], date_to=actual["to"]
                )
            row["from"] = row["date_from"][:10]
            row["to"] = row["date_to"][:10]
            row["brokerName"] = row["broker_name"]
            row["quality"] = None
            row["status"] = "Stored" if row["bars"] else "Empty"
            inventory.append(row)
        logger.info("Read market inventory: count=%d", len(inventory))
        return tuple(inventory)

    def register_source(
        self,
        owner: str,
        *,
        source: str,
        symbol: str,
        underlying: str,
        instrument: str,
        timeframe: str,
        timezone: str,
        broker: str,
        options: dict[str, Any],
    ) -> str:
        """Register source identity and opaque provider options atomically."""
        labels = (
            owner,
            source,
            symbol,
            underlying,
            instrument,
            timeframe,
            timezone,
            broker,
        )
        if any(not value or len(value) > MAX_SOURCE_LABEL for value in labels):
            raise ValueError("Invalid source dataset identity")
        if not self.source_available():
            raise MarketSchemaUnavailableError(
                "Script-backed catalog migration is required"
            )
        identity = json.dumps(
            [source, symbol, underlying, instrument, timeframe, timezone, broker],
            separators=(",", ":"),
        )
        encoded_options = json.dumps(options, allow_nan=False, sort_keys=True)
        dataset_id = uuid4().hex
        now = datetime.now(UTC).isoformat()
        with (
            closing(open_definition_catalog(self.database_path)) as connection,
            connection,
        ):
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                "SELECT id, options_json FROM source_datasets WHERE owner=? "
                "AND identity_json=?",
                (owner, identity),
            ).fetchone()
            if existing is not None:
                if existing["options_json"] != encoded_options:
                    raise ValueError(
                        "Dataset already exists with different provider options"
                    )
                logger.info(
                    "Reused source definition: owner=%s id=%s", owner, existing["id"]
                )
                return str(existing["id"])
            connection.execute(
                "INSERT INTO datamgr_datasets "
                "(id,source,symbol,underlying,instrument,timeframe,broker,broker_name,"
                "timezone,category,date_from,date_to,bars,created_at,updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    dataset_id,
                    source,
                    symbol,
                    underlying,
                    instrument,
                    timeframe,
                    broker,
                    broker,
                    timezone,
                    "",
                    "",
                    "",
                    0,
                    now,
                    now,
                ),
            )
            connection.execute(
                "INSERT INTO source_datasets VALUES (?,?,?,?)",
                (dataset_id, owner, identity, encoded_options),
            )
        logger.info("Registered source definition: owner=%s id=%s", owner, dataset_id)
        return dataset_id

    def source_definition(self, owner: str, dataset_id: str) -> dict[str, Any]:
        """Read an owned definition, rejecting access to another provider's options."""
        with closing(open_definition_catalog(self.database_path)) as connection:
            row = connection.execute(
                "SELECT d.*,s.options_json FROM datamgr_datasets d "
                "JOIN source_datasets s "
                "ON s.id=d.id WHERE d.id=? AND s.owner=?",
                (dataset_id, owner),
            ).fetchone()
        if row is None:
            raise ValueError("Source dataset unavailable")
        result = dict(row)
        result["options"] = json.loads(result.pop("options_json"))
        logger.info("Read source definition: owner=%s id=%s", owner, dataset_id)
        return result

    def source_definitions(self, owner: str) -> tuple[dict[str, Any], ...]:
        """List only this source owner's definitions."""
        with closing(open_definition_catalog(self.database_path)) as connection:
            ids = connection.execute(
                "SELECT id FROM source_datasets WHERE owner=? ORDER BY id", (owner,)
            ).fetchall()
        return tuple(self.source_definition(owner, row["id"]) for row in ids)

    def source_partitions(self, dataset_id: str) -> tuple[dict[str, Any], ...]:
        """Read latest committed partition metadata without a producer import."""
        with closing(open_definition_catalog(self.database_path)) as connection:
            rows = connection.execute(
                "SELECT p.* FROM source_partitions p WHERE p.dataset_id=? AND "
                "p.revision=(SELECT MAX(q.revision) FROM source_partitions q "
                "WHERE q.dataset_id=p.dataset_id AND q.period=p.period) "
                "ORDER BY p.period",
                (dataset_id,),
            ).fetchall()
        return tuple(dict(row) for row in rows)

    def retained_source(self, dataset_id: str) -> dict[str, Any]:
        """Resolve retained definition metadata without loading its producer."""
        with closing(open_definition_catalog(self.database_path)) as connection:
            row = connection.execute(
                "SELECT * FROM datamgr_datasets WHERE id=?",
                (dataset_id,),
            ).fetchone()
            custody = (
                connection.execute(
                    "SELECT owner FROM source_datasets WHERE id=?",
                    (dataset_id,),
                ).fetchone()
                if self.source_available()
                else None
            )
        if row is None:
            raise ValueError("Source dataset unavailable")
        if custody is not None:
            return {
                **dict(row),
                "owner": custody["owner"],
                "storage_backend": "source_partitions",
            }
        # Retain the existing public format without importing its producer.
        self.get_dataset(dataset_id)
        return {
            **dict(row),
            "owner": "plugin.data_manager.dukascopy",
            "storage_backend": "market_files",
        }

    def read_source(self, dataset_id: str) -> pa.Table:
        """Decode current retained partitions in timestamp order."""
        definition = self.retained_source(dataset_id)
        if definition["storage_backend"] == "market_files":
            dataset = self.get_dataset(dataset_id)
            tables = [
                pq.read_table(self._verified_path(record))
                for record in self.list_files(
                    dataset.source,
                    dataset.kind,
                    dataset.symbol,
                )
            ]
        else:
            tables = [
                self.read_source_partition(row)
                for row in self.source_partitions(dataset_id)
            ]
        if not tables:
            raise ValueError("Dataset has no committed market rows")
        return pa.concat_tables(tables).sort_by("DateTime")

    def update_source_broker(
        self, dataset_id: str, broker: str, broker_name: str
    ) -> None:
        """Update broker metadata and its identity atomically without changing rows."""
        definition = self.retained_source(dataset_id)
        with (
            closing(open_definition_catalog(self.database_path)) as connection,
            connection,
        ):
            connection.execute("BEGIN IMMEDIATE")
            if definition["storage_backend"] == "source_partitions":
                identity = json.dumps(
                    [
                        definition[key]
                        for key in (
                            "source",
                            "symbol",
                            "underlying",
                            "instrument",
                            "timeframe",
                            "timezone",
                        )
                    ]
                    + [broker],
                    separators=(",", ":"),
                )
                connection.execute(
                    "UPDATE source_datasets SET identity_json=? WHERE id=?",
                    (identity, dataset_id),
                )
            connection.execute(
                "UPDATE datamgr_datasets SET broker=?,broker_name=?,updated_at=? "
                "WHERE id=?",
                (broker, broker_name, datetime.now(UTC).isoformat(), dataset_id),
            )
        logger.info("Updated dataset broker: id=%s broker=%s", dataset_id, broker)

    def export_source_definition(self, dataset_id: str) -> dict[str, Any]:
        """Return retained metadata and opaque source options for explicit transfer."""
        record = self.retained_source(dataset_id)
        if record["storage_backend"] == "source_partitions":
            record.update(self.source_definition(record["owner"], dataset_id))
        else:
            record["options"] = {}
        logger.info("Exported retained definition: id=%s", dataset_id)
        return record

    def remove_source(self, dataset_id: str, *, clear_only: bool) -> None:
        """Remove current catalog references; preserve immutable published bytes."""
        definition = self.retained_source(dataset_id)
        if definition["storage_backend"] != "source_partitions":
            if clear_only:
                clear_market_symbol(
                    self.database_path, self.data_root, definition["symbol"]
                )
            else:
                delete_market_symbol(
                    self.database_path, self.data_root, definition["symbol"]
                )
            return
        with (
            closing(open_definition_catalog(self.database_path)) as connection,
            connection,
        ):
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "DELETE FROM source_partitions WHERE dataset_id=?", (dataset_id,)
            )
            if clear_only:
                connection.execute(
                    "UPDATE datamgr_datasets SET bars=0,date_from='',date_to='' "
                    "WHERE id=?",
                    (dataset_id,),
                )
            else:
                connection.execute(
                    "DELETE FROM source_datasets WHERE id=?", (dataset_id,)
                )
                connection.execute(
                    "DELETE FROM datamgr_datasets WHERE id=?", (dataset_id,)
                )
        logger.info(
            "Removed dataset references: id=%s clear=%s", dataset_id, clear_only
        )

    def read_source_partition(self, record: dict[str, Any]) -> pa.Table:
        """Verify retained bytes and decode standard Parquet independently."""
        relative = Path(str(record["relative_path"]))
        root = self.data_root.resolve()
        path = root / relative
        if relative.is_absolute() or not path.resolve().is_relative_to(root):
            raise ValueError("Source partition path escapes storage")
        if any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)):
            raise ValueError("Linked source partition path")
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != record["sha256"]:
            raise ValueError("Source partition digest mismatch")
        logger.info(
            "Read verified source partition: id=%s period=%s",
            record["dataset_id"],
            record["period"],
        )
        return pq.read_table(pa.BufferReader(data))

    def publish_source(
        self,
        owner: str,
        dataset_id: str,
        period: str,
        table: pa.Table,
        *,
        expected_revision: int = 0,
    ) -> dict[str, Any]:
        """Publish one complete partition under checked host custody."""
        return self._publish_source(
            owner, dataset_id, period, table, expected_revision=expected_revision
        )

    def replace_source(
        self,
        owner: str,
        dataset_id: str,
        tables: dict[str, pa.Table],
        *,
        expected_revisions: dict[str, int],
    ) -> None:
        """Atomically replace a complete dataset snapshot, preserving prior bytes.

        A checked complete revision map prevents concurrent acquisition from being
        overwritten. New immutable files from a failed transaction stay unreferenced.
        """
        self.source_definition(owner, dataset_id)
        with (
            closing(open_definition_catalog(self.database_path)) as connection,
            connection,
        ):
            connection.execute("BEGIN IMMEDIATE")
            current = {
                row["period"]: row["revision"]
                for row in connection.execute(
                    "SELECT period,MAX(revision) AS revision FROM source_partitions "
                    "WHERE dataset_id=? GROUP BY period",
                    (dataset_id,),
                )
            }
            if current != expected_revisions:
                raise ValueError("Dataset changed; reload before replacing rows")
            for period, table in tables.items():
                self._publish_source(
                    owner,
                    dataset_id,
                    period,
                    table,
                    expected_revision=current.get(period, 0),
                    connection=connection,
                )
            for period in current.keys() - tables.keys():
                connection.execute(
                    "DELETE FROM source_partitions WHERE dataset_id=? AND period=?",
                    (dataset_id, period),
                )
            totals = connection.execute(
                "SELECT MIN(p.first_ms),MAX(p.last_ms),SUM(p.row_count) "
                "FROM source_partitions p WHERE p.dataset_id=? AND p.revision="
                "(SELECT MAX(q.revision) FROM source_partitions q "
                "WHERE q.dataset_id=p.dataset_id AND q.period=p.period)",
                (dataset_id,),
            ).fetchone()
            connection.execute(
                "UPDATE datamgr_datasets SET date_from=?,date_to=?,bars=?,updated_at=? "
                "WHERE id=?",
                (
                    datetime.fromtimestamp(totals[0] / 1000, tz=UTC).isoformat()
                    if totals[0] is not None
                    else "",
                    datetime.fromtimestamp(totals[1] / 1000, tz=UTC).isoformat()
                    if totals[1] is not None
                    else "",
                    totals[2] or 0,
                    datetime.now(UTC).isoformat(),
                    dataset_id,
                ),
            )
        logger.info(
            "Replaced source snapshot: id=%s partitions=%d", dataset_id, len(tables)
        )

    def _publish_source(  # noqa: C901, PLR0915 -- atomic immutable bytes and catalog commit.
        self,
        owner: str,
        dataset_id: str,
        period: str,
        table: pa.Table,
        *,
        expected_revision: int = 0,
        connection: sqlite3.Connection | None = None,
    ) -> dict[str, Any]:
        """Commit immutable source bytes under a checked optimistic revision.

        The plugin supplies the complete partition after its own merge policy.
        Failed catalog commits leave only unreferenced immutable bytes; readers
        never see them and previous revisions remain valid.
        """
        self.source_definition(owner, dataset_id)
        if not re.fullmatch(r"[0-9a-f]{32}", dataset_id) or not re.fullmatch(
            r"[A-Za-z0-9_-]{1,40}", period
        ):
            raise ValueError("Invalid source partition identity")
        if table.num_rows == 0 or "DateTime" not in table.column_names:
            raise ValueError("Source partition requires timestamped rows")
        column = table.column("DateTime")
        if (
            not pa.types.is_timestamp(column.type)
            or column.type.tz != "UTC"
            or column.null_count
        ):
            raise ValueError("Source timestamps must be non-null UTC timestamps")
        stamps = column.cast(pa.timestamp("ms", tz="UTC")).cast(pa.int64()).to_pylist()
        if stamps != sorted(stamps):
            raise ValueError("Source timestamps are not ordered")
        sink = pa.BufferOutputStream()
        pq.write_table(table, sink, compression="zstd", compression_level=6)
        content = sink.getvalue().to_pybytes()
        digest = hashlib.sha256(content).hexdigest()
        relative = Path("market", "datasets", dataset_id, period, f"{digest}.parquet")
        path = self.data_root / relative
        if any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)):
            raise ValueError("Linked source partition path")
        path.parent.mkdir(parents=True, exist_ok=True)
        schema_json = json.dumps({"arrow_schema": str(table.schema), "owner": owner})
        with ExitStack() as stack:
            if connection is None:
                connection = stack.enter_context(
                    closing(open_definition_catalog(self.database_path))
                )
                stack.enter_context(connection)
                connection.execute("BEGIN IMMEDIATE")
            actual = connection.execute(
                "SELECT COALESCE(MAX(revision),0) FROM source_partitions "
                "WHERE dataset_id=? AND period=?",
                (dataset_id, period),
            ).fetchone()[0]
            if actual != expected_revision:
                raise ValueError(
                    "Source partition changed; retry from the current revision"
                )
            if not path.exists():
                with NamedTemporaryFile(
                    dir=path.parent, suffix=".tmp", delete=False
                ) as target:
                    staged = Path(target.name)
                try:
                    with staged.open("wb") as target:
                        target.write(content)
                        target.flush()
                        os.fsync(target.fileno())
                    staged.replace(path)
                finally:
                    staged.unlink(missing_ok=True)
            elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise ValueError("Existing source bytes failed integrity verification")
            revision = actual + 1
            # Equal bytes are an idempotent publication, not a duplicate revision.
            prior = connection.execute(
                "SELECT * FROM source_partitions WHERE dataset_id=? AND "
                "period=? AND revision=?",
                (dataset_id, period, actual),
            ).fetchone()
            if prior is not None and prior["sha256"] == digest:
                logger.info(
                    "Source partition unchanged: id=%s period=%s", dataset_id, period
                )
                return dict(prior)
            now = datetime.now(UTC).isoformat()
            connection.execute(
                "INSERT INTO source_partitions VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    dataset_id,
                    period,
                    revision,
                    relative.as_posix(),
                    digest,
                    table.num_rows,
                    stamps[0],
                    stamps[-1],
                    schema_json,
                    now,
                ),
            )
            totals = connection.execute(
                "SELECT "
                "MIN(p.first_ms),MAX(p.last_ms),SUM(p.row_count) FROM "
                "source_partitions p "
                "WHERE p.dataset_id=? AND p.revision=(SELECT "
                "MAX(q.revision) FROM source_partitions q "
                "WHERE q.dataset_id=p.dataset_id AND q.period=p.period)",
                (dataset_id,),
            ).fetchone()
            connection.execute(
                "UPDATE datamgr_datasets SET "
                "date_from=?,date_to=?,bars=?,updated_at=? WHERE id=?",
                (
                    datetime.fromtimestamp(totals[0] / 1000, tz=UTC).isoformat(),
                    datetime.fromtimestamp(totals[1] / 1000, tz=UTC).isoformat(),
                    totals[2],
                    now,
                    dataset_id,
                ),
            )
            committed = connection.execute(
                "SELECT * FROM source_partitions WHERE dataset_id=? AND "
                "period=? AND revision=?",
                (dataset_id, period, revision),
            ).fetchone()
        logger.info(
            "Published source partition: id=%s period=%s revision=%d",
            dataset_id,
            period,
            revision,
        )
        return dict(committed)

    def list_brokers(self) -> tuple[MarketBroker, ...]:
        """List eligible profiles independently of market-file migration."""
        return tuple(
            MarketBroker(str(broker_id), name, postfix, timezone)
            for broker_id, name, postfix, timezone in read_broker_profiles(
                self.database_path
            )
        )

    def list_all_brokers(self) -> tuple[dict[str, Any], ...]:
        """List full broker records independently of market-file migration."""
        return read_all_broker_profiles(self.database_path)

    def definitions_available(self) -> bool:
        """Check definition storage independently of acquisition storage."""
        try:
            with closing(open_definition_catalog(self.database_path)):
                return True
        except ValueError, sqlite3.Error:
            return False

    def register_definitions(
        self, requests: tuple[DefinitionRequest, ...], *, idempotent: bool = False
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
                existing = connection.execute(
                    "SELECT id FROM datamgr_datasets WHERE source=? AND symbol=? "
                    "AND timeframe=? AND broker=?",
                    ("Dukascopy", name, timeframe, request.broker),
                ).fetchone()
                if existing:
                    if not idempotent:
                        raise ValueError("Dukascopy dataset definition already exists")
                    datasets.append(
                        MarketDataset(
                            existing["id"],
                            "dukascopy",
                            request.symbol.lower(),
                            request.kind,
                            request.symbol,
                            request.broker,
                            "UTC",
                        )
                    )
                    logger.info("Reused Dukascopy definition: id=%s", existing["id"])
                    continue
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

    def read_market_rows(
        self,
        dataset_id: str,
        *,
        start_ms: int,
        end_ms: int,
        offset: int = 0,
        limit: int = 2000,
    ) -> pa.Table:
        """Read a bounded verified page from a definition's canonical partitions."""
        if start_ms > end_ms or offset < 0 or not 1 <= limit <= MARKET_PAGE_ROWS:
            raise ValueError("Invalid market read bounds")
        dataset = self.get_dataset(dataset_id)
        schema = TICK_SCHEMA if dataset.kind == "ticks" else M1_SCHEMA
        selected: list[dict[str, Any]] = []
        skipped = 0
        for record in sorted(
            self.list_files("dukascopy", dataset.kind, dataset.symbol),
            key=lambda item: item.period,
        ):
            if record.last_ms < start_ms or record.first_ms > end_ms:
                continue
            parquet = pq.ParquetFile(self._verified_path(record))
            if not parquet.schema_arrow.equals(schema):
                raise ValueError("Market read schema mismatch")
            for batch in parquet.iter_batches(batch_size=BATCH_ROWS):
                for row in batch.to_pylist():
                    stamp = int(row["DateTime"].timestamp() * 1000)
                    if not start_ms <= stamp <= end_ms:
                        continue
                    if skipped < offset:
                        skipped += 1
                        continue
                    selected.append(row)
                    if len(selected) == limit:
                        logger.info(
                            "Read market page: rows=%d offset=%d", limit, offset
                        )
                        return pa.Table.from_pylist(selected, schema=schema)
        logger.info("Read market page: rows=%d offset=%d", len(selected), offset)
        return pa.Table.from_pylist(selected, schema=schema)

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
        received_intervals: tuple[tuple[int, int], ...] | None = None,
        merge_timestamps: bool = False,
    ) -> MarketFile:
        """Replace one interval by streaming an immutable period rewrite."""
        path = self.path(source, kind, symbol, period)
        schema = TICK_SCHEMA if kind == "ticks" else M1_SCHEMA
        if not incoming.schema.equals(schema) or start_ms > end_ms:
            raise ValueError("Invalid market interval")
        intervals = (
            received_intervals
            if received_intervals is not None
            else ((start_ms, end_ms),)
        )
        if not intervals or any(
            not start_ms <= first <= last <= end_ms for first, last in intervals
        ):
            raise ValueError("Invalid received intervals")
        if any(right[0] <= left[1] for left, right in pairwise(intervals)):
            raise ValueError("Overlapping or unordered received intervals")
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
        fresh_stamps = {stamp(row) for row in fresh}
        if any(
            not any(first <= stamp(row) <= last for first, last in intervals)
            for row in fresh
        ):
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
                    if (
                        stamp(row) not in fresh_stamps
                        if merge_timestamps
                        else not any(
                            first <= stamp(row) <= last for first, last in intervals
                        )
                    ):
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
                        if (
                            merge_timestamps
                            and previous
                            and pending is not None
                            and stamp(row) == stamp(pending)
                        ):
                            continue
                        append_row(row, writer)
                        pending = row if merge_timestamps and previous else None
                        continue
                    if pending is not None and stamp(row) != stamp(pending):
                        append_row(pending, writer)
                    pending = row
                if pending is not None and kind == "m1":
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
                tuple(sorted({*previous.coverage, *intervals}))
                if previous
                else intervals
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
