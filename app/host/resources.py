# ruff: noqa: INP001
"""System diagnostics, hardware inspection, memory watchdog, and resource governance.

Description:
    Provides the unified host resource custody and system diagnostics authority
    for the HaruQuantAI workstation. Consolidates read-only SQLite database probes
    (evaluating existence, WAL size, and table inventory), workspace directory
    readiness checks, filesystem storage writability probes, and granular psutil
    hardware telemetry (CPU cores, frequency, load, physical RAM headroom, disk
    space, and Python process health). Enforces the default worker concurrency
    allocation policy (workers = max(1, cpu_cores - 2)) alongside explicit modes,
    manages OS CPU core affinity, safely qualifies GPU acceleration without
    startup blocking, runs deterministic computational CPU benchmarks, operates
    an active Memory Watchdog that rejects or pauses tasks when available system
    RAM drops below 15%, evaluates data-frame/memory cleanup guards, and provisions
    isolated per-job temporary scratch directories.

Purpose:
    FEAT-HOST-RESOURCES: Host system diagnostics, hardware inspection, memory
    watchdog, and resource governance.

Key Capabilities:
    - FR-HOST-RESOURCES-WORKSPACE-DIRS: Inspect configured directory existence
      from settings.workspace_paths.
      Associated: `inspect_workspace_directories()`
      Logging: INFO for available directories; WARNING for absent directories.
    - FR-HOST-RESOURCES-PROBE-DATABASE: Probe database file existence, WAL size,
      and table inventory.
      Associated: `probe_database()`
      Logging: DEBUG on success; WARNING if missing; ERROR on read failure.
    - FR-HOST-RESOURCES-PROBE-CPU: Probe CPU topology, frequency, and load.
      Associated: `probe_cpu()`
      Logging: DEBUG on probe completion; WARNING on telemetry exception.
    - FR-HOST-RESOURCES-PROBE-MEMORY: Probe host physical RAM capacity and headroom.
      Associated: `probe_memory()`
      Logging: DEBUG on probe completion; WARNING on telemetry exception.
    - FR-HOST-RESOURCES-PROBE-DISK: Probe filesystem storage capacity and volume.
      Associated: `probe_disk()`
      Logging: DEBUG on probe completion; WARNING on telemetry exception.
    - FR-HOST-RESOURCES-PROBE-PROCESS: Probe host Python process health and memory.
      Associated: `probe_process()`
      Logging: DEBUG on probe completion; WARNING on telemetry exception.
    - FR-HOST-RESOURCES-PROBE-STORAGE: Check workspace storage write availability.
      Associated: `probe_storage()`
      Logging: DEBUG on storage probe completion.
    - FR-HOST-RESOURCES-PROBE-HARDWARE: Gather host machine hardware telemetry.
      Associated: `probe_hardware()`
      Logging: DEBUG on hardware probe completion.
    - FR-HOST-RESOURCES-PROBE-HEALTH: Aggregate probes into complete health snapshot.
      Associated: `get_system_health()`, `HostHealthReport`
      Logging: INFO on healthy status; WARNING when degraded.
    - FR-HOST-RESOURCES-WORKER-ALLOCATION: Derive worker concurrency limits using
      workers = max(1, cpu_cores - 2) default policy.
      Associated: `calculate_worker_allocation()`, `get_worker_capacity()`
      Logging: INFO on worker allocation and capacity calculation.
    - FR-HOST-RESOURCES-CORE-AFFINITY: Inspect and apply process CPU core affinity.
      Associated: `apply_cpu_affinity()`, `inspect_cpu_affinity()`
      Logging: INFO on affinity applied; WARNING when unsupported or denied.
    - FR-HOST-RESOURCES-GPU-ACCELERATION: Safely inspect GPU acceleration availability.
      Associated: `inspect_gpu_qualification()`
      Logging: DEBUG detailing GPU device detection status.
    - FR-HOST-RESOURCES-BENCHMARK: Execute bounded real computational CPU benchmark.
      Associated: `run_cpu_benchmark()`, `BenchmarkRunner`
      Logging: INFO on benchmark start and completion; never synthesizes fake scores.
    - FR-HOST-RESOURCES-MEMORY-WATCHDOG: Monitor RAM headroom and reject or pause
      tasks when available system RAM drops below 15%, plus data-frame guards.
      Associated: `check_memory_headroom()`, `MemoryWatchdog`,
      `evaluate_dataframe_guard()`, `run_memory_cleanup()`
      Logging: DEBUG when headroom is healthy; WARNING when available RAM < 15%.
    - FR-HOST-RESOURCES-SCRATCH-SANDBOX: Allocate and clean up isolated per-job
      temporary scratch directories.
      Associated: `allocate_job_scratch()`, `cleanup_job_scratch()`,
      `job_scratch_sandbox()`, `ResourceManager`
      Logging: INFO on scratch sandbox allocation and cleanup; ERROR on traversal.

Python API Usage:
    ```python
    from app.host.resources import (
        calculate_worker_allocation,
        check_memory_headroom,
        get_system_health,
        job_scratch_sandbox,
        probe_hardware,
        resource_manager,
    )

    # 1. Derive worker pool size using max(1, cpu_cores - 2)
    hw = probe_hardware()
    workers = calculate_worker_allocation(hw.cpu_count_logical)

    # 2. Verify available system RAM headroom (>= 15%)
    watchdog_status = check_memory_headroom(min_available_pct=15.0)

    # 3. Provision and clean up an isolated per-job scratch directory
    with job_scratch_sandbox("job-001") as scratch_dir:
        health = resource_manager.get_system_health()
    ```

CLI Usage:
    ```bash
    uv run python -m app.host.resources
    ```
"""

from __future__ import annotations

import gc
import math
import os
import platform
import shutil
import threading
import time
import uuid
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psutil
from app.host.logging import get_logger, normalize_path
from app.host.persistence.create import DEFAULT_DB_PATH
from app.host.persistence.read import count_database_tables

__all__ = [
    "MemoryWatchdog",
    "ResourceManager",
    "allocate_job_scratch",
    "apply_cpu_affinity",
    "calculate_worker_allocation",
    "check_memory_headroom",
    "cleanup_job_scratch",
    "evaluate_dataframe_guard",
    "get_system_health",
    "get_worker_capacity",
    "inspect_workspace_directories",
    "job_scratch_sandbox",
    "probe_hardware",
    "resource_manager",
    "run_cpu_benchmark",
]

logger = get_logger(__name__)

WORKSPACE_DIRS_FR = "FR-HOST-RESOURCES-WORKSPACE-DIRS"
PROBE_DATABASE_FR = "FR-HOST-RESOURCES-PROBE-DATABASE"
PROBE_CPU_FR = "FR-HOST-RESOURCES-PROBE-CPU"
PROBE_MEMORY_FR = "FR-HOST-RESOURCES-PROBE-MEMORY"
PROBE_DISK_FR = "FR-HOST-RESOURCES-PROBE-DISK"
PROBE_PROCESS_FR = "FR-HOST-RESOURCES-PROBE-PROCESS"
PROBE_STORAGE_FR = "FR-HOST-RESOURCES-PROBE-STORAGE"
PROBE_HARDWARE_FR = "FR-HOST-RESOURCES-PROBE-HARDWARE"
PROBE_HEALTH_FR = "FR-HOST-RESOURCES-PROBE-HEALTH"
DIAGNOSTICS_FR = PROBE_HEALTH_FR
WORKER_ALLOCATION_FR = "FR-HOST-RESOURCES-WORKER-ALLOCATION"
WORKER_CAPACITY_FR = WORKER_ALLOCATION_FR
CORE_AFFINITY_FR = "FR-HOST-RESOURCES-CORE-AFFINITY"
GPU_ACCELERATION_FR = "FR-HOST-RESOURCES-GPU-ACCELERATION"
BENCHMARK_FR = "FR-HOST-RESOURCES-BENCHMARK"
MEMORY_WATCHDOG_FR = "FR-HOST-RESOURCES-MEMORY-WATCHDOG"
SCRATCH_SANDBOX_FR = "FR-HOST-RESOURCES-SCRATCH-SANDBOX"

