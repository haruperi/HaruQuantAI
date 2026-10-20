"""Unit and multiprocessing tests for Stage 1D resource governance and JobManager.

Tests app/host/resources.py (consolidated diagnostics, hardware/storage/DB probes,
workers = max(1, cpu_cores - 2) allocation policy, active 15% RAM MemoryWatchdog,
DataFrame guard, memory cleanup, per-job scratch sandboxing) and app/host/jobs.py
(ProcessPoolExecutor worker pool, cooperative JobContext cancellation, memory
pressure admission gating, and startup RUNNING -> INTERRUPTED reconciliation).
"""

from __future__ import annotations

import ast
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

import app.host.jobs as jobs_mod
import app.host.resources as resources_mod
import psutil
import pytest
from app.host.jobs import (
    JobCancelledError,
    JobContext,
    JobManager,
    JobState,
    MemoryPressureError,
    run_sample_compute_task,
)
from app.host.persistence import HostPersistence
from app.host.resources import (
    MIN_AVAILABLE_RAM_PCT,
    BenchmarkRunner,
    HostHealthReport,
    MemoryObservation,
    MemoryWatchdog,
    MemoryWatchdogStatus,
    ResourceMonitor,
    WorkerCapacity,
    allocate_job_scratch,
    apply_cpu_affinity,
    calculate_worker_allocation,
    check_memory_headroom,
    cleanup_job_scratch,
    evaluate_dataframe_guard,
    get_worker_capacity,
    inspect_cpu_affinity,
    inspect_gpu_qualification,
    inspect_resources,
    inspect_workspace_directories,
    job_scratch_sandbox,
    probe_cpu,
    probe_database,
    probe_disk,
    probe_hardware,
    probe_memory,
    probe_process,
    probe_storage,
    run_cpu_benchmark,
    run_memory_cleanup,
)

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture


