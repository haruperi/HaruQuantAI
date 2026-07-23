"""Unit tests for bounded atomic SQLite transaction execution.

[CAP-DATA-026 Phase 2] Copy of the legacy storage test, re-pointed at the
new `persistence`/`audit` modules. The legacy copy still guards `storage/`
until Phase 11 deletes it. Behaviour assertions are unchanged.
"""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from app.services.data.contracts import DataError
from app.services.data.persistence.contracts import (
    StatementPlan,
    TransactionRequest,
)
from app.services.data.persistence.transactions import execute_transaction


def _configure_database(
    monkeypatch: pytest.MonkeyPatch,
    data_directory: Path,
    *,
    database_url: str = "sqlite:///unit.sqlite3",
    timeout: str = "1",
) -> None:
    """Configure one isolated call-time database."""
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("DATA_DIR", str(data_directory))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", timeout)


def _request(
    *statements: str,
    parameters: tuple[tuple[None | bool | int | float | str | bytes, ...], ...],
    max_rows: int = 10,
    request_id: str = (
        "req-cdd2aca0ac58346ae812052ca1eb75f9a39c7367cb68da814d99aa4d81b2bead"
    ),
) -> TransactionRequest:
    """Build one exact statement plan for a unit test."""
    return TransactionRequest(
        plan=StatementPlan(
            statements=statements,
            parameter_sets=parameters,
            max_rows=max_rows,
        ),
        request_id=request_id,
    )


def test_execute_transaction_rolls_back_atomically(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A later integrity failure rolls back every earlier write in the plan."""
    _configure_database(monkeypatch, tmp_path)
    execute_transaction(
        _request(
            "CREATE TABLE facts (id INTEGER PRIMARY KEY, value TEXT NOT NULL)",
            parameters=((),),
        )
    )
    failing = _request(
        "INSERT INTO facts (id, value) VALUES (?, ?)",
        "INSERT INTO facts (id, value) VALUES (?, ?)",
        parameters=((1, "first"), (1, "duplicate")),
    )

    with pytest.raises(DataError) as captured:
        execute_transaction(failing)

    assert captured.value.code == "DB_WRITE_FAILED"
    assert captured.value.safe_details["stage"] == "execution"
    result = execute_transaction(
        _request("SELECT COUNT(*) AS count FROM facts", parameters=((),))
    )
    assert result.rows == ({"count": 0},)


@pytest.mark.parametrize(
    ("database_url", "timeout"),
    [
        ("postgresql:///data", "1"),
        ("sqlite:///:memory:", "1"),
        ("sqlite:///../outside.sqlite3", "1"),
        ("sqlite:///data.sqlite3?mode=rw", "1"),
        ("sqlite:///data.sqlite3", "0"),
        ("sqlite:///data.sqlite3", "not-a-number"),
    ],
)
def test_execute_transaction_rejects_unsafe_configuration(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    database_url: str,
    timeout: str,
) -> None:
    """Unsafe or unbounded configuration fails before opening a connection."""
    _configure_database(
        monkeypatch,
        tmp_path,
        database_url=database_url,
        timeout=timeout,
    )

    with pytest.raises(DataError) as captured:
        execute_transaction(_request("SELECT 1", parameters=((),)))

    assert captured.value.code == "DB_CONNECTION_ERROR"
    assert captured.value.safe_details["stage"] == "configuration"


def test_execute_transaction_requires_every_configuration_value() -> None:
    """Missing Data-owned configuration fails closed without path invention."""
    from app.services.data._settings import DataSettings, data_settings_context

    bad_settings = DataSettings(
        database_url=None,
        data_dir=None,
        sqlite_busy_timeout_seconds=None,
    )
    with data_settings_context(bad_settings), pytest.raises(DataError) as captured:
        execute_transaction(_request("SELECT 1", parameters=((),)))

    assert captured.value.code == "DB_CONNECTION_ERROR"


def test_execute_transaction_rolls_back_when_result_exceeds_bound(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A result beyond max_rows aborts writes made by the same transaction."""
    _configure_database(monkeypatch, tmp_path)
    execute_transaction(
        _request(
            "CREATE TABLE facts (id INTEGER PRIMARY KEY)",
            "INSERT INTO facts (id) VALUES (?)",
            "INSERT INTO facts (id) VALUES (?)",
            parameters=((), (1,), (2,)),
        )
    )
    failing = _request(
        "INSERT INTO facts (id) VALUES (?)",
        "SELECT id FROM facts ORDER BY id",
        parameters=((3,), ()),
        max_rows=1,
    )

    with pytest.raises(DataError) as captured:
        execute_transaction(failing)

    assert captured.value.code == "DATABASE_ERROR"
    assert captured.value.safe_details["stage"] == "result_bound"
    result = execute_transaction(
        _request("SELECT COUNT(*) AS count FROM facts", parameters=((),))
    )
    assert result.rows == ({"count": 2},)


@pytest.mark.parametrize(
    "statement",
    [
        "COMMIT",
        "ATTACH DATABASE ':memory:' AS escaped",
    ],
)
def test_execute_transaction_denies_caller_transaction_or_attachment(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    statement: str,
) -> None:
    """Caller SQL cannot escape the executor's transaction or database boundary."""
    _configure_database(monkeypatch, tmp_path)

    with pytest.raises(DataError) as captured:
        execute_transaction(_request(statement, parameters=((),)))

    assert captured.value.code == "DATABASE_ERROR"
    assert captured.value.safe_details["stage"] == "execution"


@pytest.mark.parametrize(
    ("statement", "stage"),
    [
        ("SELECT 1 AS duplicate, 2 AS duplicate", "result_columns"),
        ("SELECT X'00' AS unsupported", "result_value"),
    ],
)
def test_execute_transaction_rejects_unrepresentable_results(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    statement: str,
    stage: str,
) -> None:
    """Ambiguous columns and BLOB values never cross the typed result boundary."""
    _configure_database(monkeypatch, tmp_path)

    with pytest.raises(DataError) as captured:
        execute_transaction(_request(statement, parameters=((),)))

    assert captured.value.code == "DATABASE_ERROR"
    assert captured.value.safe_details["stage"] == stage


def test_execute_transaction_classifies_busy_timeout_as_write_lock(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A verified SQLite busy timeout maps to the shared lock-conflict code."""
    _configure_database(monkeypatch, tmp_path, timeout="0.01")
    database_path = tmp_path / "unit.sqlite3"
    execute_transaction(
        _request(
            "CREATE TABLE facts (id INTEGER PRIMARY KEY)",
            parameters=((),),
        )
    )

    with closing(
        sqlite3.connect(database_path, timeout=0.01, autocommit=False)
    ) as blocker:
        blocker.execute("INSERT INTO facts (id) VALUES (?)", (1,))
        with pytest.raises(DataError) as captured:
            execute_transaction(
                _request(
                    "INSERT INTO facts (id) VALUES (?)",
                    parameters=((2,),),
                )
            )
        blocker.rollback()

    assert captured.value.code == "CONCURRENT_WRITE_LOCKED"
    assert captured.value.safe_details["stage"] == "execution"
