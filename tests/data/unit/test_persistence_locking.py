"""Unit tests for persistent path-scoped Data write locks.

[CAP-DATA-026 Phase 2] Copy of the legacy storage test, re-pointed at the
new `persistence`/`audit` modules. The legacy copy still guards `storage/`
until Phase 11 deletes it. Behaviour assertions are unchanged.
"""

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import cast

import pytest
from app.services.data.contracts import DataError
from app.services.data.persistence import locking
from app.services.data.persistence.contracts import (
    TransactionRequest,
    TransactionResult,
)
from app.services.data.persistence.locking import acquire_write_lock


def _configure_locking(
    monkeypatch: pytest.MonkeyPatch,
    data_directory: Path,
    *,
    lease_seconds: str = "30",
) -> Path:
    """Configure one isolated lock database and return its path."""
    database_path = data_directory / "locking.sqlite3"
    monkeypatch.setenv("DATABASE_URL", "sqlite:///locking.sqlite3")
    monkeypatch.setenv("DATA_DIR", str(data_directory))
    monkeypatch.setenv("SQLITE_BUSY_TIMEOUT_SECONDS", "0.1")
    monkeypatch.setenv("WRITE_LOCK_LEASE_SECONDS", lease_seconds)
    return database_path


def _lock_row(database_path: Path, target: Path) -> tuple[object, ...]:
    """Read one persisted lock row for verification."""
    with closing(sqlite3.connect(database_path, autocommit=True)) as connection:
        row = connection.execute(
            """
            SELECT owner_request_id, active, lease_expires_at_ns,
                   previous_owner_request_id, recovered_at_ns, recovery_count
            FROM data_write_locks
            WHERE resolved_path = ?
            """,
            (str(target.resolve()),),
        ).fetchone()
    assert row is not None
    return row


