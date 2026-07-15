"""Integration tests for the Data path-lock persistence boundary."""

import importlib
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from app.services.data.storage.locking import acquire_write_lock


def _configure_locking(monkeypatch: pytest.MonkeyPatch, data_directory: Path) -> Path:
    """Configure one isolated integration lock database."""
    database_path = data_directory / "boundary-locking.sqlite3"
    monkeypatch.setenv("DATABASE_URL", "sqlite:///boundary-locking.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(data_directory))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "0.1")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "30")
    return database_path


def test_lock_release_persists_inactive_owner_evidence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Context exit closes its transaction and retains bounded owner evidence."""
    database_path = _configure_locking(monkeypatch, tmp_path)
    target = tmp_path / "boundary.parquet"

    with acquire_write_lock(
        target, "req-f345724aceae43e57c079d73e9f8e2f1352a047206a57df885838faef26d6bd9"
    ) as lock:
        assert lock.expires_at_ns > 0

    with closing(sqlite3.connect(database_path, autocommit=True)) as connection:
        row = connection.execute(
            """
            SELECT resolved_path, owner_request_id, active, lease_expires_at_ns
            FROM data_write_locks
            """
        ).fetchone()
        connection.execute("BEGIN IMMEDIATE")
        connection.rollback()

    assert row == (
        str(target.resolve()),
        "req-f345724aceae43e57c079d73e9f8e2f1352a047206a57df885838faef26d6bd9",
        0,
        "0000000000000000000",
    )


def test_locking_import_has_no_configuration_or_schema_side_effect(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Importing locking reads no environment and creates no bootstrap table."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DATA_DIR", raising=False)
    monkeypatch.delenv("SQLITE_BUSY_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("WRITE_LOCK_LEASE_SECONDS", raising=False)

    module = importlib.import_module("app.services.data.storage.locking")
    reloaded = importlib.reload(module)

    assert reloaded.__all__ == ["WriteLock", "acquire_write_lock"]
    assert tuple(tmp_path.iterdir()) == ()
