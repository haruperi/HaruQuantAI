"""Unit tests for AppGridControl service and coordinator lifecycle."""

from __future__ import annotations

import logging

import pytest
from app.core.grid.contracts import (
    RemoteJobResult,
    RemoteJobSpec,
    RemoteWorkerNode,
)
from app.core.grid.executor import RemoteComputeCoordinator
from app.workspace.grid_control.models import FinishedJobSnapshot
from app.workspace.grid_control.service import GridControlService


def test_service_initialization() -> None:
    """Verify service initializes with defaults and listener."""
    coordinator = RemoteComputeCoordinator()
    service = GridControlService(coordinator, max_finished_jobs=10)
    assert service.coordinator is coordinator
    assert service.max_finished_jobs == 10
    assert len(coordinator.listeners) == 1


def test_worker_registration_and_topology(caplog: pytest.LogCaptureFixture) -> None:
    """Verify worker registration, heartbeats, and topology queries."""
    service = GridControlService()
    node = RemoteWorkerNode(
        worker_id="node-1",
        ip="192.168.1.10",
        total_cores=8,
        total_memory_mb=16384.0,
    )

    with caplog.at_level(logging.INFO):
        service.register_worker(node)
    assert "FR-GRID-SERVICE-COORDINATION: Registering worker node-1" in caplog.text

    service.heartbeat(
        worker_id="node-1",
        running_threads=2,
        cpu_usage_pct=25,
        used_memory_mb=4096.0,
    )

    topology = service.get_topology()
    assert len(topology.nodes) == 1
    assert topology.total_cores == 8
    assert topology.running_threads == 2


def test_job_submission_and_queue_snapshot(caplog: pytest.LogCaptureFixture) -> None:
    """Verify jobs are partitioned into waiting and running depending on workers."""
    service = GridControlService()
    spec_waiting = RemoteJobSpec(
        job_id="job-wait-1",
        job_group_id="group-1",
    )

    # When no workers registered and fallback disabled, job remains waiting
    service.coordinator.fallback_to_local = False
    service.submit_job(spec_waiting)

    with caplog.at_level(logging.INFO):
        data = service.get_grid_data()
    assert len(data.waiting) == 1
    assert data.waiting[0].job_id == "job-wait-1"
    assert len(data.running) == 0
    assert "FR-GRID-SERVICE-SNAPSHOT" in caplog.text

    # Register worker so subsequent job runs
    node = RemoteWorkerNode(worker_id="node-1", ip="10.0.0.1", total_cores=4)
    service.register_worker(node)

    spec_running = RemoteJobSpec(
        job_id="job-run-1",
        job_group_id="group-2",
    )
    service.submit_job(spec_running)
    service.update_job_progress("job-run-1", 60)

    data2 = service.get_grid_data()
    assert len(data2.running) == 1
    assert data2.running[0].job_id == "job-run-1"
    assert data2.running[0].progress == 60


def test_job_completion_lifecycle(caplog: pytest.LogCaptureFixture) -> None:
    """Verify job completion moves jobs to finished with correct metrics."""
    service = GridControlService(max_finished_jobs=3)

    # Register worker so job is dispatched
    node = RemoteWorkerNode(worker_id="node-1", ip="10.0.0.1", total_cores=4)
    service.register_worker(node)

    spec = RemoteJobSpec(job_id="job-comp-1", job_group_id="analytics")
    service.submit_job(spec)

    result = RemoteJobResult(
        job_id="job-comp-1",
        job_group_id="analytics",
        worker_id="node-1",
        success=True,
        duration_ms=450,
    )

    with caplog.at_level(logging.INFO):
        handled = service.coordinator.handle_result(result)
    assert handled is True
    assert "Job job-comp-1 completed: success=True, duration=450ms" in caplog.text

    data = service.get_grid_data()
    assert len(data.finished) == 1
    assert data.finished[0].job_id == "job-comp-1"
    assert data.finished[0].success is True
    assert data.finished[0].duration_ms == 450


def test_manual_finished_job_and_bounded_history() -> None:
    """Verify max_finished_jobs ring buffer bounds history length."""
    service = GridControlService(max_finished_jobs=2)

    for i in range(4):
        snapshot = FinishedJobSnapshot(
            job_id=f"fin-{i}",
            job_group_id="test",
            create_time_ms=1000 + i,
            success=True,
        )
        service.record_finished_job(snapshot)

    data = service.get_grid_data()
    assert len(data.finished) == 2
    # Most recent should be fin-3 and fin-2
    assert [j.job_id for j in data.finished] == ["fin-3", "fin-2"]