def test_write_lock_is_path_scoped_and_exclusive(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """FR-DATA-016: one active owner blocks another owner on the same path."""
    _configure_locking(monkeypatch, tmp_path)
    target = tmp_path / "dataset.parquet"

    with (
        acquire_write_lock(
            target,
            "req-b2f972ff90198b269433a685737f461ed34f4ddb7c36be7e9faff7b6b40cf2dc",
        ),
        pytest.raises(DataError) as captured,
    ):
        acquire_write_lock(
            target,
            "req-0565ba438d31eb0e5a019dc636c894ffae5fee7f9c5e1240dc67bba72e527450",
        )

    assert captured.value.code == "CONCURRENT_WRITE_LOCKED"
    with acquire_write_lock(
        target, "req-24ab04ec4acda0c145865de174ee6065c9d979e8fe4cf8f9b404aad029e3b084"
    ) as reacquired:
        assert reacquired.path == target.resolve()


def test_different_resolved_paths_can_be_owned_together(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Lock exclusivity is scoped to the resolved path rather than globally."""
    _configure_locking(monkeypatch, tmp_path)

    with (
        acquire_write_lock(
            tmp_path / "one.csv",
            "req-6af65d1bad1fe41723c4ba5bc9da65ad30af95eead59cfa3deda8c25dd6a94e5",
        ),
        acquire_write_lock(
            tmp_path / "two.csv",
            "req-340f21f1a09a9f488b5ab8ef3d2f2be30a587ff4fd798a0b3933009057de0374",
        ),
    ):
        pass


def test_stale_lock_recovery_is_atomic_and_persists_evidence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An expired owner is replaced while bounded recovery evidence is retained."""
    database_path = _configure_locking(
        monkeypatch,
        tmp_path,
        lease_seconds="1",
    )
    times = iter((1_000_000_000, 2_000_000_000))
    monkeypatch.setattr(locking.time, "time_ns", lambda: next(times))
    target = tmp_path / "stale.csv"

    abandoned = acquire_write_lock(
        target, "req-61261de311c66ee9928f20e2bc9d83fcaa3498fdab96317b8b3820e51c8689e4"
    )
    with acquire_write_lock(
        target, "req-a982027e287b92f89b7984548551a52948505b5da64ade4b388f5434fece21e1"
    ) as recovered:
        assert recovered.recovery_count == 1

    row = _lock_row(database_path, target)
    assert (
        abandoned.request_id
        == "req-61261de311c66ee9928f20e2bc9d83fcaa3498fdab96317b8b3820e51c8689e4"
    )
    assert row == (
        "req-a982027e287b92f89b7984548551a52948505b5da64ade4b388f5434fece21e1",
        0,
        "0000000000000000000",
        "req-61261de311c66ee9928f20e2bc9d83fcaa3498fdab96317b8b3820e51c8689e4",
        "0000000002000000000",
        1,
    )


@pytest.mark.parametrize("value", [None, "", " 1", "0", "-1", "nan", "inf", "1e20"])
def test_lock_lease_configuration_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    value: str | None,
) -> None:
    """A missing or invalid lease duration fails before lock-table creation."""
    from app.services.data._settings import DataSettings, data_settings_context

    database_path = _configure_locking(monkeypatch, tmp_path)

    lease = None if value is None else value  # type: ignore[arg-type]

    try:
        settings = DataSettings(
            database_url="sqlite:///locking.sqlite3",
            data_dir=tmp_path,
            sqlite_busy_timeout_seconds=0.1,
            write_lock_lease_seconds=lease,
        )
        context = data_settings_context(settings)
    except ValueError:

        def _raise_value_error():
            raise ValueError("bad settings")

        class _BadSettingsContext:
            def __enter__(self):
                target_path = "app.services.data.persistence.locking.get_data_settings"
                monkeypatch.setattr(target_path, _raise_value_error)

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        context = _BadSettingsContext()

    with context, pytest.raises(DataError) as captured:
        acquire_write_lock(
            tmp_path / "invalid.csv",
            "req-2bafd040219b771f2951816df2030ebcfeae4a9a6b0beedca0794caf066a8085",
        )

    assert captured.value.code == "DB_CONNECTION_ERROR"
    assert not database_path.exists()


@pytest.mark.parametrize("request_id", ["", " request", "request "])
def test_lock_requires_caller_owned_request_id(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    request_id: str,
) -> None:
    """Blank or untrimmed owner identities fail before persistence."""
    database_path = _configure_locking(monkeypatch, tmp_path)

    with pytest.raises(DataError) as captured:
        acquire_write_lock(tmp_path / "invalid.csv", request_id)

    assert captured.value.code == "INVALID_INPUT"
    assert not database_path.exists()


def test_lock_rejects_non_path_input(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Runtime path validation fails closed before persistence."""
    database_path = _configure_locking(monkeypatch, tmp_path)

    with pytest.raises(DataError) as captured:
        acquire_write_lock(
            cast("Path", "not-a-path"),
            "req-b8064ee6a3eb5622a5fa6eef5fec60c43147e6425834eaead5d6647a10b0aab0",
        )

    assert captured.value.code == "INVALID_INPUT"
    assert not database_path.exists()


def test_lock_rejects_inconsistent_persisted_result(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Unexpected acquisition evidence never becomes a successful lease."""
    _configure_locking(monkeypatch, tmp_path)

    def _inconsistent_result(request: TransactionRequest) -> TransactionResult:
        return TransactionResult(
            rows=(
                {
                    "owner_request_id": (
                        "req-13d6b58ac3340a2bb680ae96f455bbae5e06e3dc63a7df18"
                        "afb26f0d0953d3d6"
                    ),
                    "lease_expires_at_ns": "0000000000000000001",
                    "recovery_count": 0,
                },
            ),
            affected_rows=1,
            committed=True,
            request_id=request.request_id,
        )

    monkeypatch.setattr(locking, "execute_transaction", _inconsistent_result)

    with pytest.raises(DataError) as captured:
        acquire_write_lock(
            tmp_path / "result.csv",
            "req-502380604dc2c213ee83e5e7b473e65f437c11e8bd0a3ee8cbfd512974bab732",
        )

    assert captured.value.code == "DATABASE_ERROR"


def test_release_does_not_clear_a_recovered_owner(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An expired owner's exit cannot delete a verified successor lease."""
    database_path = _configure_locking(
        monkeypatch,
        tmp_path,
        lease_seconds="1",
    )
    times = iter((1_000_000_000, 2_000_000_000))
    monkeypatch.setattr(locking.time, "time_ns", lambda: next(times))
    target = tmp_path / "owner.csv"
    abandoned = acquire_write_lock(
        target, "req-9c41a36f930606de49211e907304eb7ebec1487464bfa8b52835350459dd068a"
    )
    successor = acquire_write_lock(
        target, "req-67be6c5ffe05da4c3cab25d3fe3d7eae5084fd687fbc958f1395a1133dacf9da"
    )

    with pytest.raises(DataError) as captured:
        abandoned.__exit__(None, None, None)

    assert captured.value.code == "CONCURRENT_WRITE_LOCKED"
    assert _lock_row(database_path, target)[0:2] == (
        "req-67be6c5ffe05da4c3cab25d3fe3d7eae5084fd687fbc958f1395a1133dacf9da",
        1,
    )
    successor.__enter__()
    successor.__exit__(None, None, None)


def test_write_lock_context_cannot_be_reentered(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """One acquired context cannot be entered twice or reused after release."""
    _configure_locking(monkeypatch, tmp_path)
    lock = acquire_write_lock(
        tmp_path / "context.csv",
        "req-032124525dcd565cdd553d78b79aaee38fb37b71982ec92d73cb1174471d62f3",
    )

    with lock, pytest.raises(DataError) as captured:
        lock.__enter__()
    with pytest.raises(DataError):
        lock.__enter__()

    assert captured.value.code == "CONCURRENT_WRITE_LOCKED"
