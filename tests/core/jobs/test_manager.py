"""Job lifecycle, cancellation, recovery, and real gateway persistence contracts."""

import os
import pickle
import sqlite3
import threading
from concurrent.futures import Future
from contextlib import closing
from unittest.mock import Mock

import pytest
from app.core.host import resources
from app.core.host.persistence import HostPersistence
from app.core.jobs import manager as jobs


class ControlledExecutor:
    """Expose real Future transitions without starting operating-system workers."""

    def __init__(self):
        self.calls = []
        self.shutdown = Mock()

    def submit(self, function, *args):
        future = Future()
        self.calls.append((future, function, args))
        return future

    def complete(self, index=0):
        future, function, args = self.calls[index]
        try:
            result = function(*args)
        except Exception as error:
            future.set_exception(error)
        else:
            future.set_result(result)


@pytest.fixture
def gateway(tmp_path):
    path = tmp_path / "jobs.db"
    with closing(sqlite3.connect(path)) as connection:
        connection.executescript("""
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
    return HostPersistence(path)


@pytest.fixture
def manager(gateway, tmp_path, monkeypatch):
    monitor = resources.ResourceMonitor(
        scratch_root=tmp_path / "scratch",
        probe_memory_fn=lambda: resources.MemoryObservation(
            100, 50, 50, 50, 1, 0.5, True
        ),
    )
    instance = jobs.JobManager(max_workers=2, resource_mgr=monitor, persistence=gateway)
    executor = ControlledExecutor()
    monkeypatch.setattr(instance, "ensure_pool", lambda: executor)
    monkeypatch.setattr(instance, "ensure_io_pool", lambda: executor)
    yield instance, executor
    instance.shutdown(cancel_futures=True)


def test_context_pickling_markers_progress_and_cancellation(tmp_path):
    event = threading.Event()
    context = jobs.JobContext("task", tmp_path, attempt_id=3, cancel_event=event)
    assert context.read_progress() is None
    context.report_progress(123, "finished")
    assert context.read_progress() == (100, "finished")
    context.report_progress(-1)
    assert context.read_progress() == (0, "")
    restored = pickle.loads(pickle.dumps(context))
    assert restored.job_id == "task" and restored.attempt_id == 3
    context.set_paused(True)
    assert restored.is_paused()
    restored.wait_if_paused(timeout=0)
    context.set_paused(False)
    assert not restored.is_paused()
    context.cancel()
    assert event.is_set() and restored.is_cancelled()
    with pytest.raises(jobs.JobCancelledError):
        restored.raise_if_cancelled()
    with pytest.raises(jobs.JobCancelledError):
        restored.report_progress(20)


def test_context_corrupt_progress_and_memory_policies(tmp_path, monkeypatch):
    context = jobs.JobContext("task", tmp_path)
    (tmp_path / jobs.PROGRESS_MARKER_FILE).write_text("invalid json")
    assert context.read_progress() is None
    status = resources.check_memory_headroom(
        memory_obs=resources.MemoryObservation(100, 5, 95, 95, 1, 0.05, True)
    )
    monkeypatch.setattr(jobs, "check_memory_headroom", lambda *_, **__: status)
    with pytest.raises(jobs.MemoryPressureError):
        context.check_memory_guard()
    pause = resources.check_memory_headroom(
        policy="pause",
        memory_obs=resources.MemoryObservation(100, 5, 95, 95, 1, 0.05, True),
    )
    monkeypatch.setattr(jobs, "check_memory_headroom", lambda *_, **__: pause)
    assert context.check_memory_guard(policy="pause") == pause
    assert context.is_paused()


def test_completed_job_persists_lifecycle_and_cleans_scratch(manager, gateway):
    service, executor = manager
    submitted = service.submit_job(
        jobs.run_sample_compute_task, 20, job_id="compute", owner="researcher"
    )
    assert submitted.status == jobs.JobState.RUNNING
    assert service.max_workers == 2
    assert service.resource_manager.scratch_root.is_dir()
    executor.complete()
    completed = service.wait_for_job("compute", timeout=0)
    assert completed.status == jobs.JobState.COMPLETED
    assert completed.progress == 100
    assert completed.result["iterations"] == 20
    assert completed.worker_pid == os.getpid()
    assert not (service.resource_manager.scratch_root / "compute").exists()
    assert [event["to_state"] for event in service.get_job_events("compute")] == [
        "RUNNING",
        "COMPLETED",
    ]
    assert service.list_jobs(status="COMPLETED")[0].owner == "researcher"
    restarted = jobs.JobManager(
        max_workers=1, persistence=gateway, resource_mgr=service.resource_manager
    )
    try:
        assert restarted.get_job("compute").status == "COMPLETED"
        assert restarted.get_job("missing") is None
    finally:
        restarted.shutdown()


def test_worker_failure_is_terminal_and_records_error(manager):
    service, executor = manager

    def fail():
        raise ValueError("bad input")

    service.submit_job(fail, job_id="failure")
    executor.complete()
    record = service.wait_for_job("failure", timeout=0)
    assert record.status == "FAILED" and record.error_message == "bad input"
    assert service.get_job_events("failure")[-1]["to_state"] == "FAILED"


def test_running_job_pause_progress_resume_and_cooperative_cancel(manager):
    service, executor = manager
    record = service.submit_job(lambda: "result", job_id="running")
    future = executor.calls[0][0]
    future.set_running_or_notify_cancel()
    context = jobs.JobContext(record.job_id, record.scratch_dir)
    context.report_progress(35, "checkpoint")
    assert service.get_job("running").progress == 35
    assert service.pause_job("running")
    assert context.is_paused() and service.get_job("running").status == "PAUSED"
    assert service.resume_job("running") and not context.is_paused()
    assert service.cancel_job("running")
    assert context.is_cancelled()
    executor.complete()
    assert service.wait_for_job("running", timeout=0).status == "CANCELLED"
    assert not service.cancel_job("missing")
    assert not service.pause_job("missing")
    assert not service.resume_job("missing")
    with pytest.raises(KeyError, match="not found"):
        service.wait_for_job("missing", timeout=0)


@pytest.mark.parametrize("policy", ["reject", "pause"])
def test_memory_admission_rejects_or_defers_without_dispatch(
    manager, monkeypatch, policy
):
    service, executor = manager
    pressured = resources.check_memory_headroom(
        policy=policy,
        memory_obs=resources.MemoryObservation(100, 5, 95, 95, 1, 0.05, True),
    )
    monkeypatch.setattr(
        service.resource_manager, "check_memory_headroom", lambda **_: pressured
    )
    if policy == "reject":
        with pytest.raises(jobs.MemoryPressureError):
            service.submit_job(lambda: 1, job_id="pressured", on_memory_pressure=policy)
        assert service.get_job("pressured").status == "FAILED"
    else:
        record = service.submit_job(
            lambda: 1, job_id="pressured", on_memory_pressure=policy
        )
        assert record.status == "PAUSED"
        assert service.resume_paused_jobs() == []
        assert service.cancel_job("pressured")
        assert service.wait_for_job("pressured", timeout=0).status == "CANCELLED"
    assert executor.calls == []


def test_paused_admission_dispatches_after_recovery(manager, monkeypatch):
    service, executor = manager
    current = [
        resources.check_memory_headroom(
            policy="pause",
            memory_obs=resources.MemoryObservation(100, 5, 95, 95, 1, 0.05, True),
        )
    ]
    monkeypatch.setattr(
        service.resource_manager, "check_memory_headroom", lambda **_: current[0]
    )
    service.submit_job(lambda: 42, job_id="deferred", on_memory_pressure="pause")
    current[0] = resources.check_memory_headroom(
        memory_obs=resources.MemoryObservation(100, 50, 50, 50, 1, 0.5, True)
    )
    assert service.resume_paused_jobs() == ["deferred"]
    executor.complete()
    assert service.wait_for_job("deferred", timeout=0).result == 42


def test_orphan_recovery_changes_only_running_rows(manager, gateway):
    service, _ = manager
    response = gateway.create_records(
        "host_jobs",
        [
            {"job_id": "orphan", "status": "RUNNING"},
            {"job_id": "finished", "status": "COMPLETED"},
        ],
    )
    assert response["success"]
    scratch = service.resource_manager.allocate_scratch("orphan")
    assert service.reconcile_orphan_jobs() == ["orphan"]
    assert not scratch.exists()
    assert service.get_job("orphan").status == "INTERRUPTED"
    assert service.get_job("finished").status == "COMPLETED"
    assert service.reconcile_orphan_jobs() == []


def test_executor_selection_laziness_and_shutdown(gateway, tmp_path, monkeypatch):
    monitor = resources.ResourceMonitor(scratch_root=tmp_path / "scratch")
    process, thread = Mock(), Mock()
    process.__name__ = "ProcessPoolExecutor"
    thread.__name__ = "ThreadPoolExecutor"
    monkeypatch.setattr(jobs, "ProcessPoolExecutor", process)
    monkeypatch.setattr(jobs, "ThreadPoolExecutor", thread)
    service = jobs.JobManager(max_workers=8, resource_mgr=monitor, persistence=gateway)
    assert not process.called and not thread.called
    assert service.ensure_pool() is service.ensure_pool()
    assert service.ensure_io_pool() is service.ensure_io_pool()
    process.assert_called_once_with(max_workers=8)
    thread.assert_called_once_with(max_workers=4)
    service.shutdown(cancel_futures=True)
    process.return_value.shutdown.assert_called_once_with(
        wait=True, cancel_futures=True
    )
    thread.return_value.shutdown.assert_called_once_with(wait=True, cancel_futures=True)
