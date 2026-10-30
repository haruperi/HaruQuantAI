"""Unit and integration tests for transactional background databank jobs."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from app.core.host.persistence import HostPersistence
from app.core.jobs import (
    AddToDatabankJob,
    DeleteFromDatabankJob,
    JobCancelledError,
    JobContext,
    JobManager,
    JobState,
    LoadFileToDatabankJob,
    MoveToDatabankJob,
    clear_databank_locks,
    is_databank_locked,
    lock_databank,
    locked_databank,
    unlock_databank,
)
from app.core.lib.errors import DomainError
from app.core.trading.results.contracts import RunResult
from app.core.trading.results.store import ResultStore


@pytest.fixture(autouse=True)
def _reset_databank_locks() -> None:
    clear_databank_locks()
    yield
    clear_databank_locks()


@pytest.fixture
def persistence_gateway(tmp_path: Path) -> HostPersistence:
    db_file = tmp_path / "test_databank_jobs.db"
    conn = sqlite3.connect(db_file)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS host_jobs (
            job_id TEXT PRIMARY KEY, owner TEXT NOT NULL DEFAULT 'default',
            kind TEXT NOT NULL DEFAULT 'compute', status TEXT NOT NULL,
            progress REAL NOT NULL DEFAULT 0, accepted INTEGER DEFAULT 0,
            rejected INTEGER DEFAULT 0, message TEXT NOT NULL DEFAULT '',
            attempt_id INTEGER DEFAULT 1, submitted_at_utc TEXT NOT NULL DEFAULT '',
            started_at_utc TEXT, finished_at_utc TEXT, error_message TEXT
        );
        CREATE TABLE IF NOT EXISTS host_job_events (
            event_id TEXT PRIMARY KEY, job_id TEXT NOT NULL, attempt_id TEXT,
            from_state TEXT, to_state TEXT NOT NULL, details_json TEXT NOT NULL,
            created_at_utc TEXT NOT NULL
        );
    """)
    conn.close()
    gateway = HostPersistence(db_file)
    gateway.ensure_databanks_schema()
    return gateway


@pytest.fixture
def store(persistence_gateway: HostPersistence) -> ResultStore:
    return ResultStore(persistence_gateway)


def _make_result(
    result_id: str,
    databank_id: str = "db-alpha",
    strategy_id: str = "strat-1",
    strategy_name: str = "Strategy 1",
    net_profit: float = 1000.0,
) -> RunResult:
    return RunResult(
        result_id=result_id,
        databank_id=databank_id,
        strategy_id=strategy_id,
        strategy_name=strategy_name,
        metrics={"net_profit": net_profit, "profit_factor": 1.5, "win_rate": 0.6},
        trades=(
            {
                "ticket": 1,
                "symbol": "EURUSD",
                "profit": 100.0,
                "close_time": "2026-01-01T12:00:00Z",
            },
        ),
    )


def test_add_to_databank_job(store: ResultStore, tmp_path: Path) -> None:
    results = [
        _make_result("res-1", "db-alpha", net_profit=100.0),
        _make_result("res-2", "db-alpha", net_profit=200.0),
    ]
    job = AddToDatabankJob("db-alpha", results, store=store)
    ctx = JobContext("job-add-1", tmp_path / "scratch-add")

    count = job(ctx)
    assert count == 2
    assert job.progress == 1.0

    # Verify results in store
    res1 = store.get_result("res-1")
    res2 = store.get_result("res-2")
    assert res1.result_id == "res-1"
    assert res1.databank_id == "db-alpha"
    assert res2.result_id == "res-2"

    # Verify progress reported
    progress_info = ctx.read_progress()
    assert progress_info is not None
    assert progress_info[0] == 100.0


def test_add_to_databank_job_locked_raises(store: ResultStore) -> None:
    results = [_make_result("res-locked", "db-locked")]
    job = AddToDatabankJob("db-locked", results, store=store)

    lock_databank("db-locked")
    with pytest.raises(DomainError) as exc_info:
        job()
    assert exc_info.value.code == "DATABANK_LOCKED"


def test_unlock_databank_allows_operations(store: ResultStore) -> None:
    results = [_make_result("res-unlocked", "db-temp")]
    job = AddToDatabankJob("db-temp", results, store=store)

    lock_databank("db-temp")
    assert is_databank_locked("db-temp")
    with pytest.raises(DomainError):
        job()

    unlock_databank("db-temp")
    assert not is_databank_locked("db-temp")
    assert job() == 1


