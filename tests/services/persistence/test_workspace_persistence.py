"""Unit and integration tests for Workspace domain SQLite persistence."""

from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

import pytest
from app.contracts.workspace import WORKSPACE_PERSISTENCE
from app.kernel.bootstrapper import Runtime
from app.services.persistence.workspace import (
    SPEC,
    WorkspacePersistenceConfig,
    WorkspacePersistenceFeature,
    WorkspacePersistenceService,
    feature,
)


def test_persistence_config_validation() -> None:
    """Verify persistence configuration bounds checks."""
    config = WorkspacePersistenceConfig(busy_timeout_ms=3000)
    assert config.busy_timeout_ms == 3000

    with pytest.raises(ValueError, match="busy_timeout_ms must be non-negative"):
        WorkspacePersistenceConfig(busy_timeout_ms=-1)

    with pytest.raises(ValueError, match="db_path cannot be empty"):
        WorkspacePersistenceConfig(db_path="  ")


def test_sqlite_persistence_crud_and_rollback(tmp_path: Path) -> None:
    """Test SQL query, mutation, and transaction rollback on error."""
    db_file = str(tmp_path / "test_workspace.db")
    service = WorkspacePersistenceService(WorkspacePersistenceConfig(db_path=db_file))

    try:
        # Test insert setting
        rows = service.execute_mutation(
            "INSERT INTO workspace_settings (scope, key, value_json, updated_at_utc) "
            "VALUES (?, ?, ?, ?);",
            ("app", "test_key", '{"a": 1}', "2026-09-19T00:00:00Z"),
        )
        assert rows == 1

        # Test select
        result = service.execute_query(
            "SELECT scope, key, value_json FROM workspace_settings WHERE key = ?;",
            ("test_key",),
        )
        assert len(result) == 1
        assert result[0][0] == "app"
        assert result[0][1] == "test_key"
        assert result[0][2] == '{"a": 1}'

        # Test rollback on duplicate primary key failure
        with pytest.raises(sqlite3.IntegrityError):
            service.execute_mutation(
                "INSERT INTO workspace_settings (scope, key, value_json, updated_at_utc) "
                "VALUES (?, ?, ?, ?);",
                ("app", "test_key", '{"duplicate": true}', "2026-09-19T00:00:00Z"),
            )
    finally:
        service.close()


def test_persistence_feature_lifecycle(tmp_path: Path) -> None:
    """Verify feature factory, spec, and runtime mounting."""
    feat = feature()
    assert feat.spec == SPEC

    db_file = str(tmp_path / "test_lifecycle.db")

    async def _test() -> None:
        async with Runtime(
            (
                lambda: WorkspacePersistenceFeature(
                    WorkspacePersistenceConfig(db_path=db_file)
                ),
            )
        ) as runtime:
            service = runtime.require(WORKSPACE_PERSISTENCE)
            assert isinstance(service, WorkspacePersistenceService)

            # Check that schema tables are active
            tables = service.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
            )
            table_names = [r[0] for r in tables]
            assert "workspace_jobs" in table_names
            assert "workspace_settings" in table_names
            assert "workspace_grid_leases" in table_names

    asyncio.run(_test())
