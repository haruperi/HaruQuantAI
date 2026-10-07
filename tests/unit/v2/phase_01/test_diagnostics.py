"""Unit tests for app/host/diagnostics.py.

Verifies hardware capacity probes, zero-vs-unavailable metric discrimination,
worker concurrency derivation across core usage modes, thread affinity,
GPU qualification, computational benchmarking with cancellation, and FastAPI
diagnostics REST endpoints.
"""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from unittest.mock import patch

from app.host.diagnostics import (
    BenchmarkRunner,
    apply_thread_affinity,
    calculate_worker_allocation,
    create_diagnostics_router,
    get_worker_capacity,
    inspect_gpu_qualification,
    inspect_thread_affinity,
    probe_cpu,
    probe_disk,
    probe_memory,
    probe_platform,
    probe_process,
    probe_system_diagnostics,
    run_cpu_benchmark,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_probe_cpu_normal_and_failure() -> None:
    """Verify normal CPU probe and graceful fallback when probes raise errors."""
    # Normal probe
    cpu_obs = probe_cpu()
    assert cpu_obs.is_available is True
    assert cpu_obs.total_logical_cores >= 1
    if cpu_obs.utilization_pct is not None:
        assert 0.0 <= cpu_obs.utilization_pct <= 100.0

    # Failure simulation: zero vs unavailable discrimination
    with patch("psutil.cpu_percent", side_effect=OSError("CPU probe error")):
        failed_cpu = probe_cpu()
        assert failed_cpu.is_available is False
        assert failed_cpu.utilization_pct is None
        assert failed_cpu.total_logical_cores >= 1


def test_probe_memory_normal_and_failure() -> None:
    """Verify normal memory probe and fallback when virtual_memory raises."""
    mem_obs = probe_memory()
    assert mem_obs.is_available is True
    assert mem_obs.total_bytes > 0
    assert mem_obs.available_bytes > 0
    assert mem_obs.total_mb > 0
    assert 0.0 <= mem_obs.used_pct <= 100.0

    # Failure simulation
    with patch("psutil.virtual_memory", side_effect=OSError("RAM error")):
        failed_mem = probe_memory()
        assert failed_mem.is_available is False
        assert failed_mem.total_bytes == 0
        assert failed_mem.total_mb == 0.0


def test_probe_disk_normal_and_failure(tmp_path: Path) -> None:
    """Verify storage capacity probe, path sanitization, and fallback."""
    disk_obs = probe_disk(tmp_path)
    assert disk_obs.is_available is True
    assert disk_obs.total_bytes > 0
    assert disk_obs.free_bytes > 0
    assert 0.0 <= disk_obs.free_pct <= 100.0

    # Verify physical path is sanitized
    assert "C:\\Users\\" not in disk_obs.mount_point
    assert "/home/" not in disk_obs.mount_point

    # Failure simulation
    with patch("psutil.disk_usage", side_effect=OSError("Disk error")):
        failed_disk = probe_disk(tmp_path)
        assert failed_disk.is_available is False
        assert failed_disk.total_bytes == 0


def test_probe_process_normal_and_failure() -> None:
    """Verify current host process telemetry and error handling."""
    proc_obs = probe_process()
    assert proc_obs.is_available is True
    assert proc_obs.pid > 0
    assert proc_obs.threads_count >= 1
    assert proc_obs.memory_rss_bytes > 0
    assert proc_obs.memory_rss_mb > 0
    assert proc_obs.uptime_seconds >= 0.0

    # Failure simulation
    with patch("psutil.Process", side_effect=RuntimeError("Process error")):
        failed_proc = probe_process()
        assert failed_proc.is_available is False
        assert failed_proc.memory_rss_bytes == 0


def test_probe_platform() -> None:
    """Verify operating system and Python runtime platform identification."""
    plat = probe_platform()
    assert plat.system != ""
    assert plat.machine != ""
    assert plat.python_version != ""
    assert plat.python_compiler != ""


def test_worker_allocation_modes() -> None:
    """Verify worker concurrency calculations across all core usage modes."""
    # 4 cores system
    assert calculate_worker_allocation(4, mode="single") == 1
    assert calculate_worker_allocation(4, mode="1") == 1
    assert calculate_worker_allocation(4, mode="reserve-one") == 3
    assert calculate_worker_allocation(4, mode="all_except_one") == 3
    assert calculate_worker_allocation(4, mode="maximum") == 4
    assert calculate_worker_allocation(4, mode="all") == 4

    # Custom mode with boundaries
    assert calculate_worker_allocation(4, mode="custom", custom_cores=2) == 2
    assert calculate_worker_allocation(4, mode="custom", custom_cores=10) == 4
    assert calculate_worker_allocation(4, mode="custom", custom_cores=0) == 1

    # Edge case: 1 core system in reserve-one mode must clamp to 1
    assert calculate_worker_allocation(1, mode="reserve-one") == 1


def test_thread_affinity_and_gpu_qualification() -> None:
    """Verify thread affinity inspection/application and GPU qualification."""
    affinity_supported, current_affinity = inspect_thread_affinity()
    assert isinstance(affinity_supported, bool)
    if affinity_supported:
        assert isinstance(current_affinity, list)
        # Apply current affinity should succeed
        assert apply_thread_affinity(current_affinity) is True

    # Empty cores list returns False
    assert apply_thread_affinity([]) is False

    # GPU qualification without CUDA_VISIBLE_DEVICES
    with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": ""}, clear=False):
        assert inspect_gpu_qualification() is False

    # GPU qualification with CUDA_VISIBLE_DEVICES set
    with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "0,1"}, clear=False):
        assert inspect_gpu_qualification() is True