@pytest.fixture(autouse=True)
def isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect HostPersistence.DEFAULT_DB_PATH to an isolated temporary file."""
    db_file = tmp_path / "test_resources_jobs.db"
    monkeypatch.setattr(HostPersistence, "DEFAULT_DB_PATH", db_file)
    return db_file


# ---------------------------------------------------------------------------
# Top-level picklable worker functions for ProcessPoolExecutor tests
# ---------------------------------------------------------------------------


def mp_worker_with_context(ctx: JobContext, multiplier: int) -> dict[str, Any]:
    """Top-level multiprocessing worker verifying JobContext and child PID."""
    ctx.raise_if_cancelled()
    ctx.wait_if_paused(timeout=1.0)
    ctx.report_progress(50.0, "Halfway in child process")
    scratch_file = ctx.scratch_dir / "worker_output.txt"
    scratch_file.write_text(f"pid={os.getpid()}", encoding="utf-8")
    ctx.raise_if_cancelled()
    return {
        "worker_pid": os.getpid(),
        "job_id": ctx.job_id,
        "computed": 21 * multiplier,
        "scratch_exists": scratch_file.is_file(),
    }


def mp_worker_without_context(a: int, b: int) -> int:
    """Top-level worker that does not take a JobContext parameter."""
    return a + b


def mp_cancellable_spin_worker(ctx: JobContext, max_steps: int = 300) -> int:
    """Top-level worker that polls JobContext until cancelled."""
    ready_marker = ctx.scratch_dir / "worker_started.flag"
    ready_marker.write_text("started", encoding="utf-8")
    for step in range(max_steps):
        ctx.raise_if_cancelled()
        time.sleep(0.02)
        if step % 5 == 0:
            ctx.report_progress(float(step), f"step {step}")
    return max_steps


def mp_failing_worker(ctx: JobContext) -> None:
    """Top-level worker that raises a deterministic RuntimeError."""
    ctx.report_progress(10.0, "About to fail")
    msg = "Simulated worker computation failure"
    raise RuntimeError(msg)


# ---------------------------------------------------------------------------
# Architectural & Module Contract Tests
# ---------------------------------------------------------------------------


def test_module_contracts_and_no_forbidden_imports() -> None:
    """Verify __all__ bounds and absence of sqlite3 or stdlib logging imports."""
    assert len(resources_mod.__all__) <= 15
    assert len(jobs_mod.__all__) <= 6

    for mod_path in (
        Path(resources_mod.__file__).resolve(),
        Path(jobs_mod.__file__).resolve(),
    ):
        tree = ast.parse(mod_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != "sqlite3", f"Forbidden sqlite3 in {mod_path}"
                    assert alias.name != "logging", f"Forbidden logging in {mod_path}"
            elif isinstance(node, ast.ImportFrom):
                assert node.module != "sqlite3", f"Forbidden sqlite3 in {mod_path}"
                assert node.module != "logging", f"Forbidden logging in {mod_path}"


def test_diagnostics_py_removed() -> None:
    """Confirm app/host/diagnostics.py has been consolidated into resources.py."""
    diagnostics_path = Path(resources_mod.__file__).resolve().parent / "diagnostics.py"
    assert not diagnostics_path.exists()


# ---------------------------------------------------------------------------
# Worker Allocation Policy Tests: workers = max(1, cpu_cores - 2)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("cpu_cores", "expected_workers"),
    [
        (1, 1),
        (2, 1),
        (3, 1),
        (4, 2),
        (8, 6),
        (12, 10),
        (16, 14),
    ],
)
def test_calculate_worker_allocation_reserve_two_default(
    cpu_cores: int,
    expected_workers: int,
) -> None:
    """Verify default worker allocation policy: workers = max(1, cpu_cores - 2)."""
    workers = calculate_worker_allocation(total_cores=cpu_cores)
    assert workers == expected_workers


def test_calculate_worker_allocation_modes_and_capacity() -> None:
    """Verify single, reserve-one, maximum, custom modes, and get_worker_capacity."""
    assert calculate_worker_allocation(8, mode="single") == 1
    assert calculate_worker_allocation(8, mode="reserve-one") == 7
    assert calculate_worker_allocation(8, mode="all-except-one") == 7
    assert calculate_worker_allocation(8, mode="maximum") == 8
    assert calculate_worker_allocation(8, mode="custom", custom_cores=5) == 5
    assert calculate_worker_allocation(8, mode="custom", custom_cores=99) == 8

    cap = get_worker_capacity(mode="reserve-two")
    assert isinstance(cap, WorkerCapacity)
    assert cap.allocated_workers == max(1, cap.total_cores - 2)

    cap_custom = get_worker_capacity(mode="custom", custom_cores=2)
    assert cap_custom.custom_cores == 2


# ---------------------------------------------------------------------------
# Memory Watchdog (< 15% Available RAM) & Memory Governance Tests
# ---------------------------------------------------------------------------


def _make_mem_obs(available_pct: float) -> MemoryObservation:
    """Build synthetic MemoryObservation for deterministic watchdog tests."""
    total = 16 * (1024**3)
    avail = int(total * (available_pct / 100.0))
    used = total - avail
    used_pct = round(100.0 - available_pct, 2)
    return MemoryObservation(
        total_bytes=total,
        available_bytes=avail,
        used_bytes=used,
        used_pct=used_pct,
        total_mb=round(total / (1024**2), 2),
        available_mb=round(avail / (1024**2), 2),
        is_available=True,
    )


def test_check_memory_headroom_allow_reject_pause() -> None:
    """Verify memory watchdog returns ALLOW >= 15% and REJECT/PAUSE when < 15%."""
    status_ok = check_memory_headroom(
        min_available_pct=MIN_AVAILABLE_RAM_PCT,
        policy="reject",
        memory_obs=_make_mem_obs(40.0),
    )
    assert status_ok.is_pressured is False
    assert status_ok.recommended_action == "ALLOW"
    assert status_ok.available_pct == 40.0

    status_reject = check_memory_headroom(
        min_available_pct=15.0,
        policy="reject",
        memory_obs=_make_mem_obs(11.0),
    )
    assert status_reject.is_pressured is True
    assert status_reject.recommended_action == "REJECT"

    status_pause = check_memory_headroom(
        min_available_pct=15.0,
        policy="pause",
        memory_obs=_make_mem_obs(14.0),
    )
    assert status_pause.is_pressured is True
    assert status_pause.recommended_action == "PAUSE"


def test_memory_watchdog_lifecycle_and_callbacks() -> None:
    """Verify MemoryWatchdog background polling, pressure/recovery callbacks."""
    current_pct = {"val": 35.0}
    pressure_events: list[MemoryWatchdogStatus] = []
    recovery_events: list[MemoryWatchdogStatus] = []

    watchdog = MemoryWatchdog(
        min_available_pct=15.0,
        policy="pause",
        poll_interval_seconds=0.05,
        probe_fn=lambda: _make_mem_obs(current_pct["val"]),
    )
    watchdog.register_callbacks(
        on_pressure=pressure_events.append,
        on_recovery=recovery_events.append,
    )

    assert watchdog.min_available_pct == 15.0
    assert watchdog.policy == "pause"

    # 1. Healthy check (35% >= 15%)
    st1 = watchdog.check()
    assert st1.is_pressured is False
    assert len(pressure_events) == 0

    # 2. Drop below 15% (10% < 15%) -> triggers on_pressure
    current_pct["val"] = 10.0
    st2 = watchdog.check()
    assert st2.is_pressured is True
    assert st2.recommended_action == "PAUSE"
    assert len(pressure_events) == 1

    # 3. Recover above 15% (28% >= 15%) -> triggers on_recovery
    current_pct["val"] = 28.0
    st3 = watchdog.check()
    assert st3.is_pressured is False
    assert len(recovery_events) == 1

    # 4. Background thread start/stop
    watchdog.start()
    watchdog.start()  # idempotent
    time.sleep(0.08)
    watchdog.stop()


def test_dataframe_guard_and_memory_cleanup() -> None:
    """Verify evaluate_dataframe_guard modes ('warn', 'stop', 'off') and cleanup."""
    assert evaluate_dataframe_guard(100_000, max_rows=500_000, mode="warn") == "ALLOW"
    assert evaluate_dataframe_guard(900_000, max_rows=500_000, mode="warn") == "WARN"
    assert evaluate_dataframe_guard(900_000, max_rows=500_000, mode="off") == "ALLOW"

    with pytest.raises(MemoryError, match="exceeds stop limit"):
        evaluate_dataframe_guard(900_000, max_rows=500_000, mode="stop")

    reclaimed = run_memory_cleanup()
    assert isinstance(reclaimed, int)
    assert reclaimed >= 0


# ---------------------------------------------------------------------------
# Hardware, Storage, Database Probes, Benchmark & Scratch Sandbox Tests
# ---------------------------------------------------------------------------


def test_probes_and_error_resilience(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify hardware/storage/DB probes and graceful error handling."""
    HostPersistence.read_records("host_settings")
    (tmp_path / "logs").mkdir(exist_ok=True)
    (tmp_path / "data" / "database").mkdir(parents=True, exist_ok=True)

    health = inspect_resources(root_path=tmp_path)
    assert isinstance(health, HostHealthReport)
    assert health.database.exists is True
    assert health.database.table_count >= 25
    assert health.hardware.cpu_count_logical >= 1

    dirs = inspect_workspace_directories()
    assert isinstance(dirs, dict)

    # Probe error resilience when psutil raises OSError
    def raise_os_error(*_args: object, **_kwargs: object) -> None:
        msg = "simulated telemetry failure"
        raise OSError(msg)

    monkeypatch.setattr(psutil, "cpu_count", raise_os_error)
    assert probe_cpu().is_available is False

    monkeypatch.setattr(psutil, "virtual_memory", raise_os_error)
    assert probe_memory().is_available is False

    monkeypatch.setattr(psutil, "disk_usage", raise_os_error)
    assert probe_disk(tmp_path).is_available is False

    monkeypatch.setattr(psutil, "Process", raise_os_error)
    assert probe_process().is_available is False

    monkeypatch.setattr(HostPersistence, "DEFAULT_DB_PATH", tmp_path / "missing.db")
    assert probe_database().exists is False
    assert probe_storage(tmp_path).workspace_root != ""
    assert probe_hardware().cpu_count_logical >= 1


