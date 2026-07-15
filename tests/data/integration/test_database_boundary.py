"""Integration tests for the short-lived Data SQLite boundary."""

import importlib
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from app.services.data.contracts import StatementPlan, TransactionRequest
from app.services.data.storage.database import execute_transaction


def test_database_connection_is_closed_after_committed_result(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A committed result contains no handle and leaves no open transaction."""
    database_path = tmp_path / "boundary.sqlite3"
    monkeypatch.setenv("DATABASE_URL", "sqlite:///boundary.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "0.1")
    result = execute_transaction(
        TransactionRequest(
            plan=StatementPlan(
                statements=("CREATE TABLE evidence (id INTEGER PRIMARY KEY)",),
                parameter_sets=((),),
                max_rows=1,
            ),
            request_id="req-0139010c42782f820ccb4d10eab26c7f12a4fd7a91dd9fb2df632e535bb0817a",
        )
    )

    with closing(
        sqlite3.connect(database_path, timeout=0.1, autocommit=False)
    ) as connection:
        connection.execute("INSERT INTO evidence (id) VALUES (?)", (1,))
        connection.commit()

    assert result.committed
    assert set(type(result).model_fields) == {
        "rows",
        "affected_rows",
        "committed",
        "request_id",
    }


def test_storage_package_import_has_no_configuration_or_filesystem_side_effect(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The structural storage package imports without reading configuration."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DATA_DIR", raising=False)
    monkeypatch.delenv("SQLITE_BUSY_TIMEOUT_SECONDS", raising=False)

    storage = importlib.import_module("app.services.data.storage")
    reloaded = importlib.reload(storage)

    expected = [
        "acquire_write_lock",
        "execute_transaction",
        "get_cache_entry",
        "load_dataset",
        "persist_audit_event",
        "put_cache_entry",
        "query_audit_events",
        "run_domain_migrations",
        "save_dataset",
    ]
    assert sorted(reloaded.__all__) == expected
    assert tuple(tmp_path.iterdir()) == ()
