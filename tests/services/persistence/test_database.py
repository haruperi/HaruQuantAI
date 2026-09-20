"""Tests for SQLite database persistence feature (FEAT-PERSISTENCE-DATABASE)."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from app.contracts.persistence import (
    DATABASE_SERVICE,
    DatabaseConnectionError,
)
from app.kernel.bootstrapper import Runtime
from app.services.persistence.database import (
    DatabaseConfig,
    DatabaseFeature,
    DatabaseServiceImpl,
    feature,
)


def test_database_config_defaults(tmp_path: Path) -> None:
    """Test default and explicit DatabaseConfig values."""
    db_file = tmp_path / "test.db"
    cfg = DatabaseConfig(database_path=db_file)
    assert cfg.database_path == db_file
    assert cfg.timeout_s == 5.0
    assert cfg.busy_timeout_ms == 5000
    assert cfg.wal_mode is True


def test_database_config_invalid() -> None:
    """Test validation errors for invalid config values."""
    with pytest.raises(ValueError, match="timeout_s must be positive"):
        DatabaseConfig(timeout_s=-1.0)

    with pytest.raises(ValueError, match="busy_timeout_ms must be positive"):
        DatabaseConfig(busy_timeout_ms=0)


def test_database_service_crud_and_transactions(tmp_path: Path) -> None:
    """Test queries, mutations, transactions, and rollback."""
    db_file = tmp_path / "test_crud.db"
    cfg = DatabaseConfig(database_path=db_file)
    service = DatabaseServiceImpl(cfg)

    # Initial query on created schema
    res = service.execute_query("SELECT count(*) as count FROM persistence_artifacts;")
    assert res[0]["count"] == 0

    # execute_mutation
    inserted = service.execute_mutation(
        "INSERT INTO persistence_databanks "
        "(project_name, databank_name, capacity, default_view, auto_sync_policy, created_at_utc) "
        "VALUES (?, ?, ?, ?, ?, ?);",
        ("ProjA", "Results", 100, "Default", "never", "2026-09-20T12:00:00Z"),
    )
    assert inserted == 1

    # execute_query
    rows = service.execute_query(
        "SELECT project_name, databank_name, capacity FROM persistence_databanks WHERE project_name = ?;",
        ("ProjA",),
    )
    assert len(rows) == 1
    assert rows[0]["project_name"] == "ProjA"
    assert rows[0]["capacity"] == 100

    # execute_script
    service.execute_script(
        "INSERT INTO persistence_databanks "
        "(project_name, databank_name, capacity, default_view, auto_sync_policy, created_at_utc) "
        "VALUES ('ProjA', 'Final', 50, 'Default', 'never', '2026-09-20T12:00:00Z');"
        "INSERT INTO persistence_databanks "
        "(project_name, databank_name, capacity, default_view, auto_sync_policy, created_at_utc) "
        "VALUES ('ProjA', 'Initial', 200, 'Default', 'never', '2026-09-20T12:00:00Z');"
    )
    all_dbs = service.execute_query(
        "SELECT databank_name FROM persistence_databanks WHERE project_name = 'ProjA' ORDER BY databank_name;"
    )
    assert [d["databank_name"] for d in all_dbs] == [
        "Final",
        "Initial",
        "Results",
    ]

    # transaction commit
    with service.transaction() as con:
        con.execute(
            "UPDATE persistence_databanks SET capacity = 500 WHERE databank_name = 'Final';"
        )

    updated = service.execute_query(
        "SELECT capacity FROM persistence_databanks WHERE databank_name = 'Final';"
    )
    assert updated[0]["capacity"] == 500

    # transaction rollback
    with pytest.raises(RuntimeError, match="Simulated failure"):
        with service.transaction() as con:
            con.execute(
                "UPDATE persistence_databanks SET capacity = 999 WHERE databank_name = 'Final';"
            )
            msg = "Simulated failure"
            raise RuntimeError(msg)

    rolled_back = service.execute_query(
        "SELECT capacity FROM persistence_databanks WHERE databank_name = 'Final';"
    )
    assert rolled_back[0]["capacity"] == 500

    # checkpoint & close
    service.checkpoint()
    service.close()


def test_database_initialization_error(tmp_path: Path) -> None:
    """Test error handling when database path is invalid."""
    invalid_path = tmp_path / "not_a_dir"
    # Create file where directory is expected
    invalid_path.write_text("blocker")
    blocked_db = invalid_path / "sub" / "db.sqlite"

    with pytest.raises(DatabaseConnectionError):
        DatabaseServiceImpl(DatabaseConfig(database_path=blocked_db))


def test_database_feature_lifecycle(tmp_path: Path) -> None:
    """Test feature registration, context injection, and lifecycle teardown."""

    async def _test() -> None:
        db_file = tmp_path / "lifecycle.db"
        runtime = Runtime(
            [lambda: DatabaseFeature(DatabaseConfig(database_path=db_file))]
        )
        async with runtime:
            service = runtime.require(DATABASE_SERVICE)
            assert service.database_path == db_file

            # Run query through injected service
            res = service.execute_query(
                "SELECT count(*) as count FROM persistence_artifacts;"
            )
            assert res[0]["count"] == 0

    asyncio.run(_test())


def test_database_factory() -> None:
    """Test zero-argument factory returns valid feature."""
    f = feature()
    assert isinstance(f, DatabaseFeature)
    assert f.spec.name == "persistence.database"