def test_affinity_gpu_benchmark_and_scratch_sandbox(tmp_path: Path) -> None:
    """Verify CPU affinity, GPU qualification, benchmark, and scratch sandboxes."""
    supported, current_cores = inspect_cpu_affinity()
    assert isinstance(supported, bool)
    assert apply_cpu_affinity([]) is False
    if supported and current_cores:
        assert apply_cpu_affinity(current_cores) is True

    assert isinstance(inspect_gpu_qualification(), bool)

    bench = run_cpu_benchmark(iterations=2_000)
    assert bench.total_ticks == 2_000
    assert bench.throughput_ops_per_sec > 0

    runner = BenchmarkRunner()
    bjob = runner.start_job(iterations=1_000)
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        cur = runner.get_job(bjob.job_id)
        if cur is not None and cur.state in ("completed", "cancelled", "failed"):
            break
        time.sleep(0.02)
    final_bjob = runner.get_job(bjob.job_id)
    assert final_bjob is not None
    assert final_bjob.state == "completed"

    scratch_root = tmp_path / "scratch_root"
    job_dir = allocate_job_scratch("job-123", base_dir=scratch_root)
    assert job_dir.is_dir()
    (job_dir / "temp.bin").write_bytes(b"1234")

    assert cleanup_job_scratch("job-123", base_dir=scratch_root) is True
    assert not job_dir.exists()
    assert cleanup_job_scratch("job-123", base_dir=scratch_root) is False

    with job_scratch_sandbox("job-ctx-99", base_dir=scratch_root) as sdir:
        assert sdir.is_dir()
        (sdir / "artifact.txt").write_text("hello", encoding="utf-8")
    assert not sdir.exists()

    with pytest.raises(ValueError, match="Invalid job_id"):
        allocate_job_scratch("../escape", base_dir=scratch_root)


