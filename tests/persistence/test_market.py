"""Market catalog schema never mutates an existing unified database."""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from app.persistence.market import (
    BrokerSchemaUnavailableError,
    MarketSchemaUnavailableError,
    create_isolated_schema,
    open_market_catalog,
    read_broker_profiles,
)


def test_market_schema_is_explicit_and_rejects_existing_store(tmp_path: Path) -> None:
    """Provisioning a new test store is separate from live migration."""
    path = tmp_path / "database" / "haruquantai.db"
    with pytest.raises(MarketSchemaUnavailableError):
        open_market_catalog(path)
    create_isolated_schema(path)
    with closing(open_market_catalog(path)) as connection:
        assert (
            connection.execute("SELECT count(*) FROM market_files").fetchone()[0] == 0
        )
    with pytest.raises(FileExistsError):
        create_isolated_schema(path)


def test_read_only_broker_catalog_filters_eligible_rows(tmp_path: Path) -> None:
    """The profile list comes from SQLite, independent of market migration."""
    path = tmp_path / "database" / "haruquantai.db"
    path.parent.mkdir(parents=True)
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute(
            "CREATE TABLE datamgr_broker (id INTEGER PRIMARY KEY, name TEXT, "
            "postfix TEXT, server_timezone TEXT, enabled INTEGER, mt_use INTEGER)"
        )
        connection.executemany(
            "INSERT INTO datamgr_broker VALUES (?,?,?,?,?,?)",
            [
                (3, "Dukascopy", "_dukascopy", "EETUS", 1, 1),
                (2, "RoboForex", "_robo", "EET", 1, 1),
                (4, "Disabled", "_hidden", "UTC", 0, 1),
                (5, "Stocks only", "_stock", "UTC", 1, 0),
            ],
        )
    assert read_broker_profiles(path) == (
        (2, "RoboForex", "_robo", "EET"),
        (3, "Dukascopy", "_dukascopy", "EETUS"),
    )
    with closing(sqlite3.connect(path)) as connection:
        assert connection.execute("SELECT count(*) FROM datamgr_broker").fetchone() == (
            4,
        )


def test_missing_broker_table_fails_without_creation(tmp_path: Path) -> None:
    """An absent table cannot become a fabricated browser catalog."""
    path = tmp_path / "database" / "haruquantai.db"
    path.parent.mkdir(parents=True)
    with closing(sqlite3.connect(path)):
        pass
    with pytest.raises(BrokerSchemaUnavailableError):
        read_broker_profiles(path)
    with closing(sqlite3.connect(path)) as connection:
        names = connection.execute("SELECT name FROM sqlite_master").fetchall()
    assert names == []
