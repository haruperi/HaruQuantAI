"""Unit tests for domain-owned database migrations runner."""

from pathlib import Path

import pytest
from app.services.data.contracts import DataError
from app.services.data.contracts.storage import (
    MigrationRequest,
    MigrationStep,
)
from app.services.data.storage.locking import acquire_write_lock
from app.services.data.storage.migrations import run_domain_migrations


def _configure_migrations(
    monkeypatch: pytest.MonkeyPatch,
    data_directory: Path,
) -> Path:
    """Configure one isolated database for migrations and return its path."""
    database_path = data_directory / "migrations.sqlite3"
    monkeypatch.setenv("DATABASE_URL", "sqlite:///migrations.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(data_directory))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "30")
    return database_path


def test_run_domain_migrations_applies_and_skips_steps(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Apply new migrations first, then check that running again skips them."""
    _configure_migrations(monkeypatch, tmp_path)

    step1 = MigrationStep(
        domain="data",
        migration_id="001_create_test",
        checksum="hash1",
        statements=("CREATE TABLE test_table (id INTEGER PRIMARY KEY, val TEXT)",),
    )
    step2 = MigrationStep(
        domain="data",
        migration_id="002_add_index",
        checksum="hash2",
        statements=("CREATE INDEX idx_test_val ON test_table (val)",),
    )

    request1 = MigrationRequest(
        domain="data",
        steps=(step1, step2),
        request_id="req-b46da39b2525ed3ee4e8fd74f4974ef75bf3e0fd34324f0a299fc1eceb464924",
    )

    # First run: should apply both
    result1 = run_domain_migrations(request1)
    assert result1.applied_ids == ("001_create_test", "002_add_index")
    assert result1.skipped_ids == ()

    # Second run with same request: should skip both
    result2 = run_domain_migrations(request1)
    assert result2.applied_ids == ()
    assert result2.skipped_ids == ("001_create_test", "002_add_index")


def test_run_domain_migrations_rejects_modified_applied_step(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Modifying the checksum of an already applied migration must raise an error."""
    _configure_migrations(monkeypatch, tmp_path)

    step1 = MigrationStep(
        domain="data",
        migration_id="001_create_test",
        checksum="hash1",
        statements=("CREATE TABLE test_table (id INTEGER PRIMARY KEY)",),
    )

    # Apply the first version of step 1
    run_domain_migrations(
        MigrationRequest(
            domain="data",
            steps=(step1,),
            request_id="req-1c465394a7256e0bd4fb6746c0906fcf394c93e3fc3d7ff5b5d94e13262f649c",
        )
    )

    # Create step 1 with modified checksum
    modified_step1 = MigrationStep(
        domain="data",
        migration_id="001_create_test",
        checksum="hash1_modified",
        statements=("CREATE TABLE test_table (id INTEGER PRIMARY KEY)",),
    )

    request_fail = MigrationRequest(
        domain="data",
        steps=(modified_step1,),
        request_id="req-b0883908531bfb068184243e2dbfbdba8313f9b0b65918d0f3ec90551eaff81a",
    )

    with pytest.raises(DataError) as captured:
        run_domain_migrations(request_fail)

    assert captured.value.code == "SCHEMA_MIGRATION_FAILED"
    assert captured.value.safe_details["stage"] == "checksum_validation"
    assert captured.value.safe_details["migration_id"] == "001_create_test"


def test_run_domain_migrations_rejects_out_of_order_step(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Applying a migration with a lower ID than maximum applied ID raises error."""
    _configure_migrations(monkeypatch, tmp_path)

    step2 = MigrationStep(
        domain="data",
        migration_id="002_create_table",
        checksum="hash2",
        statements=("CREATE TABLE second (id INTEGER PRIMARY KEY)",),
    )

    # Apply step 2 first (simulating out-of-order database state or step gaps)
    run_domain_migrations(
        MigrationRequest(
            domain="data",
            steps=(step2,),
            request_id="req-c3e9c0253cdddbe63e4241e137d042e852677834cc0f42c2dc539138b4f70c6e",
        )
    )

    step1 = MigrationStep(
        domain="data",
        migration_id="001_create_table",
        checksum="hash1",
        statements=("CREATE TABLE first (id INTEGER PRIMARY KEY)",),
    )

    # Now attempt to run step 1, which has lower ID than 2
    request_fail = MigrationRequest(
        domain="data",
        steps=(step1, step2),
        request_id="req-62d1d2555a5e35a974e02ceb75e51aa8fd44bb16f2338cd8c122441d0dd1b818",
    )

    with pytest.raises(DataError) as captured:
        run_domain_migrations(request_fail)

    assert captured.value.code == "SCHEMA_MIGRATION_FAILED"
    assert captured.value.safe_details["stage"] == "order_validation"
    assert captured.value.safe_details["migration_id"] == "001_create_table"


def test_run_domain_migrations_propagates_concurrent_lock(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An active write lock blocks the migration runner with CONCURRENT_WRITE_LOCKED."""
    database_path = _configure_migrations(monkeypatch, tmp_path)

    # Acquire the lock beforehand
    with acquire_write_lock(
        database_path,
        "req-9cfa283ea158f52056d10d74c3dad4a198f7d89587a65601ac05b83ef9e92d22",
    ):
        step = MigrationStep(
            domain="data",
            migration_id="001_test",
            checksum="hash1",
            statements=("CREATE TABLE test (id INTEGER PRIMARY KEY)",),
        )
        request = MigrationRequest(
            domain="data",
            steps=(step,),
            request_id="req-edaa55c9b738149fe519e7e254fec1dad549fce62ff08a1ab28000a65d6de1ac",
        )

        with pytest.raises(DataError) as captured:
            run_domain_migrations(request)

        assert captured.value.code == "CONCURRENT_WRITE_LOCKED"


def test_run_domain_migrations_rejects_unsafe_configuration(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Missing or invalid configuration raises DB_CONNECTION_ERROR."""
    # Ensure environment values are deleted/invalid
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DATA_DIR", raising=False)

    step = MigrationStep(
        domain="data",
        migration_id="001_test",
        checksum="hash1",
        statements=("CREATE TABLE test (id INTEGER PRIMARY KEY)",),
    )
    request = MigrationRequest(
        domain="data",
        steps=(step,),
        request_id="req-2c5ba42aa86dfdc67bd844f3252b1cfd53b4726c7b9dea4d9c34e85b35f12910",
    )

    with pytest.raises(DataError) as captured:
        run_domain_migrations(request)

    assert captured.value.code == "DB_CONNECTION_ERROR"


@pytest.mark.parametrize(
    ("db_url", "data_dir", "stage"),
    [
        ("sqlite:///:memory:", "exists", "configuration"),
        ("sqlite:///db.sqlite3?mode=ro", "exists", "configuration"),
        ("postgresql:///db", "exists", "configuration"),
        ("sqlite:///db.sqlite3", "nonexistent_dir", "configuration"),
        ("sqlite:///../outside.sqlite3", "exists", "configuration"),
        ("sqlite:///missing_parent/db.sqlite3", "exists", "configuration"),
    ],
)
def test_run_domain_migrations_invalid_env_details(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    db_url: str,
    data_dir: str,
    stage: str,
) -> None:
    """Invalid env variables trigger DB_CONNECTION_ERROR."""
    dir_path = tmp_path if data_dir == "exists" else tmp_path / "nonexistent"

    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("DATA_DIR", str(dir_path))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "1")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", "30")

    step = MigrationStep(
        domain="data",
        migration_id="001_test",
        checksum="hash1",
        statements=("CREATE TABLE test (id INTEGER PRIMARY KEY)",),
    )
    request = MigrationRequest(
        domain="data",
        steps=(step,),
        request_id="req-63196181e70b4db641ee87242a6b0bee26cd421dc09cf13c8d221e946cffda20",
    )

    with pytest.raises(DataError) as captured:
        run_domain_migrations(request)

    assert captured.value.code == "DB_CONNECTION_ERROR"
    assert captured.value.safe_details["stage"] == stage


def test_run_domain_migrations_ledger_initialization_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Ledger table creation failure triggers SCHEMA_MIGRATION_FAILED."""
    _configure_migrations(monkeypatch, tmp_path)

    from app.services.data.storage import migrations

    def mock_execute_transaction(*args, **kwargs):
        raise DataError("DATABASE_ERROR", safe_details={"stage": "mock"})

    monkeypatch.setattr(migrations, "execute_transaction", mock_execute_transaction)

    step = MigrationStep(
        domain="data",
        migration_id="001_test",
        checksum="hash1",
        statements=("CREATE TABLE test (id INTEGER PRIMARY KEY)",),
    )
    request = MigrationRequest(
        domain="data",
        steps=(step,),
        request_id="req-7b1614aa64942fea386a43b32faf63df2739536d624874e6b2f967e46d2b2487",
    )

    with pytest.raises(DataError) as captured:
        run_domain_migrations(request)

    assert captured.value.code == "SCHEMA_MIGRATION_FAILED"
    assert captured.value.safe_details["stage"] == "ledger_initialization"


def test_run_domain_migrations_ledger_query_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Ledger query failure triggers SCHEMA_MIGRATION_FAILED."""
    _configure_migrations(monkeypatch, tmp_path)

    from app.services.data.contracts import TransactionResult
    from app.services.data.storage import migrations

    calls = 0

    def mock_execute_transaction(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:  # First is init, second is query
            raise DataError("DATABASE_ERROR", safe_details={"stage": "mock"})
        return TransactionResult(
            rows=(),
            affected_rows=0,
            committed=True,
            request_id="req-4248ec040f25c337464d601a23be28bee0a2a9c01d8ff18ccdbc5913176bd0ff",
        )

    monkeypatch.setattr(migrations, "execute_transaction", mock_execute_transaction)

    step = MigrationStep(
        domain="data",
        migration_id="001_test",
        checksum="hash1",
        statements=("CREATE TABLE test (id INTEGER PRIMARY KEY)",),
    )
    request = MigrationRequest(
        domain="data",
        steps=(step,),
        request_id="req-3f648b5c5df3542ba593551b7f195d0d1153b386eadbacc46b023fd7ad4fa245",
    )

    with pytest.raises(DataError) as captured:
        run_domain_migrations(request)

    assert captured.value.code == "SCHEMA_MIGRATION_FAILED"
    assert captured.value.safe_details["stage"] == "ledger_query"


def test_run_domain_migrations_step_execution_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Step execution failure triggers SCHEMA_MIGRATION_FAILED."""
    _configure_migrations(monkeypatch, tmp_path)

    from app.services.data.contracts import TransactionResult
    from app.services.data.storage import migrations

    calls = 0

    def mock_execute_transaction(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 3:  # First is init, second is query, third is step execution
            raise DataError("DATABASE_ERROR", safe_details={"stage": "mock"})
        return TransactionResult(
            rows=(),
            affected_rows=0,
            committed=True,
            request_id="req-4248ec040f25c337464d601a23be28bee0a2a9c01d8ff18ccdbc5913176bd0ff",
        )

    monkeypatch.setattr(migrations, "execute_transaction", mock_execute_transaction)

    step = MigrationStep(
        domain="data",
        migration_id="001_test",
        checksum="hash1",
        statements=("CREATE TABLE test (id INTEGER PRIMARY KEY)",),
    )
    request = MigrationRequest(
        domain="data",
        steps=(step,),
        request_id="req-5260ff118a63787e7efa7a5b649197a24cacb65fe1d7df32d254f7711f51de2d",
    )

    with pytest.raises(DataError) as captured:
        run_domain_migrations(request)

    assert captured.value.code == "SCHEMA_MIGRATION_FAILED"
    assert captured.value.safe_details["stage"] == "step_execution"