def test_resource_manager_facade(tmp_path: Path) -> None:
    """Verify ResourceMonitor integrates allocation, watchdog, and sandboxes."""
    HostPersistence.read_records("host_settings")
    rm = ResourceMonitor(
        min_available_ram_pct=15.0,
        watchdog_policy="reject",
        scratch_root=tmp_path / "scratch",
    )
    assert rm.scratch_root == tmp_path / "scratch"
    assert rm.get_worker_allocation(mode="reserve-two") >= 1
    assert rm.check_memory_headroom().threshold_pct == 15.0
    assert rm.inspect_resources(root_path=tmp_path).status in (
        "HEALTHY",
        "DEGRADED",
    )
    with rm.scratch_sandbox("rm-job-1") as sdir:
        assert sdir.is_dir()
    assert not sdir.exists()


# ---------------------------------------------------------------------------
# Persistence Read/Update/Delete Helper Tests
# ---------------------------------------------------------------------------


def test_persistence_job_helpers() -> None:
    """Verify HostPersistence CRUD methods on host_jobs and host_job_events."""
    HostPersistence.update_record(
        "host_jobs",
        pk_values={"job_id": "crud-job-1"},
        updates={
            "owner": "tester",
            "kind": "unit",
            "status": "RUNNING",
            "progress": 25.0,
            "message": "Running unit test",
            "attempt_id": 1,
            "submitted_at_utc": "2026-10-14T12:00:00+00:00",
            "started_at_utc": "2026-10-14T12:00:01+00:00",
        },
        upsert=True,
    )
    HostPersistence.create_record(
        "host_job_events",
        {
            "event_id": "evt-crud-1",
            "job_id": "crud-job-1",
            "from_state": "QUEUED",
            "to_state": "RUNNING",
            "details_json": '{"progress": 25.0}',
            "created_at_utc": "2026-10-14T12:00:01+00:00",
        },
    )

    fetched_rows = HostPersistence.read_records(
        "host_jobs", pk_values={"job_id": "crud-job-1"}, limit=1
    )
    assert len(fetched_rows) == 1
    assert fetched_rows[0]["status"] == "RUNNING"

    running_jobs = HostPersistence.read_records(
        "host_jobs", where={"status": "RUNNING"}
    )
    assert len(running_jobs) == 1

    attempts = HostPersistence.read_records(
        "host_job_attempts", where={"job_id": "crud-job-1"}
    )
    assert isinstance(attempts, list)

    events = HostPersistence.read_records(
        "host_job_events", where={"job_id": "crud-job-1"}
    )
    assert len(events) == 1

    updated = HostPersistence.update_record(
        "host_jobs",
        pk_values={"job_id": "crud-job-1"},
        updates={
            "status": "INTERRUPTED",
            "message": "Interrupted on boot",
            "finished_at_utc": "2026-10-14T12:05:00+00:00",
            "error_message": "Orphaned",
        },
    )
    assert updated == 1

    deleted = HostPersistence.delete_record(
        "host_jobs",
        pk_values={"job_id": "crud-job-1"},
        check_references=False,
    )
    assert deleted == 1
    assert (
        HostPersistence.read_records("host_jobs", pk_values={"job_id": "crud-job-1"})
        == []
    )