MIN_FREE_DISK_PCT: float = 2.0
MIN_AVAILABLE_RAM_PCT: float = 15.0
DEFAULT_SCRATCH_ROOT: Path = Path("data/scratch")
BENCHMARK_CHECK_INTERVAL: int = 10_000


@dataclass(frozen=True)
class DatabaseProbe:
    """Diagnostic metrics for active persistence database."""

    path: str
    exists: bool
    size_bytes: int
    wal_exists: bool
    wal_size_bytes: int
    table_count: int
    error: str | None = None


@dataclass(frozen=True)
class StorageProbe:
    """Storage availability and capacity metrics."""

    workspace_root: str
    logs_dir_writable: bool
    database_dir_writable: bool
    free_bytes: int
    total_bytes: int
    free_pct: float


@dataclass(frozen=True)
class HardwareProbe:
    """Host machine hardware topology and utilization."""

    cpu_count_logical: int
    cpu_count_physical: int | None
    cpu_percent: float
    ram_total_bytes: int
    ram_available_bytes: int
    ram_used_pct: float


@dataclass(frozen=True)
class CpuObservation:
    """Observation of host CPU topology and measured load."""

    logical_cores: int
    physical_cores: int | None
    frequency_mhz: float | None
    utilization_pct: float | None
    is_available: bool


@dataclass(frozen=True)
class MemoryObservation:
    """Observation of host physical RAM capacity and headroom."""

    total_bytes: int
    available_bytes: int
    used_bytes: int
    used_pct: float
    total_mb: float
    available_mb: float
    is_available: bool


@dataclass(frozen=True)
class DiskObservation:
    """Observation of filesystem volume capacity and free space."""

    mount_point: str
    total_bytes: int
    free_bytes: int
    used_bytes: int
    free_pct: float
    is_available: bool


@dataclass(frozen=True)
class ProcessObservation:
    """Observation of host Python process health, memory, and threads."""

    pid: int
    cpu_pct: float | None
    memory_rss_bytes: int
    memory_rss_mb: float
    threads_count: int
    open_files_count: int | None
    uptime_seconds: float
    is_available: bool


@dataclass(frozen=True)
class WorkerCapacity:
    """Worker pool concurrency limit, core affinity, and accelerator status."""

    total_cores: int
    allocated_workers: int
    mode: str
    custom_cores: int | None
    affinity_supported: bool
    affinity_active: bool
    gpu_available: bool


@dataclass(frozen=True)
class MemoryWatchdogStatus:
    """Snapshot of system RAM headroom evaluated against the watchdog threshold."""

    available_pct: float
    used_pct: float
    available_bytes: int
    total_bytes: int
    threshold_pct: float
    is_pressured: bool
    recommended_action: str
    timestamp_utc: str


@dataclass(frozen=True)
class BenchmarkResults:
    """Measured performance metrics from an executed CPU benchmark."""

    duration_seconds: float
    total_ticks: int
    avg_strategies_per_hour: int
    time_per_tick_ms: float
    throughput_ops_per_sec: float


@dataclass(frozen=True)
class BenchmarkJob:
    """State tracking for synchronous or background benchmark jobs."""

    job_id: str
    state: str
    progress_pct: float
    started_at: str | None
    completed_at: str | None
    duration_seconds: float | None
    iterations_completed: int
    throughput_ops_per_sec: float | None
    results: BenchmarkResults | None
    error_message: str | None
    metadata: dict[str, Any]


@dataclass(frozen=True)
class HostHealthReport:
    """Comprehensive host platform health and telemetry snapshot."""

    status: str
    database: DatabaseProbe
    storage: StorageProbe
    hardware: HardwareProbe
    timestamp_utc: str

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return asdict(self)


# ============================================================================
# 1. Workspace Directory Inspection
# ============================================================================


def _extract_workspace_paths(settings: Any = None) -> dict[str, str]:
    """Resolve directory paths mapping from host settings or defaults."""
    effective_settings = settings
    if effective_settings is None:
        try:
            from app.host.settings import settings as host_settings

            effective_settings = host_settings
        except ImportError, AttributeError:
            effective_settings = None

    if effective_settings is not None:
        ws_node = getattr(effective_settings, "workspace_paths", None)
        if ws_node is not None:
            if hasattr(ws_node, "as_dict"):
                return dict(ws_node.as_dict())
            if isinstance(ws_node, dict):
                return dict(ws_node)

    return {
        "configs_dir": "data/presets",
        "data_dir": "data/market",
        "projects_dir": "data/projects",
        "strategies_dir": "data/strategies",
    }


def inspect_workspace_directories(
    settings: Any = None,
) -> dict[str, bool]:
    """Inspect existence of directories configured in settings.workspace_paths.

    Args:
        settings: Optional HostSettings instance. If omitted, resolves shared
            host settings singleton if available.

    Returns:
        Mapping of directory key names to boolean existence status.
    """
    paths_dict = _extract_workspace_paths(settings)
    results: dict[str, bool] = {}
    for dir_name, dir_path in sorted(paths_dict.items()):
        p = Path(dir_path).resolve()
        exists = p.exists() and p.is_dir()
        results[dir_name] = exists
        sanitized_path = normalize_path(str(p))
        if exists:
            logger.info(
                "%s: workspace directory '%s' is available at %s",
                WORKSPACE_DIRS_FR,
                dir_name,
                sanitized_path,
                extra={
                    "fr_id": WORKSPACE_DIRS_FR,
                    "directory": dir_name,
                    "path": sanitized_path,
                    "status": "AVAILABLE",
                },
            )
        else:
            logger.warning(
                "%s: workspace directory '%s' is absent at %s",
                WORKSPACE_DIRS_FR,
                dir_name,
                sanitized_path,
                extra={
                    "fr_id": WORKSPACE_DIRS_FR,
                    "directory": dir_name,
                    "path": sanitized_path,
                    "status": "ABSENT",
                },
            )

    return results


# ============================================================================
# 2. Granular Probe Functions
# ============================================================================


