"""Tests for schema migrations feature (FEAT-PERSISTENCE-MIGRATIONS)."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from app.contracts.persistence import (
    MIGRATION_SERVICE,
    MigrationError,
)
from app.kernel.bootstrapper import Runtime
from app.services.persistence.database import (
    DatabaseConfig,
    DatabaseFeature,
    DatabaseServiceImpl,
)
from app.services.persistence.migrations import (
    MigrationConfig,
    MigrationFeature,
    MigrationServiceImpl,
    feature,
)


def test_migrations_initial_and_apply(tmp_path: Path) -> None:
    """Test discovering and applying built-in forward migrations."""
    db_file = tmp_path / "test_mig.db"
    db_service = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
    mig_service = MigrationServiceImpl(db_service)

    assert mig_service.current_version() == 0
    pending = mig_service.get_pending_migrations()
    assert len(pending) == 2
    assert [p.version for p in pending] == [1, 2]

    # Apply all migrations
    applied = mig_service.apply_all()
    assert len(applied) == 2
    assert mig_service.current_version() == 2

    # Second apply_all should be no-op
    pending_after = mig_service.get_pending_migrations()
    assert len(pending_after) == 0
    applied_again = mig_service.apply_all()
    assert len(applied_again) == 0


def test_custom_migrations_and_directory(tmp_path: Path) -> None:
    """Test custom migrations via configuration and file discovery."""
    db_file = tmp_path / "test_custom_mig.db"
    mig_dir = tmp_path / "sql_migrations"
    mig_dir.mkdir()

    # Create file-based migration 0003
    file_sql = "CREATE TABLE test_extra (id INTEGER PRIMARY KEY, note TEXT);"
    (mig_dir / "0003_extra_table.sql").write_text(file_sql, encoding="utf-8")

    db_service = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))
    config = MigrationConfig(
        migrations_dir=mig_dir,
        custom_migrations=(
            (
                4,
                "0004_another_table",
                "CREATE TABLE test_fourth (val REAL);",
            ),
        ),
    )
    mig_service = MigrationServiceImpl(db_service, config)

    pending = mig_service.get_pending_migrations()
    assert [p.version for p in pending] == [1, 2, 3, 4]

    applied = mig_service.apply_all()
    assert len(applied) == 4
    assert mig_service.current_version() == 4

    # Verify tables were created
    res = db_service.execute_query(
        "SELECT count(*) as count FROM sqlite_master WHERE type='table' AND name IN ('test_extra', 'test_fourth');"
    )
    assert res[0]["count"] == 2


def test_migration_checksum_mismatch(tmp_path: Path) -> None:
    """Test that modifying an already applied migration fails closed."""
    db_file = tmp_path / "test_tamper.db"
    db_service = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))

    # Apply standard migrations
    mig_service_initial = MigrationServiceImpl(db_service)
    mig_service_initial.apply_all()
    assert mig_service_initial.current_version() == 2

    # Tamper with recorded checksum in database
    db_service.execute_mutation(
        "UPDATE persistence_schema_migrations SET checksum = 'tampered' WHERE version = 1;"
    )

    mig_service_tampered = MigrationServiceImpl(db_service)
    with pytest.raises(MigrationError, match="Checksum mismatch"):
        mig_service_tampered.get_pending_migrations()

    with pytest.raises(MigrationError, match="Checksum mismatch"):
        mig_service_tampered.apply_all()


def test_migration_failure_rollback(tmp_path: Path) -> None:
    """Test that a failing migration rolls back cleanly without advancing version."""
    db_file = tmp_path / "test_fail.db"
    db_service = DatabaseServiceImpl(DatabaseConfig(database_path=db_file))

    broken_config = MigrationConfig(
        custom_migrations=(
            (
                3,
                "0003_broken",
                "INVALID SQL SYNTAX HERE STATEMENT;",
            ),
        )
    )
    mig_service = MigrationServiceImpl(db_service, broken_config)

    with pytest.raises(MigrationError, match="Failed to apply migration"):
        mig_service.apply_all()

    # Initial built-ins (1 and 2) applied, but 3 was rolled back and not recorded
    applied = mig_service.get_applied_migrations()
    assert len(applied) == 2
    assert mig_service.current_version() == 2


def test_migrations_feature_lifecycle(tmp_path: Path) -> None:
    """Test feature composition and runtime registration."""

    async def _test() -> None:
        db_file = tmp_path / "runtime_mig.db"
        runtime = Runtime(
            [
                lambda: DatabaseFeature(DatabaseConfig(database_path=db_file)),
                MigrationFeature,
            ]
        )
        async with runtime:
            mig_service = runtime.require(MIGRATION_SERVICE)
            assert mig_service.current_version() == 0
            applied = mig_service.apply_all()
            assert len(applied) == 2
            assert mig_service.current_version() == 2

    asyncio.run(_test())


def test_migrations_factory() -> None:
    """Test zero-argument factory returns valid MigrationFeature."""
    f = feature()
    assert isinstance(f, MigrationFeature)
    assert f.spec.name == "persistence.migrations"