# ---------------------------------------------------------------------------
# Multiprocessing JobManager Tests (ProcessPoolExecutor, Cancellation, Watchdog)
# ---------------------------------------------------------------------------


def test_job_manager_process_pool_execution(tmp_path: Path) -> None:
    """Verify JobManager executes CPU tasks in a separate OS worker process."""
    rm = ResourceMonitor(scratch_root=tmp_path / "mp_scratch")

    manager = JobManager(
        max_workers=2,
        resource_mgr=rm,
        use_process_pool=True,
    )
    try:
        assert manager.max_workers == 2
        assert manager.resource_manager is rm
        submitted = manager.submit_job(
            mp_worker_with_context,
            2,
            owner="quant",
            kind="multiprocessing-test",
        )
        completed = manager.wait_for_job(submitted.job_id, timeout=15.0)
        assert completed.status == str(JobState.COMPLETED)
        assert completed.progress == 100.0
        assert completed.result is not None
        assert completed.result["computed"] == 42
        assert completed.result["scratch_exists"] is True
        assert completed.worker_pid is not None
        assert completed.worker_pid != os.getpid()
        assert completed.to_dict()["job_id"] == submitted.job_id

        # Also test worker callable that does not take JobContext
        sub_simple = manager.submit_job(
            mp_worker_without_context,
            19,
            23,
            owner="quant",
            kind="simple-add",
        )
        done_simple = manager.wait_for_job(sub_simple.job_id, timeout=15.0)
        assert done_simple.status == str(JobState.COMPLETED)
        assert done_simple.result == 42
    finally:
        manager.shutdown()


def test_job_manager_cooperative_cancellation_in_process_pool(
    tmp_path: Path,
) -> None:
    """Verify cooperative cancellation via JobContext terminates a running process task."""
    scratch_root = tmp_path / "cancel_scratch"
    rm = ResourceMonitor(scratch_root=scratch_root)

    manager = JobManager(
        max_workers=2,
        resource_mgr=rm,
        use_process_pool=True,
        cleanup_scratch_on_exit=False,
    )
    try:
        record = manager.submit_job(
            mp_cancellable_spin_worker,
            500,
            owner="quant",
            kind="long-simulation",
            job_id="cancel-target-01",
        )
        ready_flag = scratch_root / "cancel-target-01" / "worker_started.flag"
        deadline = time.monotonic() + 10.0
        while not ready_flag.exists() and time.monotonic() < deadline:
            time.sleep(0.02)

        assert manager.cancel_job(record.job_id) is True
        assert manager.cancel_job("nonexistent-job-id") is False

        final_record = manager.wait_for_job(record.job_id, timeout=10.0)
        assert final_record.status == str(JobState.CANCELLED)

        persisted = manager.get_job(record.job_id)
        assert persisted is not None
        assert persisted.status == str(JobState.CANCELLED)
    finally:
        manager.shutdown()


def test_job_manager_task_failure_handling(tmp_path: Path) -> None:
    """Verify worker exceptions transition the job to FAILED and persist error details."""
    rm = ResourceMonitor(scratch_root=tmp_path / "fail_scratch")

    manager = JobManager(
        max_workers=1,
        resource_mgr=rm,
        use_process_pool=False,
    )
    try:
        rec = manager.submit_job(
            mp_failing_worker,
            owner="quant",
            kind="failing-job",
        )
        done = manager.wait_for_job(rec.job_id, timeout=5.0)
        assert done.status == str(JobState.FAILED)
        assert done.error_message is not None
        assert "Simulated worker computation failure" in done.error_message
    finally:
        manager.shutdown()


