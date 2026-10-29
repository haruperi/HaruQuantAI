"""Tests for RemoteComputeCoordinator, grid contracts, and failure handling."""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from app.core.grid.contracts import (
    RemoteJobResult,
    RemoteJobSpec,
    RemoteWorkerNode,
)
from app.core.grid.executor import RemoteComputeCoordinator
from app.core.host.persistence import HostPersistence
from app.core.jobs.manager import JobManager


@pytest.fixture
def job_manager(tmp_path: Path) -> Generator[JobManager]:
    """Provide a fresh JobManager instance with SQLite persistence."""
    db_file = tmp_path / "test_jobs.db"
    conn = sqlite3.connect(db_file)
    try:
        conn.executescript("""
            CREATE TABLE host_jobs (
                job_id TEXT PRIMARY KEY, owner TEXT NOT NULL DEFAULT 'default',
                kind TEXT NOT NULL DEFAULT 'compute', status TEXT NOT NULL,
                progress REAL NOT NULL DEFAULT 0, accepted INTEGER DEFAULT 0,
                rejected INTEGER DEFAULT 0, message TEXT NOT NULL DEFAULT '',
                attempt_id INTEGER DEFAULT 1, submitted_at_utc TEXT NOT NULL DEFAULT '',
                started_at_utc TEXT, finished_at_utc TEXT, error_message TEXT);
            CREATE TABLE host_job_events (
                event_id TEXT PRIMARY KEY, job_id TEXT NOT NULL, attempt_id TEXT,
                from_state TEXT, to_state TEXT NOT NULL, details_json TEXT NOT NULL,
                created_at_utc TEXT NOT NULL);
        """)
    finally:
        conn.close()
    gateway = HostPersistence(db_file)
    mgr = JobManager(
        persistence=gateway,
        use_process_pool=False,
    )
    yield mgr
    mgr.shutdown(wait=True)


def test_topology_and_heartbeat_updates() -> None:
    """Verify worker node registration, heartbeat processing, and topology tracking."""
    coordinator = RemoteComputeCoordinator(fallback_to_local=False)
    t0 = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)

    node1 = RemoteWorkerNode(
        worker_id="node-1",
        ip="192.168.1.10",
        total_cores=8,
        total_memory_mb=16384.0,
        last_heartbeat_utc=t0,
    )
    node2 = RemoteWorkerNode(
        worker_id="node-2",
        ip="192.168.1.11",
        total_cores=16,
        total_memory_mb=32768.0,
        last_heartbeat_utc=t0,
    )

    coordinator.register_worker(node1)
    coordinator.register_worker(node2)

    topo = coordinator.get_topology(now_utc=t0)
    assert topo.total_cores == 24
    assert topo.running_threads == 0

    # Heartbeat updates thread and cpu usage
    coordinator.heartbeat(
        "node-1",
        timestamp_utc=t0 + timedelta(seconds=2),
        running_threads=4,
        cpu_usage_pct=50,
        used_memory_mb=4096.0,
    )
    updated_topo = coordinator.get_topology(now_utc=t0 + timedelta(seconds=2))
    assert updated_topo.running_threads == 4
    assert node1.cpu_usage_pct == 50


def test_fixture_1_two_worker_duplicate_delivery() -> None:
    """Concrete Fixture 1: Duplicate result from duplicate/retry worker is ignored (first-wins)."""
    coordinator = RemoteComputeCoordinator(fallback_to_local=False)
    t0 = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)

    worker_a = RemoteWorkerNode(
        worker_id="worker-A", ip="10.0.0.1", last_heartbeat_utc=t0
    )
    worker_b = RemoteWorkerNode(
        worker_id="worker-B", ip="10.0.0.2", last_heartbeat_utc=t0
    )
    coordinator.register_worker(worker_a)
    coordinator.register_worker(worker_b)

    spec = RemoteJobSpec(
        job_id="job-dup-1",
        job_group_id="group-1",
        operation_id="backtest",
        payload={"param": 10},
    )
    coordinator.submit(spec, now_utc=t0)
    assert coordinator.job_states["job-dup-1"] == "DISPATCHED"

    events: list[RemoteJobResult] = []
    coordinator.add_job_finished_listener(lambda _g, _j, res: events.append(res))

    # Worker A delivers result first
    result_a = RemoteJobResult(
        job_id="job-dup-1",
        job_group_id="group-1",
        worker_id="worker-A",
        success=True,
        data={"val": 1},
        duration_ms=100,
    )
    first_accepted = coordinator.handle_result(result_a)
    assert first_accepted is True
    assert coordinator.job_states["job-dup-1"] == "COMPLETED"
    assert coordinator.job_results["job-dup-1"].data == {"val": 1}
    assert len(events) == 1

    # Worker B delivers duplicate result second
    result_b = RemoteJobResult(
        job_id="job-dup-1",
        job_group_id="group-1",
        worker_id="worker-B",
        success=True,
        data={"val": 2},
        duration_ms=120,
    )
    second_accepted = coordinator.handle_result(result_b)
    assert second_accepted is False
    # Preserved original result from Worker A; no duplicate event
    assert coordinator.job_results["job-dup-1"].data == {"val": 1}
    assert len(events) == 1


