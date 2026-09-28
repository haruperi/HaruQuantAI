"""Host-owned market-file catalog; schema creation is explicit and isolated."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path


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