def test_get_worker_capacity() -> None:
    """Verify consolidated worker capacity model."""
    capacity = get_worker_capacity(mode="custom", custom_cores=2)
    assert capacity.total_cores >= 1
    assert capacity.allocated_workers >= 1
    assert capacity.mode == "custom"
    assert capacity.custom_cores == 2
    assert isinstance(capacity.affinity_supported, bool)
    assert isinstance(capacity.gpu_available, bool)


def test_probe_system_diagnostics_snapshot(tmp_path: Path) -> None:
    """Verify consolidated system diagnostics snapshot and degradation flag."""
    snapshot = probe_system_diagnostics(tmp_path)
    assert snapshot.timestamp != ""
    assert snapshot.cpu.is_available is True
    assert snapshot.memory.is_available is True
    assert snapshot.disk.is_available is True
    assert snapshot.process.is_available is True
    assert isinstance(snapshot.is_degraded, bool)

    # Simulated degradation when memory probe fails
    with patch("app.host.diagnostics.probe_memory") as mock_mem:
        from app.host.diagnostics import MemoryObservation

        mock_mem.return_value = MemoryObservation(
            total_bytes=0,
            available_bytes=0,
            used_bytes=0,
            used_pct=0.0,
            total_mb=0.0,
            available_mb=0.0,
            is_available=False,
        )
        degraded_snap = probe_system_diagnostics(tmp_path)
        assert degraded_snap.is_degraded is True


def test_run_cpu_benchmark_real_computation() -> None:
    """Verify deterministic computational CPU benchmark execution."""
    # Run a quick 5,000 tick benchmark
    results = run_cpu_benchmark(iterations=5_000)
    assert results.total_ticks == 5_000
    assert results.duration_seconds > 0.0
    assert results.throughput_ops_per_sec > 0.0
    assert results.time_per_tick_ms > 0.0
    assert results.avg_strategies_per_hour >= 0


def test_run_cpu_benchmark_cooperative_cancellation() -> None:
    """Verify that cooperative cancellation event stops benchmark immediately."""
    cancel_evt = threading.Event()
    cancel_evt.set()  # Pre-signaled

    import pytest

    with pytest.raises(InterruptedError, match="Benchmark cancelled by caller"):
        run_cpu_benchmark(iterations=50_000, cancel_event=cancel_evt)


def test_benchmark_runner_background_lifecycle() -> None:
    """Verify background benchmark runner execution, polling, and cancellation."""
    runner = BenchmarkRunner()

    # Start benchmark
    job = runner.start_job(iterations=100_000)
    assert job.job_id.startswith("bench-")
    assert job.state == "running"

    # Immediately signal cancellation
    cancelled = runner.cancel_job(job.job_id)
    assert cancelled is True

    # Give worker a brief moment to catch cancellation
    time.sleep(0.1)
    updated = runner.get_job(job.job_id)
    assert updated is not None
    assert updated.state in ("cancelled", "completed")


def test_diagnostics_fastapi_router() -> None:
    """Verify FastAPI diagnostics REST endpoints."""
    runner = BenchmarkRunner()
    router = create_diagnostics_router(runner)

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    # 1. System diagnostics
    res_sys = client.get("/api/v1/diagnostics/system")
    assert res_sys.status_code == 200
    data_sys = res_sys.json()
    assert "cpu" in data_sys
    assert "memory" in data_sys
    assert "disk" in data_sys
    assert "process" in data_sys
    assert "worker_capacity" in data_sys

    # 2. Individual probes
    assert client.get("/api/v1/diagnostics/cpu").status_code == 200
    assert client.get("/api/v1/diagnostics/memory").status_code == 200
    assert client.get("/api/v1/diagnostics/disk").status_code == 200
    assert client.get("/api/v1/diagnostics/process").status_code == 200

    # 3. Workers capacity
    res_workers = client.get("/api/v1/diagnostics/workers?mode=custom&custom_cores=2")
    assert res_workers.status_code == 200
    data_workers = res_workers.json()
    assert data_workers["allocated_workers"] >= 1

    # 4. Benchmark execution lifecycle
    res_run = client.post("/api/v1/diagnostics/benchmark/run?iterations=10000")
    assert res_run.status_code == 202
    job_data = res_run.json()
    job_id = job_data["job_id"]

    # Poll status
    res_poll = client.get(f"/api/v1/diagnostics/benchmark/{job_id}")
    assert res_poll.status_code == 200

    # Cancel job
    res_cancel = client.post(f"/api/v1/diagnostics/benchmark/{job_id}/cancel")
    assert res_cancel.status_code == 200

    # Non-existent job
    res_404 = client.get("/api/v1/diagnostics/benchmark/nonexistent_id")
    assert res_404.status_code == 404