def probe_database(
    db_path: Path | str | None = None,
    settings: Any = None,
) -> DatabaseProbe:
    """Perform read-only diagnostic inspection on active database.

    Args:
        db_path: Path to database or None for default from host settings.
        settings: Optional HostSettings instance for configured path resolution.

    Returns:
        DatabaseProbe capturing persistence health.
    """
    if db_path is not None:
        target = Path(db_path)
    elif settings is not None and settings.get("workspace_paths", "db_path"):
        target = Path(settings.get("workspace_paths", "db_path"))
    else:
        target = DEFAULT_DB_PATH
    path_str = normalize_path(str(target))

    if not target.exists():
        logger.warning(
            "%s: database not found at %s",
            PROBE_DATABASE_FR,
            path_str,
            extra={"fr_id": PROBE_DATABASE_FR, "path": path_str},
        )
        return DatabaseProbe(
            path=path_str,
            exists=False,
            size_bytes=0,
            wal_exists=False,
            wal_size_bytes=0,
            table_count=0,
            error="Database file does not exist",
        )

    wal_file = target.with_name(f"{target.name}-wal")
    size_bytes = target.stat().st_size
    wal_exists = wal_file.exists()
    wal_size = wal_file.stat().st_size if wal_exists else 0

    table_count = 0
    err_msg: str | None = None
    try:
        table_count = count_database_tables(target)
    except Exception as err:
        err_msg = str(err)
        logger.exception(
            "%s: database read failed on %s",
            PROBE_DATABASE_FR,
            path_str,
            extra={"fr_id": PROBE_DATABASE_FR, "error": str(err)},
        )

    logger.debug(
        "%s: probed database at %s (tables=%d, size=%d)",
        PROBE_DATABASE_FR,
        path_str,
        table_count,
        size_bytes,
        extra={"fr_id": PROBE_DATABASE_FR, "table_count": table_count},
    )

    return DatabaseProbe(
        path=path_str,
        exists=True,
        size_bytes=size_bytes,
        wal_exists=wal_exists,
        wal_size_bytes=wal_size,
        table_count=table_count,
        error=err_msg,
    )


def probe_cpu() -> CpuObservation:
    """Probe host CPU topology, frequency, and current load.

    Returns:
        CpuObservation detailing logical/physical core counts and load.
    """
    try:
        logical = psutil.cpu_count(logical=True) or 1
        physical = psutil.cpu_count(logical=False)
        freq_info = psutil.cpu_freq()
        freq_val = round(float(freq_info.current), 2) if freq_info else None
        util = psutil.cpu_percent(interval=None)
        util_val = round(max(0.0, min(100.0, float(util))), 2)

        logger.debug(
            "%s: CPU probe succeeded (cores=%d, util=%.1f%%)",
            PROBE_CPU_FR,
            logical,
            util_val,
            extra={"fr_id": PROBE_CPU_FR, "cores": logical, "util": util_val},
        )
        return CpuObservation(
            logical_cores=logical,
            physical_cores=physical,
            frequency_mhz=freq_val,
            utilization_pct=util_val,
            is_available=True,
        )
    except (psutil.Error, OSError, ValueError, TypeError) as exc:
        logger.warning(
            "%s: CPU telemetry probe failed: %s",
            PROBE_CPU_FR,
            str(exc),
            extra={"fr_id": PROBE_CPU_FR, "error": str(exc)},
        )
        fallback = os.cpu_count() or 1
        return CpuObservation(
            logical_cores=fallback,
            physical_cores=None,
            frequency_mhz=None,
            utilization_pct=None,
            is_available=False,
        )


def probe_memory() -> MemoryObservation:
    """Probe physical host memory capacity and current availability.

    Returns:
        MemoryObservation with byte and megabyte units and availability flag.
    """
    try:
        mem = psutil.virtual_memory()
        total_b = mem.total
        avail_b = mem.available
        used_b = mem.used
        used_pct = round(max(0.0, min(100.0, float(mem.percent))), 2)
        total_mb = round(total_b / (1024 * 1024), 2)
        avail_mb = round(avail_b / (1024 * 1024), 2)

        logger.debug(
            "%s: memory probe succeeded (total=%.0fMB, avail=%.0fMB)",
            PROBE_MEMORY_FR,
            total_mb,
            avail_mb,
            extra={"fr_id": PROBE_MEMORY_FR, "total_mb": total_mb},
        )
        return MemoryObservation(
            total_bytes=total_b,
            available_bytes=avail_b,
            used_bytes=used_b,
            used_pct=used_pct,
            total_mb=total_mb,
            available_mb=avail_mb,
            is_available=True,
        )
    except (psutil.Error, OSError, ValueError, TypeError) as exc:
        logger.warning(
            "%s: memory telemetry probe failed: %s",
            PROBE_MEMORY_FR,
            str(exc),
            extra={"fr_id": PROBE_MEMORY_FR, "error": str(exc)},
        )
        return MemoryObservation(
            total_bytes=0,
            available_bytes=0,
            used_bytes=0,
            used_pct=0.0,
            total_mb=0.0,
            available_mb=0.0,
            is_available=False,
        )


def probe_disk(target_path: Path | str = ".") -> DiskObservation:
    """Probe storage capacity for target volume with path sanitization.

    Args:
        target_path: Path on the storage volume to inspect.

    Returns:
        DiskObservation with sanitized mount identifier and byte metrics.
    """
    path_obj = Path(target_path).resolve()
    sanitized_mount = normalize_path(str(path_obj.anchor or path_obj))
    try:
        disk = psutil.disk_usage(str(path_obj))
        total_b = disk.total
        free_b = disk.free
        used_b = disk.used
        free_pct = (
            round(max(0.0, min(100.0, (free_b / total_b) * 100.0)), 2)
            if total_b > 0
            else 0.0
        )

        logger.debug(
            "%s: disk probe succeeded (mount=%s, free_pct=%.1f%%)",
            PROBE_DISK_FR,
            sanitized_mount,
            free_pct,
            extra={"fr_id": PROBE_DISK_FR, "free_pct": free_pct},
        )
        return DiskObservation(
            mount_point=sanitized_mount,
            total_bytes=total_b,
            free_bytes=free_b,
            used_bytes=used_b,
            free_pct=free_pct,
            is_available=True,
        )
    except (psutil.Error, OSError, ValueError, TypeError) as exc:
        logger.warning(
            "%s: disk telemetry probe failed: %s",
            PROBE_DISK_FR,
            str(exc),
            extra={"fr_id": PROBE_DISK_FR, "error": str(exc)},
        )
        return DiskObservation(
            mount_point=sanitized_mount,
            total_bytes=0,
            free_bytes=0,
            used_bytes=0,
            free_pct=0.0,
            is_available=False,
        )


def probe_process() -> ProcessObservation:
    """Probe current host Python process health, memory, and threads.

    Returns:
        ProcessObservation detailing process resources and uptime.
    """
    try:
        p = psutil.Process()
        pid = p.pid
        cpu = p.cpu_percent(interval=None)
        cpu_val = round(max(0.0, float(cpu)), 2)
        mem_info = p.memory_info()
        rss_bytes = mem_info.rss
        rss_mb = round(rss_bytes / (1024 * 1024), 2)
        threads = p.num_threads()

        open_files: int | None = None
        try:
            open_files = len(p.open_files())
        except psutil.AccessDenied, OSError:
            open_files = None

        create_time = p.create_time()
        uptime = max(0.0, round(time.time() - create_time, 2))

        logger.debug(
            "%s: process probe succeeded (pid=%d, rss=%.1fMB)",
            PROBE_PROCESS_FR,
            pid,
            rss_mb,
            extra={"fr_id": PROBE_PROCESS_FR, "pid": pid},
        )
        return ProcessObservation(
            pid=pid,
            cpu_pct=cpu_val,
            memory_rss_bytes=rss_bytes,
            memory_rss_mb=rss_mb,
            threads_count=threads,
            open_files_count=open_files,
            uptime_seconds=uptime,
            is_available=True,
        )
    except (psutil.Error, OSError, ValueError, TypeError) as exc:
        logger.warning(
            "%s: process telemetry probe failed: %s",
            PROBE_PROCESS_FR,
            str(exc),
            extra={"fr_id": PROBE_PROCESS_FR, "error": str(exc)},
        )
        return ProcessObservation(
            pid=os.getpid(),
            cpu_pct=None,
            memory_rss_bytes=0,
            memory_rss_mb=0.0,
            threads_count=1,
            open_files_count=None,
            uptime_seconds=0.0,
            is_available=False,
        )