def test_fixture_2_disconnected_worker_reassignment() -> None:
    """Concrete Fixture 2: In-flight job reassigned to healthy worker when current worker times out."""
    coordinator = RemoteComputeCoordinator(fallback_to_local=False)
    t0 = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)

    worker_a = RemoteWorkerNode(
        worker_id="worker-A", ip="10.0.0.1", last_heartbeat_utc=t0
    )
    worker_b = RemoteWorkerNode(
        worker_id="worker-B", ip="10.0.0.2", last_heartbeat_utc=t0
    )
    coordinator.register_worker(worker_a)
    coordinator.register_worker(worker_b)

    spec = RemoteJobSpec(
        job_id="job-dc-1",
        job_group_id="group-1",
        operation_id="optimization",
    )
    coordinator.submit(spec, now_utc=t0)
    assigned_worker = coordinator.assigned_jobs["job-dc-1"]

    # Worker B continues heartbeats, Worker A ceases
    t1 = t0 + timedelta(seconds=11)
    coordinator.heartbeat(
        "worker-B" if assigned_worker == "worker-A" else "worker-A",
        timestamp_utc=t1,
    )

    # Watchdog detects timeout
    disconnected = coordinator.check_watchdog(now_utc=t1)
    assert assigned_worker in disconnected
    # Reassigned to surviving worker
    new_worker = coordinator.assigned_jobs["job-dc-1"]
    assert new_worker != assigned_worker
    assert coordinator.job_states["job-dc-1"] == "DISPATCHED"

    # Surviving worker finishes job
    result = RemoteJobResult(
        job_id="job-dc-1",
        worker_id=new_worker,
        success=True,
        data={"status": "reassigned_ok"},
    )
    coordinator.handle_result(result)
    assert coordinator.job_states["job-dc-1"] == "COMPLETED"


def test_fixture_3_local_fallback_on_unconnected_cluster(
    job_manager: JobManager,
) -> None:
    """Concrete Fixture 3: Submitting with no healthy remote workers falls back to local JobManager."""
    coordinator = RemoteComputeCoordinator(
        local_manager=job_manager, fallback_to_local=True
    )
    spec = RemoteJobSpec(
        job_id="job-fallback-1",
        job_group_id="local-group",
        payload={"fn": lambda: 42 * 2},
    )

    job_record = coordinator.submit(spec)
    assert coordinator.is_local_mode is True
    # Returned a JobRecord from local JobManager
    assert hasattr(job_record, "job_id")
    assert job_record.job_id == "job-fallback-1"


def test_fixture_4_cancellation_acknowledgment() -> None:
    """Concrete Fixture 4: Cancel transition job to STOPPED and notifies listeners."""
    coordinator = RemoteComputeCoordinator(fallback_to_local=False)
    t0 = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)

    worker = RemoteWorkerNode(
        worker_id="worker-1", ip="10.0.0.1", last_heartbeat_utc=t0
    )
    coordinator.register_worker(worker)

    spec = RemoteJobSpec(job_id="job-stop-1")
    coordinator.submit(spec, now_utc=t0)
    assert coordinator.job_states["job-stop-1"] == "DISPATCHED"

    cancelled_events: list[RemoteJobResult] = []
    coordinator.add_job_finished_listener(
        lambda _g, _j, res: cancelled_events.append(res)
    )

    coordinator.cancel("job-stop-1")
    assert coordinator.job_states["job-stop-1"] == "STOPPED"
    assert len(cancelled_events) == 1
    assert cancelled_events[0].stopped is True