def test_delete_from_databank_job(store: ResultStore, tmp_path: Path) -> None:
    results = [
        _make_result("res-del-1", "db-alpha"),
        _make_result("res-del-2", "db-alpha"),
    ]
    for r in results:
        store.save_result("db-alpha", r)

    job = DeleteFromDatabankJob("db-alpha", ["res-del-1", "res-del-2"], store=store)
    ctx = JobContext("job-del-1", tmp_path / "scratch-del")

    deleted = job(ctx)
    assert deleted == 2
    assert job.progress == 1.0

    with pytest.raises(DomainError) as exc1:
        store.get_result("res-del-1")
    assert exc1.value.code == "RESULT_NOT_FOUND"

    with pytest.raises(DomainError) as exc2:
        store.get_result("res-del-2")
    assert exc2.value.code == "RESULT_NOT_FOUND"


def test_delete_from_databank_job_locked_raises(store: ResultStore) -> None:
    job = DeleteFromDatabankJob("db-locked", ["res-1"], store=store)
    with locked_databank("db-locked"):
        with pytest.raises(DomainError) as exc_info:
            job()
        assert exc_info.value.code == "DATABANK_LOCKED"


def test_move_to_databank_job_transactional_success(
    store: ResultStore, tmp_path: Path
) -> None:
    results = [
        _make_result("res-m-1", "db-alpha"),
        _make_result("res-m-2", "db-alpha"),
    ]
    for r in results:
        store.save_result("db-alpha", r)

    job = MoveToDatabankJob("db-alpha", "db-beta", ["res-m-1", "res-m-2"], store=store)
    ctx = JobContext("job-move-1", tmp_path / "scratch-move")

    moved = job(ctx)
    assert moved == 2
    assert job.progress == 1.0

    # Verify moved to db-beta
    res1 = store.get_result("res-m-1")
    res2 = store.get_result("res-m-2")
    assert res1.databank_id == "db-beta"
    assert res2.databank_id == "db-beta"

    # Verify no results in db-alpha
    alpha_items = store.list_results("db-alpha")
    assert len(alpha_items) == 0

    beta_items = store.list_results("db-beta")
    assert len(beta_items) == 2


def test_move_to_databank_job_rollback_on_failure(
    persistence_gateway: HostPersistence,
) -> None:
    store = ResultStore(persistence_gateway)
    res1 = _make_result("res-safe-1", "db-src")
    res2 = _make_result("res-safe-2", "db-src")
    store.save_result("db-src", res1)
    store.save_result("db-src", res2)

    # Class that triggers a failure during the second item inside the transaction
    class FailingStore(ResultStore):
        def save_result(self, databank_id: str, result: RunResult) -> str:
            if result.result_id == "res-safe-2":
                msg = "Forced failure on second item to verify rollback"
                raise RuntimeError(msg)
            return super().save_result(databank_id, result)

    failing_store = FailingStore(persistence_gateway)
    job = MoveToDatabankJob(
        "db-src", "db-dst", ["res-safe-1", "res-safe-2"], store=failing_store
    )

    with pytest.raises(RuntimeError, match="Forced failure on second item"):
        job()

    # Both source items must remain intact in db-src!
    source_res1 = store.get_result("res-safe-1")
    source_res2 = store.get_result("res-safe-2")
    assert source_res1.databank_id == "db-src"
    assert source_res2.databank_id == "db-src"

    # Target must NOT contain any items!
    target_items = store.list_results("db-dst")
    assert len(target_items) == 0


def test_move_to_databank_job_locked_raises(store: ResultStore) -> None:
    job1 = MoveToDatabankJob("db-src", "db-dst", ["res-1"], store=store)
    with locked_databank("db-src"):
        with pytest.raises(DomainError) as exc1:
            job1()
        assert exc1.value.code == "DATABANK_LOCKED"

    job2 = MoveToDatabankJob("db-src", "db-dst", ["res-1"], store=store)
    with locked_databank("db-dst"):
        with pytest.raises(DomainError) as exc2:
            job2()
        assert exc2.value.code == "DATABANK_LOCKED"