def probe_storage(
    root_path: Path | str | None = None,
    settings: Any = None,
) -> StorageProbe:
    """Check filesystem write permissions and disk space capacity.

    Args:
        root_path: Workspace root directory or None for cwd.
        settings: Optional HostSettings instance for configured path resolution.

    Returns:
        StorageProbe capturing filesystem status.
    """
    if root_path is not None:
        root = Path(root_path).resolve()
        data_dir = root / "data"
    elif settings is not None and settings.get("workspace_paths", "data_dir"):
        data_dir = Path(settings.get("workspace_paths", "data_dir")).resolve()
        root = (
            data_dir.parent.resolve()
            if data_dir.name == "data"
            else Path.cwd().resolve()
        )
    else:
        root = Path.cwd().resolve()
        data_dir = root / "data"

    logs_dir = data_dir / "logs"
    db_dir = data_dir / "database"

    logs_writable = False
    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
        test_file = logs_dir / ".probe_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        logs_writable = True
    except OSError:
        pass

    db_writable = False
    try:
        db_dir.mkdir(parents=True, exist_ok=True)
        test_file = db_dir / ".probe_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        db_writable = True
    except OSError:
        pass

    usage = shutil.disk_usage(root)
    free_pct = (usage.free / usage.total * 100.0) if usage.total > 0 else 0.0

    logger.debug(
        "%s: probed storage at %s (logs_ok=%s, db_ok=%s, free_pct=%.1f)",
        PROBE_STORAGE_FR,
        normalize_path(str(root)),
        logs_writable,
        db_writable,
        free_pct,
        extra={"fr_id": PROBE_STORAGE_FR, "free_pct": free_pct},
    )

    return StorageProbe(
        workspace_root=normalize_path(str(root)),
        logs_dir_writable=logs_writable,
        database_dir_writable=db_writable,
        free_bytes=usage.free,
        total_bytes=usage.total,
        free_pct=round(free_pct, 2),
    )


def probe_hardware() -> HardwareProbe:
    """Gather machine hardware metrics via psutil.

    Returns:
        HardwareProbe with CPU and memory usage statistics.
    """
    cpu = probe_cpu()
    mem = probe_memory()

    logger.debug(
        "%s: probed hardware (cpus=%d, ram_pct=%.1f)",
        PROBE_HARDWARE_FR,
        cpu.logical_cores,
        mem.used_pct,
        extra={
            "fr_id": PROBE_HARDWARE_FR,
            "cpu_percent": cpu.utilization_pct or 0.0,
        },
    )

    return HardwareProbe(
        cpu_count_logical=cpu.logical_cores,
        cpu_count_physical=cpu.physical_cores,
        cpu_percent=cpu.utilization_pct or 0.0,
        ram_total_bytes=mem.total_bytes,
        ram_available_bytes=mem.available_bytes,
        ram_used_pct=mem.used_pct,
    )


def get_system_health(
    db_path: Path | str | None = None,
    root_path: Path | str | None = None,
    settings: Any = None,
) -> HostHealthReport:
    """Coordinate host probes and generate complete health snapshot.

    Args:
        db_path: Path to database or None for default.
        root_path: Workspace root directory or None for cwd.
        settings: Optional HostSettings instance for configured path resolution.

    Returns:
        HostHealthReport summarizing workstation health.
    """
    db_info = probe_database(db_path, settings=settings)
    storage_info = probe_storage(root_path, settings=settings)
    hw_info = probe_hardware()

    is_healthy = (
        db_info.exists
        and db_info.error is None
        and storage_info.logs_dir_writable
        and storage_info.database_dir_writable
        and storage_info.free_pct > MIN_FREE_DISK_PCT
    )

    status = "HEALTHY" if is_healthy else "DEGRADED"

    report = HostHealthReport(
        status=status,
        database=db_info,
        storage=storage_info,
        hardware=hw_info,
        timestamp_utc=datetime.now(UTC).isoformat(),
    )

    if is_healthy:
        logger.info(
            "%s: host health status is %s (tables=%s, free_gb=%.1f)",
            PROBE_HEALTH_FR,
            status,
            db_info.table_count,
            storage_info.free_bytes / (1024**3),
            extra={"fr_id": PROBE_HEALTH_FR, "status": status},
        )
    else:
        logger.warning(
            "%s: host health status is %s (db_err=%s, logs_ok=%s, db_ok=%s)",
            PROBE_HEALTH_FR,
            status,
            db_info.error,
            storage_info.logs_dir_writable,
            storage_info.database_dir_writable,
            extra={"fr_id": PROBE_HEALTH_FR, "status": status},
        )

    return report


# ============================================================================
# 3. Worker Concurrency Limit Derivation (workers = max(1, cpu_cores - 2))
# ============================================================================


def calculate_worker_allocation(
    total_cores: int,
    mode: str = "reserve-two",
    custom_cores: int = 1,
) -> int:
    """Derive worker pool allocation from total logical cores and selected mode.

    Default core allocation policy: workers = max(1, cpu_cores - 2).

    Modes:
        - 'reserve-two' / 'default' / 'auto': Uses max(1, total_cores - 2).
        - 'reserve-one' / 'all-except-one' / 'all_except_one':
          Uses max(1, total_cores - 1).
        - 'single' / '1': Uses exactly 1 worker.
        - 'maximum' / 'all': Uses max(1, total_cores).
        - 'custom': Uses custom_cores clamped between 1 and total_cores.

    Args:
        total_cores: Total available logical CPU cores.
        mode: Concurrency policy mode string (defaults to 'reserve-two').
        custom_cores: User-specified core count when mode is 'custom'.

    Returns:
        Integer worker allocation, guaranteed >= 1.
    """
    safe_cores = max(1, total_cores)
    normalized_mode = mode.strip().lower().replace("_", "-")

    if normalized_mode in ("single", "1"):
        allocation = 1
    elif normalized_mode in ("maximum", "all"):
        allocation = safe_cores
    elif normalized_mode in ("reserve-one", "all-except-one"):
        allocation = max(1, safe_cores - 1)
    elif normalized_mode == "custom":
        allocation = min(max(1, custom_cores), safe_cores)
    else:
        allocation = max(1, safe_cores - 2)

    logger.info(
        "%s: derived worker allocation (cores=%d, mode='%s', custom=%d -> %d)",
        WORKER_ALLOCATION_FR,
        safe_cores,
        mode,
        custom_cores,
        allocation,
        extra={
            "fr_id": WORKER_ALLOCATION_FR,
            "cores": safe_cores,
            "mode": mode,
            "allocation": allocation,
        },
    )
    return allocation