def test_job_manager_memory_watchdog_reject_and_pause(tmp_path: Path) -> None:
    """Verify JobManager rejects or pauses tasks when available RAM < 15%."""
    simulated_ram = {"pct": 9.5}

    rm = ResourceMonitor(
        min_available_ram_pct=15.0,
        watchdog_policy="reject",
        scratch_root=tmp_path / "mem_scratch",
        probe_memory_fn=lambda: _make_mem_obs(simulated_ram["pct"]),
    )

    # 1. Policy = 'reject': raises MemoryPressureError when RAM < 15%
    reject_mgr = JobManager(
        max_workers=1,
        resource_mgr=rm,
        memory_policy="reject",
        use_process_pool=False,
    )
    try:
        with pytest.raises(MemoryPressureError, match=r"below 15\.0% minimum"):
            reject_mgr.submit_job(
                run_sample_compute_task,
                100,
                job_id="rejected-ram-job",
            )
        rejected_rec = reject_mgr.get_job("rejected-ram-job")
        assert rejected_rec is not None
        assert rejected_rec.status == str(JobState.FAILED)
    finally:
        reject_mgr.shutdown()

    # 2. Policy = 'pause': queues job in PAUSED state until RAM recovers >= 15%
    simulated_ram["pct"] = 12.0
    rm_pause = ResourceMonitor(
        min_available_ram_pct=15.0,
        watchdog_policy="pause",
        scratch_root=tmp_path / "pause_scratch",
        probe_memory_fn=lambda: _make_mem_obs(simulated_ram["pct"]),
    )
    pause_mgr = JobManager(
        max_workers=1,
        resource_mgr=rm_pause,
        memory_policy="pause",
        use_process_pool=False,
    )
    try:
        paused_rec = pause_mgr.submit_job(
            run_sample_compute_task,
            500,
            job_id="paused-ram-job",
        )
        assert paused_rec.status == str(JobState.PAUSED)

        # Still under pressure (11% < 15%) -> resume_paused_jobs does not dispatch yet
        simulated_ram["pct"] = 11.0
        assert pause_mgr.resume_paused_jobs() == []

        # RAM recovers to 45% (>= 15%) -> resume_paused_jobs dispatches and completes
        simulated_ram["pct"] = 45.0
        resumed_ids = pause_mgr.resume_paused_jobs()
        assert resumed_ids == ["paused-ram-job"]
        completed = pause_mgr.wait_for_job("paused-ram-job", timeout=5.0)
        assert completed.status == str(JobState.COMPLETED)

        # Also test cancelling a paused job before it resumes
        simulated_ram["pct"] = 8.0
        paused_to_cancel = pause_mgr.submit_job(
            run_sample_compute_task,
            500,
            job_id="paused-cancel-job",
        )
        assert paused_to_cancel.status == str(JobState.PAUSED)
        assert pause_mgr.cancel_job("paused-cancel-job") is True
        cancelled_rec = pause_mgr.get_job("paused-cancel-job")
        assert cancelled_rec is not None
        assert cancelled_rec.status == str(JobState.CANCELLED)
        paused_at_shutdown = pause_mgr.submit_job(
            run_sample_compute_task, 500, job_id="shutdown-paused-job"
        )
        assert paused_at_shutdown.status == str(JobState.PAUSED)
        pause_mgr.shutdown(wait=True, cancel_futures=True)
        stopped = pause_mgr.get_job("shutdown-paused-job")
        assert stopped is not None
        assert stopped.status == str(JobState.CANCELLED)
    finally:
        pause_mgr.shutdown()


