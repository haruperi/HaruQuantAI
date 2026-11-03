"""Deterministic host probes, memory policy, scratch isolation, and benchmarks."""

import threading
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from app.core.host import resources


def memory(available=20, *, total=100, is_available=True):
    return resources.MemoryObservation(
        total,
        available,
        total - available,
        100 * (total - available) / total if total else 80,
        1,
        1,
        is_available,
    )


@pytest.mark.parametrize(
    ("cores", "mode", "custom", "expected"),
    [
        (8, "reserve-two", 1, 6),
        (1, "reserve-two", 1, 1),
        (8, "reserve_one", 1, 7),
        (8, "all_except_one", 1, 7),
        (8, "single", 1, 1),
        (8, "all", 1, 8),
        (8, "maximum", 1, 8),
        (8, "custom", 99, 8),
        (8, "custom", 0, 1),
        (0, "unknown", 1, 1),
    ],
)
def test_worker_allocation(cores, mode, custom, expected):
    assert resources.calculate_worker_allocation(cores, mode, custom) == expected


@pytest.mark.parametrize(
    ("available", "policy", "action"),
    [
        (15, "reject", "ALLOW"),
        (14, "reject", "REJECT"),
        (14, "pause", "PAUSE"),
        (14, "unknown", "REJECT"),
    ],
)
def test_headroom_boundary(available, policy, action):
    status = resources.check_memory_headroom(
        memory_obs=memory(available), policy=policy
    )
    assert status.recommended_action == action
    assert status.is_pressured is (available < 15)
    assert status.available_pct == available


def test_unavailable_memory_and_percentage_fallback():
    assert not resources.check_memory_headroom(
        memory_obs=memory(is_available=False)
    ).is_pressured
    status = resources.check_memory_headroom(memory_obs=memory(0, total=0))
    assert status.available_pct == 20
    assert (
        resources.check_memory_headroom(200, memory_obs=memory()).threshold_pct == 100
    )


def test_watchdog_pressure_recovery_and_thread_cleanup():
    current = [memory(10)]
    watchdog = resources.MemoryWatchdog(probe_fn=lambda: current[0])
    pressure, recovery = Mock(), Mock()
    watchdog.register_callbacks(on_pressure=pressure, on_recovery=recovery)
    watchdog.check()
    assert pressure.call_count == 1
    current[0] = memory(30)
    watchdog.check()
    watchdog.check()
    recovery.assert_called_once()
    assert watchdog.policy == "reject"
    assert watchdog.min_available_pct == 15
    observed = threading.Event()
    watchdog.register_callbacks(on_pressure=lambda _: observed.set())
    current[0] = memory(5)
    try:
        watchdog.start()
        watchdog.start()
        assert observed.wait(2)
    finally:
        watchdog.stop()


@pytest.mark.parametrize("job_id", ["", "..", "../escape", "x/y", "x\\y", "C:escape"])
def test_scratch_rejects_unsafe_ids(tmp_path, job_id):
    with pytest.raises(ValueError, match="Invalid job_id"):
        resources.allocate_job_scratch(job_id, tmp_path)


def test_scratch_sandbox_cleans_up_on_failure_and_preserves_siblings(tmp_path):
    sibling = tmp_path / "unrelated"
    sibling.mkdir()
    with (
        pytest.raises(RuntimeError, match="task failed"),
        resources.job_scratch_sandbox("job-1", tmp_path) as scratch,
    ):
        (scratch / "result").write_text("data")
        raise RuntimeError("task failed")
    assert not (tmp_path / "job-1").exists()
    assert sibling.is_dir()
    assert not resources.cleanup_job_scratch("missing", tmp_path)


def test_cpu_and_memory_probes_and_fallbacks(monkeypatch):
    monkeypatch.setattr(
        resources.psutil, "cpu_count", lambda *, logical: 8 if logical else 4
    )
    monkeypatch.setattr(resources.os, "cpu_count", lambda: 8)
    monkeypatch.setattr(
        resources.psutil, "cpu_freq", lambda: SimpleNamespace(current=2400.123)
    )
    monkeypatch.setattr(resources.psutil, "cpu_percent", lambda **_: 150)
    cpu = resources.probe_cpu()
    assert (
        cpu.logical_cores,
        cpu.physical_cores,
        cpu.frequency_mhz,
        cpu.utilization_pct,
    ) == (8, 4, 2400.12, 100)
    monkeypatch.setattr(
        resources.psutil,
        "virtual_memory",
        lambda: SimpleNamespace(total=2**20, available=2**19, used=2**19, percent=50),
    )
    assert resources.probe_memory().available_mb == 0.5
    monkeypatch.setattr(
        resources.psutil, "cpu_freq", Mock(side_effect=OSError("denied"))
    )
    assert not resources.probe_cpu().is_available
    monkeypatch.setattr(
        resources.psutil, "virtual_memory", Mock(side_effect=OSError("denied"))
    )
    assert not resources.probe_memory().is_available