def get_worker_capacity(
    settings: Any = None,
    mode: str | None = None,
    custom_cores: int | None = None,
) -> WorkerCapacity:
    """Derive consolidated worker capacity, CPU core affinity, and GPU status.

    Args:
        settings: Optional HostSettings instance for configured CPU mode resolution.
        mode: Explicit core allocation mode override.
        custom_cores: Explicit custom cores count override.

    Returns:
        WorkerCapacity model detailing allocated workers and capabilities.
    """
    effective_settings = settings
    if effective_settings is None and (mode is None or custom_cores is None):
        try:
            from app.host.settings import settings as host_settings

            effective_settings = host_settings
        except ImportError, AttributeError:
            effective_settings = None

    effective_mode = mode
    effective_custom = custom_cores

    if effective_settings is not None:
        config_cpu = getattr(effective_settings, "config_cpu", None)
        if config_cpu is not None:
            if effective_mode is None and hasattr(config_cpu, "core_usage"):
                effective_mode = str(config_cpu.core_usage)
            if effective_custom is None and hasattr(config_cpu, "custom_cores"):
                effective_custom = int(config_cpu.custom_cores)

    if effective_mode is None:
        effective_mode = "reserve-two"
    if effective_custom is None:
        effective_custom = 1

    cpu_obs = probe_cpu()
    total_cores = cpu_obs.logical_cores
    allocated = calculate_worker_allocation(
        total_cores=total_cores,
        mode=effective_mode,
        custom_cores=effective_custom,
    )
    aff_supported, aff_current = inspect_cpu_affinity()
    aff_active = aff_supported and aff_current is not None
    gpu_available = inspect_gpu_qualification()

    logger.info(
        "%s: worker capacity resolved (workers=%d/%d, mode='%s', gpu=%s)",
        WORKER_CAPACITY_FR,
        allocated,
        total_cores,
        effective_mode,
        gpu_available,
        extra={
            "fr_id": WORKER_CAPACITY_FR,
            "allocated_workers": allocated,
            "total_cores": total_cores,
            "gpu_available": gpu_available,
        },
    )

    return WorkerCapacity(
        total_cores=total_cores,
        allocated_workers=allocated,
        mode=effective_mode,
        custom_cores=effective_custom
        if effective_mode.lower().replace("_", "-") == "custom"
        else None,
        affinity_supported=aff_supported,
        affinity_active=aff_active,
        gpu_available=gpu_available,
    )


# ============================================================================
# 4. CPU Core Affinity Inspection and Application
# ============================================================================


def inspect_cpu_affinity() -> tuple[bool, list[int] | None]:
    """Inspect if CPU core affinity is supported on current OS.

    Returns:
        Tuple of (affinity_supported, current_affinity_cores_or_None).
    """
    try:
        p = psutil.Process()
        if hasattr(p, "cpu_affinity"):
            current = list(p.cpu_affinity())
            logger.debug(
                "%s: CPU affinity supported on process (current=%r)",
                CORE_AFFINITY_FR,
                current,
                extra={"fr_id": CORE_AFFINITY_FR, "affinity": current},
            )
            return True, current
        logger.debug(
            "%s: CPU affinity is unsupported on %s",
            CORE_AFFINITY_FR,
            platform.system(),
            extra={"fr_id": CORE_AFFINITY_FR},
        )
        return False, None
    except (AttributeError, OSError, psutil.AccessDenied) as exc:
        logger.debug(
            "%s: CPU affinity inspection exception: %s",
            CORE_AFFINITY_FR,
            str(exc),
            extra={"fr_id": CORE_AFFINITY_FR},
        )
        return False, None


def apply_cpu_affinity(cores: list[int]) -> bool:
    """Apply CPU core affinity to the host process if supported by OS.

    Args:
        cores: List of integer core indexes to bind to.

    Returns:
        True if affinity was successfully applied, False otherwise.
    """
    if not cores:
        logger.warning(
            "%s: empty core list provided for affinity application",
            CORE_AFFINITY_FR,
            extra={"fr_id": CORE_AFFINITY_FR},
        )
        return False
    try:
        p = psutil.Process()
        if hasattr(p, "cpu_affinity"):
            p.cpu_affinity(cores)
            logger.info(
                "%s: applied CPU core affinity to %r",
                CORE_AFFINITY_FR,
                cores,
                extra={"fr_id": CORE_AFFINITY_FR, "cores": cores},
            )
            return True
        logger.warning(
            "%s: CPU affinity is unsupported on %s",
            CORE_AFFINITY_FR,
            platform.system(),
            extra={"fr_id": CORE_AFFINITY_FR},
        )
        return False
    except (psutil.Error, OSError, ValueError) as exc:
        logger.warning(
            "%s: failed applying CPU affinity to %r: %s",
            CORE_AFFINITY_FR,
            cores,
            str(exc),
            extra={"fr_id": CORE_AFFINITY_FR, "cores": cores},
        )
        return False


# ============================================================================
# 5. Safe GPU Acceleration Detection
# ============================================================================


def inspect_gpu_qualification() -> bool:
    """Safely inspect if qualified GPU acceleration is available.

    Checks device presence without importing heavy or blocking external packages.
    Guaranteed never to crash or block host startup.

    Returns:
        True if GPU acceleration capability is detected, False otherwise.
    """
    is_available = False
    cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    if cuda_visible and cuda_visible.strip() not in ("-1", "none", "NONE"):
        is_available = True

    if not is_available and (
        os.environ.get("CUDA_PATH") or os.environ.get("NVIDIA_VISIBLE_DEVICES")
    ):
        is_available = True

    logger.debug(
        "%s: GPU detection inspected: available=%s",
        GPU_ACCELERATION_FR,
        is_available,
        extra={"fr_id": GPU_ACCELERATION_FR, "available": is_available},
    )
    return is_available


# ============================================================================
# 6. Active Memory Watchdog & Data-Frame / Cleanup Guards
# ============================================================================


def check_memory_headroom(
    min_available_pct: float = MIN_AVAILABLE_RAM_PCT,
    *,
    policy: str = "reject",
    memory_obs: MemoryObservation | None = None,
) -> MemoryWatchdogStatus:
    """Evaluate available system RAM against the 15% memory watchdog threshold.

    Args:
        min_available_pct: Minimum required available system RAM percentage
            (default: 15.0%).
        policy: Enforcement action when available RAM drops below threshold
            ('reject' or 'pause').
        memory_obs: Optional pre-captured MemoryObservation for deterministic
            evaluation.

    Returns:
        MemoryWatchdogStatus detailing current headroom and enforcement action.
    """
    obs = memory_obs if memory_obs is not None else probe_memory()
    threshold = max(0.0, min(100.0, float(min_available_pct)))

    if obs.is_available and obs.total_bytes > 0:
        avail_pct = round(
            max(0.0, min(100.0, (obs.available_bytes / obs.total_bytes) * 100.0)),
            2,
        )
    elif obs.is_available:
        avail_pct = round(max(0.0, min(100.0, 100.0 - obs.used_pct)), 2)
    else:
        avail_pct = 100.0

    is_pressured = obs.is_available and avail_pct < threshold
    normalized_policy = policy.strip().lower()
    if is_pressured:
        action = "PAUSE" if normalized_policy == "pause" else "REJECT"
        logger.warning(
            "%s: system RAM headroom below threshold (available=%.1f%% < %.1f%%) -> %s",
            MEMORY_WATCHDOG_FR,
            avail_pct,
            threshold,
            action,
            extra={
                "fr_id": MEMORY_WATCHDOG_FR,
                "available_pct": avail_pct,
                "threshold_pct": threshold,
                "action": action,
            },
        )
    else:
        action = "ALLOW"
        logger.debug(
            "%s: system RAM headroom healthy (available=%.1f%% >= %.1f%%)",
            MEMORY_WATCHDOG_FR,
            avail_pct,
            threshold,
            extra={
                "fr_id": MEMORY_WATCHDOG_FR,
                "available_pct": avail_pct,
                "threshold_pct": threshold,
                "action": action,
            },
        )

    return MemoryWatchdogStatus(
        available_pct=avail_pct,
        used_pct=obs.used_pct,
        available_bytes=obs.available_bytes,
        total_bytes=obs.total_bytes,
        threshold_pct=threshold,
        is_pressured=is_pressured,
        recommended_action=action,
        timestamp_utc=datetime.now(UTC).isoformat(),
    )