def test_job_manager_startup_orphan_reconciliation(
    tmp_path: Path,
    caplog: LogCaptureFixture,
) -> None:
    """Verify orphan jobs left in RUNNING state are marked INTERRUPTED on boot."""
    rm = ResourceMonitor(scratch_root=tmp_path / "reconcile_scratch")

    # Seed two orphan RUNNING jobs and one COMPLETED job
    HostPersistence.create_record(
        "host_jobs",
        {
            "job_id": "orphan-run-1",
            "owner": "system",
            "kind": "backtest",
            "status": str(JobState.RUNNING),
            "progress": 33.0,
            "message": "In flight before power loss",
            "attempt_id": 1,
            "submitted_at_utc": "2026-10-14T10:00:00+00:00",
            "started_at_utc": "2026-10-14T10:00:02+00:00",
        },
    )
    HostPersistence.create_record(
        "host_jobs",
        {
            "job_id": "orphan-run-2",
            "owner": "system",
            "kind": "wfo",
            "status": str(JobState.RUNNING),
            "progress": 75.0,
            "message": "In flight WFO",
            "attempt_id": 2,
            "submitted_at_utc": "2026-10-14T10:01:00+00:00",
            "started_at_utc": "2026-10-14T10:01:05+00:00",
        },
    )
    HostPersistence.create_record(
        "host_jobs",
        {
            "job_id": "healthy-done-1",
            "owner": "system",
            "kind": "backtest",
            "status": str(JobState.COMPLETED),
            "progress": 100.0,
            "message": "Done",
            "attempt_id": 1,
            "submitted_at_utc": "2026-10-14T09:00:00+00:00",
            "started_at_utc": "2026-10-14T09:00:01+00:00",
            "finished_at_utc": "2026-10-14T09:01:00+00:00",
        },
    )

    manager = JobManager(
        resource_mgr=rm,
        use_process_pool=False,
    )
    try:
        interrupted_ids = manager.reconcile_orphan_jobs()
        assert set(interrupted_ids) == {"orphan-run-1", "orphan-run-2"}

        for job_id in ("orphan-run-1", "orphan-run-2"):
            persisted = manager.get_job(job_id)
            assert persisted is not None
            assert persisted.status == str(JobState.INTERRUPTED)
            assert persisted.finished_at_utc is not None
            events = manager.get_job_events(job_id)
            assert any(e["to_state"] == str(JobState.INTERRUPTED) for e in events)

        completed_job = manager.get_job("healthy-done-1")
        assert completed_job is not None
        assert completed_job.status == str(JobState.COMPLETED)

        all_listed = manager.list_jobs()
        assert len(all_listed) == 3
        assert "FR-HOST-JOBS-RECONCILIATION" in caplog.text
    finally:
        manager.shutdown()


def test_job_context_pause_resume_and_memory_guard(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify JobContext pause/resume markers and check_memory_guard."""
    ctx = JobContext("ctx-unit-1", tmp_path / "ctx_scratch", min_available_ram_pct=15.0)
    assert ctx.is_cancelled() is False
    assert ctx.is_paused() is False

    ctx.set_paused(True)
    assert ctx.is_paused() is True
    ctx.set_paused(False)
    assert ctx.is_paused() is False

    # Memory guard passes when available RAM >= 15%
    monkeypatch.setattr(
        jobs_mod,
        "check_memory_headroom",
        lambda min_pct, *, policy="reject": check_memory_headroom(
            min_pct,
            policy=policy,
            memory_obs=_make_mem_obs(50.0),
        ),
    )
    st_ok = ctx.check_memory_guard(policy="reject")
    assert st_ok.is_pressured is False

    # Memory guard raises MemoryPressureError when available RAM < 15% and policy='reject'
    monkeypatch.setattr(
        jobs_mod,
        "check_memory_headroom",
        lambda min_pct, *, policy="reject": check_memory_headroom(
            min_pct,
            policy=policy,
            memory_obs=_make_mem_obs(10.0),
        ),
    )
    with pytest.raises(MemoryPressureError, match=r"dropped below 15\.0%"):
        ctx.check_memory_guard(policy="reject")

    # Memory guard pauses when policy='pause'
    st_pause = ctx.check_memory_guard(policy="pause")
    assert st_pause.recommended_action == "PAUSE"
    assert ctx.is_paused() is True
    ctx.set_paused(False)

    ctx.cancel()
    assert ctx.is_cancelled() is True
    with pytest.raises(JobCancelledError, match="was cancelled"):
        ctx.raise_if_cancelled()


def test_resources_and_jobs_cli_main_entrypoints(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify CLI main() entrypoints for both resources.py and jobs.py."""
    HostPersistence.read_records("host_settings")
    monkeypatch.setattr(
        resources_mod,
        "DEFAULT_SCRATCH_ROOT",
        tmp_path / "cli_res_scratch",
    )
    monkeypatch.setattr(
        resources_mod,
        "resource_manager",
        ResourceMonitor(scratch_root=tmp_path / "cli_res_scratch"),
    )
    resources_mod.main()

    orig_jm = jobs_mod.JobManager
    monkeypatch.setattr(
        jobs_mod,
        "JobManager",
        lambda **kw: orig_jm(
            resource_mgr=ResourceMonitor(scratch_root=tmp_path / "cli_jobs_scratch"),
            use_process_pool=False,
            **kw,
        ),
    )
    jobs_mod.main()