def test_disk_process_and_affinity_probes(monkeypatch, tmp_path):
    monkeypatch.setattr(
        resources.psutil,
        "disk_usage",
        lambda _: SimpleNamespace(total=100, free=25, used=75),
    )
    assert resources.probe_disk(tmp_path).free_pct == 25
    process = Mock(pid=123)
    process.cpu_percent.return_value = 2.5
    process.memory_info.return_value = SimpleNamespace(rss=2**20)
    process.open_files.side_effect = resources.psutil.AccessDenied(123)
    process.create_time.return_value = 90
    process.num_threads.return_value = 3
    process.cpu_affinity.return_value = [0, 1]
    monkeypatch.setattr(resources.psutil, "Process", lambda: process)
    monkeypatch.setattr(resources.time, "time", lambda: 100)
    observation = resources.probe_process()
    assert observation.pid == 123 and observation.memory_rss_mb == 1
    assert observation.open_files_count is None and observation.uptime_seconds == 10
    assert resources.inspect_cpu_affinity() == (True, [0, 1])
    assert resources.apply_cpu_affinity([1])
    process.cpu_affinity.assert_called_with([1])
    assert not resources.apply_cpu_affinity([])
    process.cpu_affinity.side_effect = resources.psutil.AccessDenied(123)
    assert not resources.apply_cpu_affinity([1])


def test_workspace_storage_and_health_composition(monkeypatch, tmp_path):
    settings = SimpleNamespace(
        workspace_paths={
            "existing": str(tmp_path),
            "missing": str(tmp_path / "missing"),
        }
    )
    assert resources.inspect_workspace_directories(settings) == {
        "existing": True,
        "missing": False,
    }
    monkeypatch.setattr(
        resources.shutil, "disk_usage", lambda _: SimpleNamespace(total=100, free=25)
    )
    storage = resources.probe_storage(tmp_path)
    assert storage.logs_dir_writable and storage.database_dir_writable
    assert not list(tmp_path.rglob(".probe_test"))
    database = resources.DatabaseProbe("db", True, 1, False, 0, None)
    hardware = resources.HardwareProbe(4, 2, 10, 100, 50, 50)
    monkeypatch.setattr(resources, "probe_database", lambda **_: database)
    monkeypatch.setattr(resources, "probe_storage", lambda *_, **__: storage)
    monkeypatch.setattr(resources, "probe_hardware", lambda: hardware)
    report = resources.inspect_resources(tmp_path)
    assert report.status == "HEALTHY"
    assert report.to_dict()["hardware"]["cpu_count_logical"] == 4
    monkeypatch.setattr(
        resources,
        "probe_database",
        lambda **_: resources.DatabaseProbe("db", False, 0, False, 0, 0, "missing"),
    )
    assert resources.inspect_resources(tmp_path).status == "DEGRADED"


def test_database_probe_uses_gateway_and_reports_failure(tmp_path):
    gateway = Mock(database_path=tmp_path / "db")
    assert not resources.probe_database(persistence=gateway).exists
    gateway.database_path.write_bytes(b"database")
    gateway.database_path.with_name("db-wal").write_bytes(b"wal")
    gateway.read_records.return_value = {"success": True}
    result = resources.probe_database(persistence=gateway)
    assert result.exists and result.wal_exists and result.wal_size_bytes == 3
    assert result.error is None and result.table_count is None
    gateway.read_records.return_value = {"success": False}
    assert resources.probe_database(persistence=gateway).error is not None


def test_gpu_detection_and_dataframe_policy(monkeypatch):
    for name in ("CUDA_VISIBLE_DEVICES", "CUDA_PATH", "NVIDIA_VISIBLE_DEVICES"):
        monkeypatch.delenv(name, raising=False)
    assert not resources.inspect_gpu_qualification()
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "-1")
    assert not resources.inspect_gpu_qualification()
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "0")
    assert resources.inspect_gpu_qualification()
    assert resources.evaluate_dataframe_guard(10, max_rows=10) == "ALLOW"
    assert resources.evaluate_dataframe_guard(11, max_rows=10) == "WARN"
    assert resources.evaluate_dataframe_guard(11, max_rows=10, mode="off") == "ALLOW"
    with pytest.raises(MemoryError, match="stop limit"):
        resources.evaluate_dataframe_guard(11, max_rows=10, mode="stop")


def test_cpu_benchmark_and_cancellation():
    result = resources.run_cpu_benchmark(50)
    assert result.total_ticks == 50 and result.throughput_ops_per_sec > 0
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(InterruptedError, match="cancelled"):
        resources.run_cpu_benchmark(50, cancel)