def evaluate_dataframe_guard(
    row_count: int,
    *,
    max_rows: int = 5_000_000,
    mode: str = "warn",
) -> str:
    """Evaluate data-frame size against configured warn/stop/off guard policy.

    Args:
        row_count: Number of rows in the candidate DataFrame/series.
        max_rows: Maximum permitted row threshold before guard triggers.
        mode: Guard policy ('warn', 'stop', or 'off').

    Returns:
        Guard decision string ('ALLOW' or 'WARN').

    Raises:
        MemoryError: When mode is 'stop' and row_count exceeds max_rows.
    """
    normalized_mode = mode.strip().lower()
    if normalized_mode == "off" or row_count <= max_rows:
        logger.debug(
            "%s: dataframe guard passed (rows=%d, max=%d, mode=%s)",
            MEMORY_WATCHDOG_FR,
            row_count,
            max_rows,
            normalized_mode,
            extra={"fr_id": MEMORY_WATCHDOG_FR, "rows": row_count},
        )
        return "ALLOW"

    if normalized_mode == "stop":
        logger.error(
            "%s: dataframe guard stopped execution (rows=%d > max=%d)",
            MEMORY_WATCHDOG_FR,
            row_count,
            max_rows,
            extra={"fr_id": MEMORY_WATCHDOG_FR, "rows": row_count},
        )
        raise MemoryError(
            f"DataFrame row count ({row_count}) exceeds stop limit ({max_rows})."
        )

    logger.warning(
        "%s: dataframe guard warning (rows=%d > max=%d)",
        MEMORY_WATCHDOG_FR,
        row_count,
        max_rows,
        extra={"fr_id": MEMORY_WATCHDOG_FR, "rows": row_count},
    )
    return "WARN"


def run_memory_cleanup() -> int:
    """Execute explicit garbage collection and log reclaimed object count.

    Returns:
        Number of unreachable objects reclaimed by garbage collector.
    """
    reclaimed = gc.collect()
    logger.info(
        "%s: executed memory cleanup (reclaimed_objects=%d)",
        MEMORY_WATCHDOG_FR,
        reclaimed,
        extra={"fr_id": MEMORY_WATCHDOG_FR, "reclaimed_objects": reclaimed},
    )
    return reclaimed