def test_move_to_databank_job_result_not_in_source(store: ResultStore) -> None:
    res = _make_result("res-wrong", "db-gamma")
    store.save_result("db-gamma", res)

    job = MoveToDatabankJob("db-source", "db-target", ["res-wrong"], store=store)
    with pytest.raises(DomainError) as exc_info:
        job()
    assert exc_info.value.code == "RESULT_NOT_IN_SOURCE"


def test_load_file_to_databank_job(store: ResultStore, tmp_path: Path) -> None:
    single_res = _make_result("res-file-1", "db-import", net_profit=500.0)
    file_path = tmp_path / "single_result.json"
    file_path.write_text(json.dumps(single_res.to_dict()), encoding="utf-8")

    job = LoadFileToDatabankJob("db-import", file_path, store=store)
    ctx = JobContext("job-load-1", tmp_path / "scratch-load")

    imported = job(ctx)
    assert imported == 1
    assert job.progress == 1.0

    loaded = store.get_result("res-file-1")
    assert loaded.result_id == "res-file-1"
    assert loaded.databank_id == "db-import"


def test_load_file_to_databank_job_batch(store: ResultStore, tmp_path: Path) -> None:
    batch = [
        _make_result("res-b-1", "db-batch").to_dict(),
        _make_result("res-b-2", "db-batch").to_dict(),
    ]
    file_path = tmp_path / "batch_results.json"
    file_path.write_text(json.dumps({"results": batch}), encoding="utf-8")

    job = LoadFileToDatabankJob("db-batch", file_path, store=store)
    imported = job()
    assert imported == 2

    assert store.get_result("res-b-1").databank_id == "db-batch"
    assert store.get_result("res-b-2").databank_id == "db-batch"


def test_load_file_missing_and_corrupt(store: ResultStore, tmp_path: Path) -> None:
    missing_file = tmp_path / "non_existent.json"
    job_missing = LoadFileToDatabankJob("db-target", missing_file, store=store)
    with pytest.raises(DomainError) as exc_missing:
        job_missing()
    assert exc_missing.value.code == "FILE_NOT_FOUND"

    corrupt_file = tmp_path / "corrupt.json"
    corrupt_file.write_text("{ not valid json }", encoding="utf-8")
    job_corrupt = LoadFileToDatabankJob("db-target", corrupt_file, store=store)
    with pytest.raises(DomainError) as exc_corrupt:
        job_corrupt()
    assert exc_corrupt.value.code == "INVALID_FILE_FORMAT"


def test_cooperative_cancellation(store: ResultStore, tmp_path: Path) -> None:
    results = [_make_result("res-c-1", "db-alpha")]
    job = AddToDatabankJob("db-alpha", results, store=store)

    ctx = JobContext("job-cancel", tmp_path / "scratch-cancel")
    ctx.cancel()

    with pytest.raises(JobCancelledError):
        job(ctx)


def test_databank_jobs_with_job_manager_integration(
    persistence_gateway: HostPersistence, tmp_path: Path
) -> None:
    store = ResultStore(persistence_gateway)
    manager = JobManager(use_process_pool=False, persistence=persistence_gateway)

    try:
        # 1. Add job
        results = [
            _make_result("res-mgr-1", "db-managed"),
            _make_result("res-mgr-2", "db-managed"),
        ]
        add_job = AddToDatabankJob("db-managed", results, store=store)
        rec_add = manager.submit_job(add_job, kind="databank")
        manager.wait_for_job(rec_add.job_id, timeout=5.0)

        final_add_rec = manager.get_job(rec_add.job_id)
        assert final_add_rec is not None
        assert final_add_rec.status == JobState.COMPLETED
        assert final_add_rec.progress == 100.0

        # Verify results exist
        assert store.get_result("res-mgr-1").databank_id == "db-managed"
        assert store.get_result("res-mgr-2").databank_id == "db-managed"

        # 2. Move job
        move_job = MoveToDatabankJob(
            "db-managed", "db-archive", ["res-mgr-1"], store=store
        )
        rec_move = manager.submit_job(move_job, kind="databank")
        manager.wait_for_job(rec_move.job_id, timeout=5.0)

        final_move_rec = manager.get_job(rec_move.job_id)
        assert final_move_rec is not None
        assert final_move_rec.status == JobState.COMPLETED
        assert final_move_rec.progress == 100.0

        # Verify moved
        assert store.get_result("res-mgr-1").databank_id == "db-archive"
        assert len(store.list_results("db-managed")) == 1

    finally:
        manager.shutdown(wait=True)