def test_benchmark_runner_completes_without_polling_sleeps(monkeypatch):
    completed = threading.Event()
    real = resources.run_cpu_benchmark

    def benchmark(**kwargs):
        result = real(**kwargs)
        completed.set()
        return result

    monkeypatch.setattr(resources, "run_cpu_benchmark", benchmark)
    # Execute the worker synchronously to inspect final state deterministically.
    monkeypatch.setattr(
        resources.threading,
        "Thread",
        lambda *, target, args, **_: SimpleNamespace(start=lambda: target(*args)),
    )
    runner = resources.BenchmarkRunner()
    job = runner.start_job(25)
    assert completed.is_set()
    assert runner.get_job(job.job_id).state == "completed"
    assert runner.get_job(job.job_id).iterations_completed == 25
    assert runner.get_job("missing") is None
    assert not runner.cancel_job("missing")


def test_get_available_processors(monkeypatch):
    monkeypatch.setattr(
        resources.psutil, "cpu_count", lambda *, logical: 16 if logical else 8
    )
    monkeypatch.setattr(resources.os, "cpu_count", lambda: 8)
    assert resources.get_available_processors() == 16

    monkeypatch.setattr(
        resources.psutil, "cpu_count", lambda *, logical: 4 if logical else 2
    )
    monkeypatch.setattr(resources.os, "cpu_count", lambda: 12)
    assert resources.get_available_processors() == 12

    monkeypatch.setattr(resources.psutil, "cpu_count", lambda *, logical: None)
    monkeypatch.setattr(resources.os, "cpu_count", lambda: None)
    assert resources.get_available_processors() == 1


def test_memory_protection_error_hierarchy():
    assert issubclass(resources.MemoryProtectionError, MemoryError)
    assert issubclass(resources.MemoryProtectionError, RuntimeError)
    err = resources.MemoryProtectionError("memory guard triggered")
    assert isinstance(err, MemoryError)
    assert isinstance(err, RuntimeError)
    assert "memory guard triggered" in str(err)


def test_check_available_memory_thresholds():
    normal_obs = resources.MemoryObservation(
        total_bytes=1000,
        available_bytes=300,
        used_bytes=700,
        used_pct=70.0,
        total_mb=1.0,
        available_mb=0.3,
        is_available=True,
    )
    # Should not raise under normal conditions
    resources.check_available_memory(
        normal_obs,
        over_limit_count=5,
        one_time_limit_pct=90.0,
        consecutive_threshold=15,
    )

    # One-time threshold breach (e.g. 91% > 90%)
    high_obs = resources.MemoryObservation(
        total_bytes=1000,
        available_bytes=90,
        used_bytes=910,
        used_pct=91.0,
        total_mb=1.0,
        available_mb=0.09,
        is_available=True,
    )
    with pytest.raises(
        resources.MemoryProtectionError, match="Memory usage is too high"
    ):
        resources.check_available_memory(
            high_obs,
            over_limit_count=0,
            one_time_limit_pct=90.0,
            consecutive_threshold=15,
        )

    # Consecutive threshold breach (count 16 > 15) even at 85%
    with pytest.raises(
        resources.MemoryProtectionError, match="Memory usage is too high"
    ):
        resources.check_available_memory(
            normal_obs,
            over_limit_count=16,
            one_time_limit_pct=90.0,
            consecutive_threshold=15,
        )


def test_watchdog_over_limit_consecutive_tracking():
    def low_ram_probe():
        return resources.MemoryObservation(
            total_bytes=1000,
            available_bytes=100,
            used_bytes=900,
            used_pct=90.0,
            total_mb=1.0,
            available_mb=0.1,
            is_available=True,
        )

    def healthy_ram_probe():
        return resources.MemoryObservation(
            total_bytes=1000,
            available_bytes=600,
            used_bytes=400,
            used_pct=40.0,
            total_mb=1.0,
            available_mb=0.6,
            is_available=True,
        )

    watchdog = resources.MemoryWatchdog(min_available_pct=15.0, probe_fn=low_ram_probe)
    assert watchdog.over_limit_count == 0

    # First pressured check increments over_limit_count
    st1 = watchdog.check()
    assert st1.is_pressured
    assert watchdog.over_limit_count == 1

    # Second pressured check increments over_limit_count
    st2 = watchdog.check()
    assert st2.is_pressured
    assert watchdog.over_limit_count == 2

    # Recovery resets over_limit_count to 0
    watchdog._probe_fn = healthy_ram_probe
    st3 = watchdog.check()
    assert not st3.is_pressured
    assert watchdog.over_limit_count == 0

    # check_available_memory on watchdog raises when over limit
    watchdog._probe_fn = low_ram_probe
    watchdog.check()
    with pytest.raises(resources.MemoryProtectionError):
        watchdog.check_available_memory(
            one_time_limit_pct=85.0, consecutive_threshold=15
        )


def test_resource_monitor_check_available_memory():
    def high_usage_probe():
        return resources.MemoryObservation(
            total_bytes=1000,
            available_bytes=50,
            used_bytes=950,
            used_pct=95.0,
            total_mb=1.0,
            available_mb=0.05,
            is_available=True,
        )

    monitor = resources.ResourceMonitor(probe_memory_fn=high_usage_probe)
    monitor.check_memory_headroom()
    with pytest.raises(resources.MemoryProtectionError):
        monitor.check_available_memory(one_time_limit_pct=90.0)