class MemoryWatchdog:
    """Active memory monitor rejecting or pausing tasks when available RAM < 15%."""

    def __init__(
        self,
        min_available_pct: float = MIN_AVAILABLE_RAM_PCT,
        *,
        policy: str = "reject",
        poll_interval_seconds: float = 1.0,
        probe_fn: Callable[[], MemoryObservation] | None = None,
    ) -> None:
        """Initialize MemoryWatchdog with threshold and enforcement policy.

        Args:
            min_available_pct: Minimum required available system RAM percentage.
            policy: Action on memory pressure ('reject' or 'pause').
            poll_interval_seconds: Background monitor polling interval.
            probe_fn: Optional custom memory probe callable for testing.
        """
        self._min_available_pct = float(min_available_pct)
        self._policy = policy
        self._poll_interval = max(0.05, float(poll_interval_seconds))
        self._probe_fn = probe_fn or probe_memory
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_status: MemoryWatchdogStatus | None = None
        self._pressure_callbacks: list[Callable[[MemoryWatchdogStatus], None]] = []
        self._recovery_callbacks: list[Callable[[MemoryWatchdogStatus], None]] = []

    @property
    def min_available_pct(self) -> float:
        """Return configured minimum available RAM percentage threshold."""
        return self._min_available_pct

    @property
    def policy(self) -> str:
        """Return configured enforcement policy ('reject' or 'pause')."""
        return self._policy

    def register_callbacks(
        self,
        *,
        on_pressure: Callable[[MemoryWatchdogStatus], None] | None = None,
        on_recovery: Callable[[MemoryWatchdogStatus], None] | None = None,
    ) -> None:
        """Register callbacks invoked when RAM drops below or recovers above 15%."""
        with self._lock:
            if on_pressure is not None:
                self._pressure_callbacks.append(on_pressure)
            if on_recovery is not None:
                self._recovery_callbacks.append(on_recovery)

    def check(self, *, policy: str | None = None) -> MemoryWatchdogStatus:
        """Evaluate current memory headroom and invoke state-transition callbacks."""
        obs = self._probe_fn()
        effective_policy = policy if policy is not None else self._policy
        status = check_memory_headroom(
            self._min_available_pct,
            policy=effective_policy,
            memory_obs=obs,
        )

        with self._lock:
            prev = self._last_status
            self._last_status = status
            pressure_cbs = list(self._pressure_callbacks)
            recovery_cbs = list(self._recovery_callbacks)

        if status.is_pressured:
            for cb in pressure_cbs:
                cb(status)
        elif prev is not None and prev.is_pressured and not status.is_pressured:
            for cb in recovery_cbs:
                cb(status)

        return status

    def start(self) -> None:
        """Start background daemon thread monitoring system RAM headroom."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._monitor_loop,
                name="HostMemoryWatchdog",
                daemon=True,
            )
            self._thread.start()
        logger.info(
            "%s: started background memory watchdog (threshold=%.1f%%, policy=%s)",
            MEMORY_WATCHDOG_FR,
            self._min_available_pct,
            self._policy,
            extra={"fr_id": MEMORY_WATCHDOG_FR},
        )

    def stop(self) -> None:
        """Stop background memory watchdog monitor thread."""
        self._stop_event.set()
        with self._lock:
            thread = self._thread
            self._thread = None
        if thread is not None and thread.is_alive():
            thread.join(timeout=2.0)
        logger.info(
            "%s: stopped background memory watchdog",
            MEMORY_WATCHDOG_FR,
            extra={"fr_id": MEMORY_WATCHDOG_FR},
        )

    def _monitor_loop(self) -> None:
        """Background polling loop checking RAM headroom."""
        while not self._stop_event.is_set():
            self.check()
            self._stop_event.wait(self._poll_interval)


# ============================================================================
# 7. Isolated Per-Job Scratch Directory Sandboxing
# ============================================================================


def _validate_sandbox_job_id(job_id: str) -> str:
    """Validate job_id to prevent path traversal outside the scratch root."""
    cleaned = job_id.strip()
    if (
        not cleaned
        or ".." in cleaned
        or "/" in cleaned
        or "\\" in cleaned
        or ":" in cleaned
    ):
        logger.error(
            "%s: rejected unsafe job_id '%s' for scratch sandbox",
            SCRATCH_SANDBOX_FR,
            job_id,
            extra={"fr_id": SCRATCH_SANDBOX_FR, "job_id": job_id},
        )
        raise ValueError(f"Invalid job_id for scratch sandbox: '{job_id}'")
    return cleaned


def allocate_job_scratch(
    job_id: str,
    base_dir: Path | str | None = None,
) -> Path:
    """Allocate an isolated temporary scratch directory for a job.

    Args:
        job_id: Unique job identifier (must not contain path separators).
        base_dir: Optional root scratch directory (defaults to data/scratch).

    Returns:
        Resolved Path to the isolated per-job scratch directory.
    """
    safe_id = _validate_sandbox_job_id(job_id)
    root = (
        Path(base_dir).resolve()
        if base_dir is not None
        else DEFAULT_SCRATCH_ROOT.resolve()
    )
    target = (root / safe_id).resolve()

    if root not in target.parents:
        logger.error(
            "%s: scratch path escaped root containment for job %s",
            SCRATCH_SANDBOX_FR,
            safe_id,
            extra={"fr_id": SCRATCH_SANDBOX_FR, "job_id": safe_id},
        )
        raise ValueError(f"Scratch path escaped containment for job '{safe_id}'")

    target.mkdir(parents=True, exist_ok=True)
    logger.info(
        "%s: allocated scratch sandbox for job %s at %s",
        SCRATCH_SANDBOX_FR,
        safe_id,
        normalize_path(str(target)),
        extra={"fr_id": SCRATCH_SANDBOX_FR, "job_id": safe_id},
    )
    return target


def cleanup_job_scratch(
    job_id: str,
    base_dir: Path | str | None = None,
) -> bool:
    """Remove the isolated temporary scratch directory for a completed/cancelled job.

    Args:
        job_id: Unique job identifier.
        base_dir: Optional root scratch directory (defaults to data/scratch).

    Returns:
        True if the directory existed and was removed, False otherwise.
    """
    safe_id = _validate_sandbox_job_id(job_id)
    root = (
        Path(base_dir).resolve()
        if base_dir is not None
        else DEFAULT_SCRATCH_ROOT.resolve()
    )
    target = (root / safe_id).resolve()

    if root not in target.parents or not target.exists():
        return False

    shutil.rmtree(target, ignore_errors=True)
    logger.info(
        "%s: cleaned up scratch sandbox for job %s",
        SCRATCH_SANDBOX_FR,
        safe_id,
        extra={"fr_id": SCRATCH_SANDBOX_FR, "job_id": safe_id},
    )
    return True


@contextmanager
def job_scratch_sandbox(
    job_id: str,
    base_dir: Path | str | None = None,
) -> Generator[Path]:
    """Context manager allocating and cleaning up a job scratch sandbox."""
    scratch_path = allocate_job_scratch(job_id, base_dir=base_dir)
    try:
        yield scratch_path
    finally:
        cleanup_job_scratch(job_id, base_dir=base_dir)


# ============================================================================
# 8. Real Computational Benchmark Engine
# ============================================================================


def run_cpu_benchmark(
    iterations: int = 100_000,
    cancel_event: threading.Event | None = None,
) -> BenchmarkResults:
    """Execute real, deterministic computational CPU benchmark.

    Evaluates arithmetic, trigonometric, and polynomial sequences simulating
    quantitative indicator processing across tick series. Never synthesizes
    or fakes performance scores.

    Args:
        iterations: Number of computational tick evaluations.
        cancel_event: Optional cooperative cancellation event.

    Returns:
        BenchmarkResults detailing measured duration and throughput.

    Raises:
        InterruptedError: If cancel_event was signaled during computation.
    """
    safe_iterations = max(1, iterations)
    logger.info(
        "%s: starting CPU benchmark with %d iterations.",
        BENCHMARK_FR,
        safe_iterations,
        extra={"fr_id": BENCHMARK_FR, "iterations": safe_iterations},
    )

    start_perf = time.perf_counter()
    accumulator = 1.0
    check_interval = max(1, min(BENCHMARK_CHECK_INTERVAL, safe_iterations // 5))

    for idx in range(1, safe_iterations + 1):
        if (
            cancel_event is not None
            and (idx % check_interval == 0)
            and cancel_event.is_set()
        ):
            logger.info(
                "%s: benchmark cancelled cooperatively at %d/%d.",
                BENCHMARK_FR,
                idx,
                safe_iterations,
                extra={"fr_id": BENCHMARK_FR, "completed": idx},
            )
            raise InterruptedError("Benchmark cancelled by caller")

        factor = (idx % 1000) + 1.0
        accumulator += (math.sin(factor) * math.cos(factor)) + math.sqrt(factor)

    _ = accumulator
    elapsed = max(1e-6, time.perf_counter() - start_perf)
    throughput = round(safe_iterations / elapsed, 2)
    time_per_tick_ms = round((elapsed * 1000.0) / safe_iterations, 5)
    avg_strat_time = round(elapsed / 100.0, 4)
    avg_strat_hour = round(3600.0 / avg_strat_time) if avg_strat_time > 0 else 0

    results = BenchmarkResults(
        duration_seconds=round(elapsed, 4),
        total_ticks=safe_iterations,
        avg_strategies_per_hour=avg_strat_hour,
        time_per_tick_ms=time_per_tick_ms,
        throughput_ops_per_sec=throughput,
    )

    logger.info(
        "%s: benchmark finished: duration=%.4fs, throughput=%.0f ops/s",
        BENCHMARK_FR,
        elapsed,
        throughput,
        extra={
            "fr_id": BENCHMARK_FR,
            "duration": elapsed,
            "throughput": throughput,
        },
    )
    return results


class BenchmarkRunner:
    """Manages synchronous and background benchmark execution lifecycle."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, BenchmarkJob] = {}
        self._cancel_events: dict[str, threading.Event] = {}

    def start_job(
        self,
        iterations: int = 100_000,
    ) -> BenchmarkJob:
        """Start a new benchmark job in a background worker thread.

        Args:
            iterations: Number of computational iterations to evaluate.

        Returns:
            BenchmarkJob record initialized in running state.
        """
        job_id = f"bench-{uuid.uuid4().hex[:8]}"
        cancel_evt = threading.Event()

        job = BenchmarkJob(
            job_id=job_id,
            state="running",
            progress_pct=0.0,
            started_at=datetime.now(UTC).isoformat(),
            completed_at=None,
            duration_seconds=None,
            iterations_completed=0,
            throughput_ops_per_sec=None,
            results=None,
            error_message=None,
            metadata={"requested_iterations": iterations},
        )

        with self._lock:
            self._jobs[job_id] = job
            self._cancel_events[job_id] = cancel_evt

        worker = threading.Thread(
            target=self._execute_worker,
            args=(job_id, iterations, cancel_evt),
            name=f"BenchmarkWorker-{job_id}",
            daemon=True,
        )
        worker.start()
        return job

    def _execute_worker(
        self,
        job_id: str,
        iterations: int,
        cancel_evt: threading.Event,
    ) -> None:
        """Worker thread executing the benchmark computation."""
        start_perf = time.perf_counter()
        completed = 0
        try:
            results = run_cpu_benchmark(iterations=iterations, cancel_event=cancel_evt)
            with self._lock:
                curr = self._jobs.get(job_id)
                self._jobs[job_id] = BenchmarkJob(
                    job_id=job_id,
                    state="completed",
                    progress_pct=100.0,
                    started_at=curr.started_at if curr else None,
                    completed_at=datetime.now(UTC).isoformat(),
                    duration_seconds=results.duration_seconds,
                    iterations_completed=iterations,
                    throughput_ops_per_sec=results.throughput_ops_per_sec,
                    results=results,
                    error_message=None,
                    metadata=curr.metadata if curr else {},
                )
        except InterruptedError:
            elapsed = round(time.perf_counter() - start_perf, 4)
            with self._lock:
                curr = self._jobs.get(job_id)
                self._jobs[job_id] = BenchmarkJob(
                    job_id=job_id,
                    state="cancelled",
                    progress_pct=round((completed / max(1, iterations)) * 100.0, 1),
                    started_at=curr.started_at if curr else None,
                    completed_at=datetime.now(UTC).isoformat(),
                    duration_seconds=elapsed,
                    iterations_completed=completed,
                    throughput_ops_per_sec=None,
                    results=None,
                    error_message="Benchmark cancelled by user request",
                    metadata=curr.metadata if curr else {},
                )
        except Exception as exc:  # noqa: BLE001
            elapsed = round(time.perf_counter() - start_perf, 4)
            with self._lock:
                curr = self._jobs.get(job_id)
                self._jobs[job_id] = BenchmarkJob(
                    job_id=job_id,
                    state="failed",
                    progress_pct=0.0,
                    started_at=curr.started_at if curr else None,
                    completed_at=datetime.now(UTC).isoformat(),
                    duration_seconds=elapsed,
                    iterations_completed=completed,
                    throughput_ops_per_sec=None,
                    results=None,
                    error_message=str(exc),
                    metadata=curr.metadata if curr else {},
                )

    def get_job(self, job_id: str) -> BenchmarkJob | None:
        """Retrieve status of an existing benchmark job."""
        with self._lock:
            return self._jobs.get(job_id)

    def cancel_job(self, job_id: str) -> bool:
        """Signal cooperative cancellation to a running benchmark job."""
        with self._lock:
            evt = self._cancel_events.get(job_id)
            if evt is not None:
                evt.set()
                logger.info(
                    "%s: signaled cooperative cancellation for %s",
                    BENCHMARK_FR,
                    job_id,
                    extra={"fr_id": BENCHMARK_FR, "job_id": job_id},
                )
                return True
            return False


