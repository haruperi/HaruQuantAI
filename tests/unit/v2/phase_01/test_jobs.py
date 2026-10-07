"""Unit tests for app.host.jobs module.

Validates hardware diagnostics, process pool allocation, budget admission,
execution lifecycles, cooperative cancellation, deduplication, restart
reconciliation, EventBus integration, scoped JobAccess, and FastAPI REST routes.
"""

from __future__ import annotations

import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from app.host.jobs import (
    Budget,
    BudgetExceededError,
    CapacityExceededError,
    DuplicateJobError,
    HardwareDiagnostics,
    JobAccess,
    JobCancelledError,
    JobContext,
    JobManager,
    JobManagerClosedError,
    JobRecord,
    JobStatus,
    JobStore,
    create_jobs_router,
    create_pool,
    diagnostics,
    main,
)
from app.host.logging import TelemetryEngine, flush
from app.host.transport import EventBus
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _simple_add(a: int, b: int) -> int:
    """Helper addition task."""
    return a + b


def _divide(a: int, b: int) -> float:
    """Helper division task that can fail."""
    return a / b


def _slow_task(duration: float) -> str:
    """Helper sleeping task."""
    time.sleep(duration)
    return "done"


def _cooperative_task(context: JobContext, iterations: int = 5) -> int:
    """Helper cooperative task that checks cancellation."""
    count = 0
    for i in range(iterations):
        context.check_cancellation()
        context.report_progress((i + 1) / iterations * 100.0, accepted=i + 1)
        time.sleep(0.02)
        count += 1
    return count


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Provide an isolated temporary SQLite database path."""
    return tmp_path / "test_jobs.db"


@pytest.fixture
def thread_pool() -> Any:
    """Provide a bounded thread pool executor for fast, deterministic unit testing."""
    pool = ThreadPoolExecutor(max_workers=4)
    yield pool
    pool.shutdown(wait=False)


@pytest.fixture
def job_manager(temp_db: Path, thread_pool: ThreadPoolExecutor) -> Any:
    """Provide a JobManager using isolated DB and thread pool."""
    manager = JobManager(
        pool=thread_pool,
        max_workers=4,
        max_memory_bytes=1024 * 1024 * 100,  # 100 MiB
        db_path=temp_db,
        auto_reconcile=False,
    )
    yield manager
    manager.close()


# ==============================================================================
# Diagnostics & Pool Tests
# ==============================================================================


def test_diagnostics() -> None:
    """Validate hardware diagnostics sampling and requirement logging."""
    engine = TelemetryEngine.get_or_create()
    diag = diagnostics()
    flush()

    assert isinstance(diag, HardwareDiagnostics)
    assert diag.cpu_count_logical >= 1
    assert diag.cpu_count_physical >= 1
    assert diag.total_ram_bytes > 0
    assert diag.available_ram_bytes > 0
    assert diag.total_ram_gb > 0
    assert diag.available_ram_gb > 0
    assert len(diag.os_platform) > 0
    assert len(diag.python_version) > 0

    requirements = [e.context.get("requirement") for e in engine.ring_buffer._entries]
    assert "FR-HOST-JOBS-HARDWARE-DIAGNOSTICS" in requirements


def test_create_pool() -> None:
    """Validate bounded process pool allocation and requirement logging."""
    engine = TelemetryEngine.get_or_create()
    pool = create_pool(max_workers=2)
    flush()
    try:
        assert isinstance(pool, ProcessPoolExecutor)
        requirements = [
            e.context.get("requirement") for e in engine.ring_buffer._entries
        ]
        assert "FR-HOST-JOBS-POOL-ALLOCATION" in requirements
    finally:
        pool.shutdown(wait=False)


# ==============================================================================
# Budget Validation Tests
# ==============================================================================


def test_budget_validation() -> None:
    """Validate budget constraints and limits."""
    budget = Budget(workers=2, memory_bytes=1024, timeout_seconds=10.0)
    budget.validate(max_workers=4, max_memory_bytes=4096)

    # Worker count < 1
    with pytest.raises(ValueError, match="Worker count must be at least 1"):
        Budget(workers=0).validate(4, 4096)

    # Worker count > max_workers
    with pytest.raises(BudgetExceededError, match="exceeds max ceiling"):
        Budget(workers=5).validate(4, 4096)

    # Memory < 0
    with pytest.raises(ValueError, match="cannot be negative"):
        Budget(memory_bytes=-1).validate(4, 4096)

    # Memory > max_memory
    with pytest.raises(BudgetExceededError, match="exceeds ceiling"):
        Budget(memory_bytes=5000).validate(4, 4096)

    # Non-positive timeout
    with pytest.raises(ValueError, match="must be strictly positive"):
        Budget(timeout_seconds=0.0).validate(4, 4096)


# ==============================================================================
# Job Submission & Execution Lifecycle Tests
# ==============================================================================


def test_submit_and_execution_lifecycle(job_manager: JobManager) -> None:
    """Validate job admission, successful execution, and resource cleanup."""
    engine = TelemetryEngine.get_or_create()
    budget = Budget(workers=1, memory_bytes=1024, timeout_seconds=5.0)
    future = job_manager.submit(
        "test-owner",
        _simple_add,
        10,
        25,
        budget=budget,
        kind="calc",
    )

    result = future.result(timeout=5.0)
    assert result == 35

    job_id = job_manager.get_job_id_for_future(future)
    assert job_id is not None

    record = job_manager.get_job(job_id)
    assert record.status == JobStatus.COMPLETED
    assert record.progress == 100.0
    assert record.owner == "test-owner"
    assert record.kind == "calc"
    assert record.started_at_utc is not None
    assert record.finished_at_utc is not None
    assert record.error_message is None

    # Capacity reservations released
    cap = job_manager.capacity_status()
    assert cap.reserved_workers == 0
    assert cap.reserved_memory_bytes == 0

    flush()
    requirements = [e.context.get("requirement") for e in engine.ring_buffer._entries]
    assert "FR-HOST-JOBS-BUDGET-ADMISSION" in requirements
    assert "FR-HOST-JOBS-EXECUTION-LIFECYCLE" in requirements


def test_job_failure_lifecycle(job_manager: JobManager) -> None:
    """Validate error capturing, safe location, and failed status."""
    engine = TelemetryEngine.get_or_create()
    future = job_manager.submit(
        "fail-owner",
        _divide,
        10,
        0,
        budget=Budget(workers=1),
    )

    with pytest.raises(ZeroDivisionError):
        future.result(timeout=5.0)

    job_id = job_manager.get_job_id_for_future(future)
    assert job_id is not None

    record = job_manager.get_job(job_id)
    assert record.status == JobStatus.FAILED
    assert record.error_message == "ZeroDivisionError"
    assert record.error_location is not None
    assert "test_jobs.py" in record.error_location

    cap = job_manager.capacity_status()
    assert cap.reserved_workers == 0

    flush()
    requirements = [e.context.get("requirement") for e in engine.ring_buffer._entries]
    assert "FR-HOST-JOBS-EXECUTION-LIFECYCLE" in requirements


def test_capacity_exceeded_rejection(job_manager: JobManager) -> None:
    """Validate CapacityExceededError when requested resources exceed available capacity."""
    # Submit first job reserving 3 of 4 workers
    fut1 = job_manager.submit(
        "owner-1",
        _slow_task,
        0.5,
        budget=Budget(workers=3),
    )

    # Second job requesting 2 workers should be rejected (3 + 2 > 4)
    with pytest.raises(CapacityExceededError, match="Insufficient capacity"):
        job_manager.submit(
            "owner-2",
            _simple_add,
            1,
            2,
            budget=Budget(workers=2),
        )

    fut1.result(timeout=2.0)


# ==============================================================================
# Deduplication Tests
# ==============================================================================


def test_deduplication(job_manager: JobManager) -> None:
    """Validate duplicate job submission rejection while task is active."""
    engine = TelemetryEngine.get_or_create()
    fut1 = job_manager.submit(
        "owner-dedup",
        _slow_task,
        0.3,
        dedup_key="sync-market-ticks",
    )

    # Submitting identical dedup_key while fut1 is active must fail
    with pytest.raises(DuplicateJobError, match="active"):
        job_manager.submit(
            "owner-dedup-2",
            _slow_task,
            0.1,
            dedup_key="sync-market-ticks",
        )

    fut1.result(timeout=2.0)

    # Once fut1 completes, dedup_key is released and submission succeeds
    fut2 = job_manager.submit(
        "owner-dedup-3",
        _simple_add,
        2,
        3,
        dedup_key="sync-market-ticks",
    )
    assert fut2.result(timeout=2.0) == 5

    flush()
    requirements = [e.context.get("requirement") for e in engine.ring_buffer._entries]
    assert "FR-HOST-JOBS-DEDUPLICATION" in requirements


# ==============================================================================
# Cooperative Cancellation & Timeout Tests
# ==============================================================================


def test_cooperative_cancellation(job_manager: JobManager) -> None:
    """Validate cooperative cancellation via JobContext."""
    engine = TelemetryEngine.get_or_create()
    future = job_manager.submit(
        "cancel-owner",
        _cooperative_task,
        iterations=50,
        pass_context=True,
    )

    job_id = job_manager.get_job_id_for_future(future)
    assert job_id is not None

    time.sleep(0.04)
    cancelled = job_manager.cancel(job_id)
    assert cancelled is True

    # Future completes or raises JobCancelledError
    try:
        future.result(timeout=3.0)
    except JobCancelledError:
        pass

    record = job_manager.get_job(job_id)
    assert record.status == JobStatus.CANCELLED

    flush()
    requirements = [e.context.get("requirement") for e in engine.ring_buffer._entries]
    assert "FR-HOST-JOBS-COOPERATIVE-CANCELLATION" in requirements


def test_timeout_supervision(job_manager: JobManager) -> None:
    """Validate that exceeding timeout triggers cancellation."""
    future = job_manager.submit(
        "timeout-owner",
        _slow_task,
        2.0,
        budget=Budget(workers=1, timeout_seconds=0.1),
    )

    time.sleep(0.3)
    job_id = job_manager.get_job_id_for_future(future)
    assert job_id is not None

    record = job_manager.get_job(job_id)
    assert record.status in (JobStatus.CANCELLED, JobStatus.FAILED)


# ==============================================================================
# Progress Reporting & EventBus Tests
# ==============================================================================


def test_progress_reporting_and_eventbus(temp_db: Path) -> None:
    """Validate progress callback and EventBus broadcasting."""
    bus = EventBus(ring_capacity=32)
    pool = ThreadPoolExecutor(max_workers=2)
    manager = JobManager(
        pool=pool,
        max_workers=2,
        db_path=temp_db,
        event_bus=bus,
        auto_reconcile=False,
    )

    try:
        future = manager.submit(
            "prog-owner",
            _cooperative_task,
            iterations=5,
            pass_context=True,
        )
        assert future.result(timeout=3.0) == 5

        job_id = manager.get_job_id_for_future(future)
        assert job_id is not None

        record = manager.get_job(job_id)
        assert record.progress == 100.0
        assert record.accepted == 5

        # Check EventBus ring buffer received events on jobs channel
        snapshot = bus.get_snapshot(channel="jobs")
        assert len(snapshot.events) >= 2
        assert any(e.event_type == "jobs.changed" for e in snapshot.events)
    finally:
        manager.close()
        pool.shutdown(wait=False)


# ==============================================================================
# Parent-Child Hierarchy Tests
# ==============================================================================


def test_parent_child_hierarchy(job_manager: JobManager) -> None:
    """Validate parent job tracking and child link propagation."""
    parent_fut = job_manager.submit("parent-owner", _slow_task, 0.4)
    parent_id = job_manager.get_job_id_for_future(parent_fut)
    assert parent_id is not None

    child_fut = job_manager.submit(
        "parent-owner",
        _simple_add,
        1,
        2,
        parent_job_id=parent_id,
    )
    child_id = job_manager.get_job_id_for_future(child_fut)
    assert child_id is not None

    parent_fut.result(timeout=2.0)
    child_fut.result(timeout=2.0)

    parent_rec = job_manager.get_job(parent_id)
    child_rec = job_manager.get_job(child_id)

    assert child_id in parent_rec.child_job_ids
    assert child_rec.parent_job_id == parent_id


# ==============================================================================
# SQLite Persistence & Startup Reconciliation Tests
# ==============================================================================


def test_sqlite_persistence_and_restart_reconciliation(temp_db: Path) -> None:
    """Validate that orphaned active jobs are reconciled to INTERRUPTED on reboot."""
    engine = TelemetryEngine.get_or_create()
    store = JobStore(db_path=temp_db)
    store.initialize()

    now_utc = datetime.now(UTC).isoformat()

    # Pre-populate database with orphaned jobs
    store.upsert_job(
        JobRecord(
            job_id="job-queued",
            owner="system",
            status=JobStatus.QUEUED,
            submitted_at_utc=now_utc,
        )
    )
    store.upsert_job(
        JobRecord(
            job_id="job-running",
            owner="system",
            status=JobStatus.RUNNING,
            submitted_at_utc=now_utc,
            started_at_utc=now_utc,
        )
    )
    store.upsert_job(
        JobRecord(
            job_id="job-completed",
            status=JobStatus.COMPLETED,
            owner="system",
            submitted_at_utc=now_utc,
            finished_at_utc=now_utc,
        )
    )

    # Initialize new JobManager with auto_reconcile=True
    pool = ThreadPoolExecutor(max_workers=2)
    manager = JobManager(
        pool=pool,
        max_workers=2,
        db_path=temp_db,
        auto_reconcile=True,
    )
    try:
        # Check orphaned jobs are reconciled
        j_queued = manager.get_job("job-queued")
        j_running = manager.get_job("job-running")
        j_completed = manager.get_job("job-completed")

        assert j_queued.status == JobStatus.INTERRUPTED
        assert j_queued.finished_at_utc is not None
        assert "Host restarted" in str(j_queued.error_message)

        assert j_running.status == JobStatus.INTERRUPTED
        assert j_completed.status == JobStatus.COMPLETED

        flush()
        requirements = [
            e.context.get("requirement") for e in engine.ring_buffer._entries
        ]
        assert "FR-HOST-JOBS-RESTART-RECONCILIATION" in requirements
    finally:
        manager.close()
        pool.shutdown(wait=False)


# ==============================================================================
# Scoped JobAccess Facade Tests
# ==============================================================================


def test_job_access_facade(job_manager: JobManager) -> None:
    """Validate scoped JobAccess facade behavior and isolation."""
    access_a = JobAccess(job_manager, owner="workspace-alpha")
    access_b = JobAccess(job_manager, owner="workspace-beta")

    assert access_a.owner == "workspace-alpha"
    assert access_b.owner == "workspace-beta"

    fut_a = access_a.submit(_simple_add, 10, 20)
    fut_b = access_b.submit(_simple_add, 30, 40)

    assert fut_a.result(timeout=2.0) == 30
    assert fut_b.result(timeout=2.0) == 70

    jobs_a = access_a.list_jobs()
    jobs_b = access_b.list_jobs()

    assert all(j.owner == "workspace-alpha" for j in jobs_a)
    assert all(j.owner == "workspace-beta" for j in jobs_b)

    # Close scoped access A without affecting B
    access_a.close()


def test_manager_global_close(job_manager: JobManager) -> None:
    """Validate manager shutdown and post-closure rejection."""
    job_manager.close()
    cap = job_manager.capacity_status()
    assert cap.is_closed is True

    with pytest.raises(JobManagerClosedError, match="closed"):
        job_manager.submit("owner", _simple_add, 1, 2)


# ==============================================================================
# REST API Endpoints Tests
# ==============================================================================


def test_jobs_router_endpoints(job_manager: JobManager) -> None:
    """Validate FastAPI router endpoints for capacity, submission, list, and cancel."""
    app = FastAPI()
    router = create_jobs_router(job_manager)
    app.include_router(router)
    client = TestClient(app)

    # 1. Capacity endpoint
    cap_resp = client.get("/jobs/capacity")
    assert cap_resp.status_code == 200
    cap_json = cap_resp.json()
    assert cap_json["status"] == "success"
    assert cap_json["data"]["max_workers"] == 4

    # 2. Submit job endpoint
    sub_resp = client.post(
        "/jobs",
        json={
            "owner": "api-client",
            "kind": "compute",
            "workers": 1,
            "memory_bytes": 1024,
            "payload": {"param": "value"},
        },
    )
    assert sub_resp.status_code == 201
    sub_json = sub_resp.json()
    assert sub_json["status"] == "success"
    job_id = sub_json["data"]["job_id"]
    assert job_id is not None

    # Wait for execution to finish
    time.sleep(0.1)

    # 3. Get job by ID
    get_resp = client.get(f"/jobs/{job_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["job_id"] == job_id

    # 4. List jobs
    list_resp = client.get("/jobs", params={"owner": "api-client"})
    assert list_resp.status_code == 200
    assert len(list_resp.json()["data"]) >= 1

    # 5. Non-existent job query returns 404
    missing_resp = client.get("/jobs/non-existent-id")
    assert missing_resp.status_code == 404
    assert missing_resp.json()["status"] == "error"

    # 6. Cancel endpoint
    cancel_resp = client.post(f"/jobs/{job_id}/cancel")
    assert cancel_resp.status_code == 200

    # 7. Cancel non-existent job returns 404
    cancel_missing = client.post("/jobs/non-existent/cancel")
    assert cancel_missing.status_code == 404
    assert cancel_missing.json()["status"] == "error"

    # 8. Capacity exceeded submission returns 429
    # Reserve remaining workers
    fut = job_manager.submit("hog", _slow_task, 0.5, budget=Budget(workers=4))
    cap_exc_resp = client.post(
        "/jobs",
        json={"owner": "overflow", "workers": 2},
    )
    assert cap_exc_resp.status_code == 429
    assert cap_exc_resp.json()["error"]["code"] == "CAPACITY_EXCEEDED"
    fut.result(timeout=2.0)

    # 9. Duplicate submission returns 409
    fut_dup = job_manager.submit(
        "dup-test", _slow_task, 0.5, dedup_key="unique-api-key"
    )
    dup_resp = client.post(
        "/jobs",
        json={"owner": "dup", "dedup_key": "unique-api-key"},
    )
    assert dup_resp.status_code == 409
    assert dup_resp.json()["error"]["code"] == "DUPLICATE_JOB"
    fut_dup.result(timeout=2.0)

    # 10. Budget exceeded returns 422
    budget_exc_resp = client.post(
        "/jobs",
        json={"owner": "greedy", "workers": 100},  # max is 4
    )
    assert budget_exc_resp.status_code == 422
    assert budget_exc_resp.json()["error"]["code"] == "BUDGET_EXCEEDED"


# ==============================================================================
# CLI Entrypoint Tests
# ==============================================================================


def test_cli_main(temp_db: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Validate CLI flags execute without errors."""
    assert main(["--diagnostics"]) == 0
    captured = capsys.readouterr()
    assert "cpu_count_logical" in captured.out

    assert main(["--capacity"]) == 0
    captured = capsys.readouterr()
    assert "max_workers" in captured.out

    assert main(["--list", "--db-path", str(temp_db)]) == 0
    captured = capsys.readouterr()
    assert "[" in captured.out

    assert main(["--reconcile", "--db-path", str(temp_db)]) == 0
    captured = capsys.readouterr()
    assert "Reconciled" in captured.out

    assert main([]) == 0