# ============================================================================
# 9. Unified ResourceManager Custodian
# ============================================================================


class ResourceManager:
    """Unified custodian for diagnostics, worker sizing, watchdog, and sandboxes."""

    def __init__(
        self,
        *,
        min_available_ram_pct: float = MIN_AVAILABLE_RAM_PCT,
        watchdog_policy: str = "reject",
        scratch_root: Path | str | None = None,
        probe_memory_fn: Callable[[], MemoryObservation] | None = None,
    ) -> None:
        """Initialize ResourceManager with memory watchdog and scratch root."""
        self._scratch_root = (
            Path(scratch_root) if scratch_root is not None else DEFAULT_SCRATCH_ROOT
        )
        self._watchdog = MemoryWatchdog(
            min_available_pct=min_available_ram_pct,
            policy=watchdog_policy,
            probe_fn=probe_memory_fn,
        )

    @property
    def watchdog(self) -> MemoryWatchdog:
        """Return the active MemoryWatchdog instance."""
        return self._watchdog

    @property
    def scratch_root(self) -> Path:
        """Return configured root directory for per-job scratch sandboxes."""
        return self._scratch_root

    def get_system_health(
        self,
        db_path: Path | str | None = None,
        root_path: Path | str | None = None,
        settings: Any = None,
    ) -> HostHealthReport:
        """Return complete host health report."""
        return get_system_health(
            db_path=db_path,
            root_path=root_path,
            settings=settings,
        )

    def get_worker_allocation(
        self,
        mode: str = "reserve-two",
        custom_cores: int = 1,
    ) -> int:
        """Calculate worker count via workers = max(1, cpu_cores - 2) default policy."""
        cpu = probe_cpu()
        return calculate_worker_allocation(
            cpu.logical_cores,
            mode=mode,
            custom_cores=custom_cores,
        )

    def check_memory_headroom(
        self,
        *,
        policy: str | None = None,
    ) -> MemoryWatchdogStatus:
        """Evaluate available system RAM headroom via the memory watchdog."""
        return self._watchdog.check(policy=policy)

    def allocate_scratch(self, job_id: str) -> Path:
        """Allocate isolated temporary scratch directory for a job."""
        return allocate_job_scratch(job_id, base_dir=self._scratch_root)

    def cleanup_scratch(self, job_id: str) -> bool:
        """Clean up isolated temporary scratch directory for a job."""
        return cleanup_job_scratch(job_id, base_dir=self._scratch_root)

    @contextmanager
    def scratch_sandbox(self, job_id: str) -> Generator[Path]:
        """Context manager provisioning and cleaning up a per-job scratch directory."""
        with job_scratch_sandbox(job_id, base_dir=self._scratch_root) as path:
            yield path


resource_manager = ResourceManager()


# ============================================================================
# Main Entrypoint Demonstration
# ============================================================================


def main() -> None:
    """Demonstrate probes, worker limits, watchdog, sandbox, and benchmark."""
    print("=== 1. Workspace Directory Inspection ===")
    dirs = inspect_workspace_directories()
    for name, status in dirs.items():
        print(f"  Directory '{name}': {'EXISTS' if status else 'ABSENT'}")

    print("=== 2. Granular Telemetry Probes ===")
    cpu = probe_cpu()
    print(
        f"CPU: {cpu.logical_cores} logical cores ({cpu.physical_cores} physical) | "
        f"{cpu.utilization_pct or 0.0}% utilization"
    )
    mem = probe_memory()
    print(
        f"RAM: {mem.total_mb / 1024.0:.2f} GB total | "
        f"{mem.available_mb / 1024.0:.2f} GB available ({mem.used_pct:.1f}% used)"
    )
    disk = probe_disk()
    print(
        f"Disk ({disk.mount_point}): {disk.total_bytes / (1024**3):.2f} GB total | "
        f"{disk.free_bytes / (1024**3):.2f} GB free ({disk.free_pct:.1f}% free)"
    )
    proc = probe_process()
    print(
        f"Process PID {proc.pid}: {proc.memory_rss_mb:.1f} MB RSS | "
        f"{proc.threads_count} threads | {proc.uptime_seconds:.1f}s uptime"
    )

    print("=== 3. Worker Concurrency (workers = max(1, cpu_cores - 2)) ===")
    capacity = get_worker_capacity()
    print(
        f"Worker Capacity: {capacity.allocated_workers} workers allocated "
        f"({capacity.mode} mode) from {capacity.total_cores} cores"
    )

    print("=== 4. Memory Watchdog & Per-Job Scratch Sandbox ===")
    watchdog_status = resource_manager.check_memory_headroom()
    print(
        f"Memory Watchdog: {watchdog_status.available_pct:.1f}% available "
        f"(threshold={watchdog_status.threshold_pct:.1f}%, "
        f"action={watchdog_status.recommended_action})"
    )
    with resource_manager.scratch_sandbox("demo-job-001") as sandbox_dir:
        marker = sandbox_dir / "task.txt"
        marker.write_text("sandbox active", encoding="utf-8")
    run_memory_cleanup()

    print("=== 5. Computational Benchmark & Consolidated System Health ===")
    bench = run_cpu_benchmark(iterations=2_000)
    print(
        f"Benchmark Throughput: {bench.throughput_ops_per_sec:.0f} ops/sec "
        f"({bench.duration_seconds:.4f}s elapsed)"
    )
    health = get_system_health()
    print(
        f"System Health Status: {health.status} "
        f"(DB tables={health.database.table_count})"
    )


if __name__ == "__main__":
    main()
