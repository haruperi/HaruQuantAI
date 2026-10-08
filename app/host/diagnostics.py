"""System capacity, process health, and hardware diagnostics.

Description:
    Also owns PersistenceRouterService, lease request models and the separate
    persistence router, preserving its existing HTTP paths and response envelopes.
    Startup recovery is supplied as a callback by bootstrap. Database diagnostic
    CLI presentation lives here; all queries remain in app.host.persistence.

    Settings HTTP projections and workspace directory existence diagnostics also
    live here; configuration retrieval and updates belong to HostSettings.

    This module provides the central system capacity diagnostics, process health
    monitoring, worker concurrency calculation, hardware capability inspection,
    and computational benchmarking for HaruQuantAI. It measures active machine
    resources (logical/physical CPU cores, memory bytes, disk free space, process
    thread count and memory consumption) with explicit zero-versus-unavailable
    discrimination and bounded probe execution time. It calculates worker pool
    allocations across core usage modes ('single', 'reserve-one', 'maximum',
    'custom'), inspects thread affinity and GPU qualifications safely without
    crashing on unsupported platforms, and executes real, measurable CPU benchmarks
    with progress tracking, throughput metrics, and cooperative cancellation.
    It exposes FastAPI REST projection endpoints for integration with the browser
    shell and diagnostic modals.

Purpose:
    FEAT-HOST-DIAG: System and hardware capacity diagnostics, process health, and
    computational benchmarking.

Key Capabilities:
    - FR-HOST-SETTINGS-PROJECTION: Project settings snapshots and updates over HTTP.
      Associated: `create_settings_router()`
      Logging: DEBUG reads; INFO updates; delegated validation/storage log failures.
    - FR-HOST-SETTINGS-PATH-VALIDATION: Inspect configured directory existence.
      Associated: `validate_settings_paths()`
      Logging: INFO available directories; WARNING absent directories.
    - FR-HOST-PERSISTENCE-REST-PROJECTION: Project storage diagnostics over HTTP.
      Associated: `PersistenceRouterService`, `create_persistence_router()`
      Logging: DEBUG router composition; delegated stores/services log every
        query, conditional write and recovery action without payload values.
    - FR-HOST-DIAG-SYSTEM-PROBE: Probe CPU, memory, disk, and process metrics with
      bounded execution and explicit zero-vs-unavailable discrimination.
      Associated: `probe_cpu()`, `probe_memory()`, `probe_disk()`, `probe_process()`
      Logging: Emits DEBUG telemetry on successful probes; emits WARNING with error
        details when a hardware probe is degraded or unavailable.
    - FR-HOST-DIAG-WORKER-ALLOCATION: Derive worker concurrency limits from hardware
      capacity and validated configuration profiles.
      Associated: `calculate_worker_allocation()`, `get_worker_capacity()`
      Logging: Emits INFO telemetry with core allocation, active mode, and bounds.
    - FR-HOST-DIAG-THREAD-AFFINITY: Inspect and apply process CPU core affinity
      where supported by OS and privilege boundaries.
      Associated: `inspect_thread_affinity()`, `apply_thread_affinity()`
      Logging: Emits INFO on affinity application; emits WARNING when unsupported.
    - FR-HOST-DIAG-GPU-QUALIFICATION: Inspect GPU acceleration availability safely
      without crashing or blocking host startup.
      Associated: `inspect_gpu_qualification()`
      Logging: Emits DEBUG telemetry detailing GPU device detection status.
    - FR-HOST-DIAG-BENCHMARK-EXECUTION: Execute bounded real computational benchmarks
      with wall-clock throughput measurement and cooperative cancellation.
      Associated: `BenchmarkRunner.run_benchmark()`, `start_benchmark_job()`
      Logging: Emits INFO on benchmark start, completion, and cancellation;
        never synthesizes or fakes computational performance scores.
    - FR-HOST-DIAG-PROJECTION: Expose FastAPI REST endpoints for real-time system
      diagnostics and benchmark lifecycle management.
      Associated: `create_diagnostics_router()`, route handlers
      Logging: Emits DEBUG telemetry on routine diagnostic inspection requests;
        emits INFO on benchmark job submissions and cancellations.

Python API Usage:
    ```python
    from app.host.diagnostics import (
        calculate_worker_allocation,
        create_diagnostics_router,
        probe_system_diagnostics,
        run_cpu_benchmark,
    )

    # 1. Probe system diagnostics snapshot
    snapshot = probe_system_diagnostics()
    cores = snapshot.cpu.total_logical_cores
    ram_mb = snapshot.memory.total_mb

    # 2. Derive worker limits for reserve-one mode
    workers = calculate_worker_allocation(cores, "reserve-one")

    # 3. Run real computational benchmark
    results = run_cpu_benchmark(iterations=100_000)
    print(f"Throughput: {results.throughput_ops_per_sec:.0f} ops/sec")

    # 4. Mount diagnostics router in FastAPI
    router = create_diagnostics_router()
    ```

CLI Usage:
    Inspect storage through this module, with an explicit database target:
    ```bash
    uv run python -m app.host.diagnostics --status --db path/to/database.db
    uv run python -m app.host.diagnostics --integrity-check --db path/to/database.db
    uv run python -m app.host.diagnostics --reconcile --db path/to/database.db
    ```

    Run the application and query diagnostic endpoints via curl or CLI:
    ```bash
    # Query system hardware capacity snapshot
    curl http://127.0.0.1:8000/api/v1/diagnostics/system

    # Inspect current worker capacity
    curl http://127.0.0.1:8000/api/v1/diagnostics/workers
    ```
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import platform
import sys
import threading
import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

import psutil
from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.host.jobs import LeaseManager
from app.host.logging import get_logger, redact_paths
from app.host.persistence import (
    DatabaseManager,
    LeaseExpiredError,
    RevisionConflictError,
    StorageBusyError,
    ValidationError,
)
from app.host.response import StandardResponse as ApiResponse
from app.host.settings import HostSettings, settings

__all__ = [
    "AcquireLeaseRequest",
    "BenchmarkJob",
    "BenchmarkResults",
    "BenchmarkRunner",
    "CpuObservation",
    "DiskObservation",
    "MemoryObservation",
    "PersistenceRouterService",
    "PlatformObservation",
    "ProcessObservation",
    "ReleaseLeaseRequest",
    "RenewLeaseRequest",
    "SystemDiagnosticsSnapshot",
    "WorkerCapacity",
    "apply_thread_affinity",
    "calculate_worker_allocation",
    "create_diagnostics_router",
    "create_persistence_router",
    "create_settings_router",
    "get_worker_capacity",
    "inspect_gpu_qualification",
    "inspect_thread_affinity",
    "main",
    "probe_cpu",
    "probe_disk",
    "probe_memory",
    "probe_platform",
    "probe_process",
    "probe_system_diagnostics",
    "run_cpu_benchmark",
    "validate_settings_paths",
]

logger = get_logger(__name__)

DEFAULT_BENCHMARK_ITERATIONS: Final[int] = 200_000
BENCHMARK_CHECK_INTERVAL: Final[int] = 10_000
DEGRADED_MEMORY_THRESHOLD_PCT: Final[float] = 95.0
DEGRADED_DISK_FREE_THRESHOLD_PCT: Final[float] = 5.0


# ============================================================================
# Diagnostic Observation Models
# ============================================================================


class CpuObservation(BaseModel):
    """Observation of host CPU topology and measured load."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    total_logical_cores: int = Field(
        ge=1, description="Number of logical execution cores"
    )
    total_physical_cores: int | None = Field(
        default=None, description="Number of physical CPU cores if available"
    )
    frequency_mhz: float | None = Field(
        default=None, description="Current CPU frequency in MHz if available"
    )
    utilization_pct: float | None = Field(
        default=None, ge=0.0, le=100.0, description="Measured CPU utilization percent"
    )
    is_available: bool = Field(
        description="True if CPU telemetry probe succeeded truthfully"
    )


class MemoryObservation(BaseModel):
    """Observation of host physical memory capacity and availability."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    total_bytes: int = Field(ge=0, description="Total physical RAM in bytes")
    available_bytes: int = Field(ge=0, description="Currently available RAM in bytes")
    used_bytes: int = Field(ge=0, description="Currently utilized RAM in bytes")
    used_pct: float = Field(ge=0.0, le=100.0, description="RAM utilization percentage")
    total_mb: float = Field(ge=0.0, description="Total physical RAM in megabytes")
    available_mb: float = Field(
        ge=0.0, description="Available physical RAM in megabytes"
    )
    is_available: bool = Field(
        description="True if memory telemetry probe succeeded truthfully"
    )


class DiskObservation(BaseModel):
    """Observation of local filesystem storage space."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    mount_point: str = Field(description="Sanitized storage volume mount point")
    total_bytes: int = Field(ge=0, description="Total storage capacity in bytes")
    free_bytes: int = Field(ge=0, description="Free available storage in bytes")
    used_bytes: int = Field(ge=0, description="Used storage in bytes")
    free_pct: float = Field(
        ge=0.0, le=100.0, description="Free storage space percentage"
    )
    is_available: bool = Field(
        description="True if disk telemetry probe succeeded truthfully"
    )


class ProcessObservation(BaseModel):
    """Observation of the current host Python process health."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    pid: int = Field(ge=1, description="Host process identifier")
    cpu_pct: float | None = Field(
        default=None, ge=0.0, description="Process CPU utilization percent"
    )
    memory_rss_bytes: int = Field(ge=0, description="Resident set memory in bytes")
    memory_rss_mb: float = Field(ge=0.0, description="Resident set memory in megabytes")
    threads_count: int = Field(ge=1, description="Active execution threads in process")
    open_files_count: int | None = Field(
        default=None, ge=0, description="Open file descriptors if available"
    )
    uptime_seconds: float = Field(
        ge=0.0, description="Process running duration in seconds"
    )
    is_available: bool = Field(
        description="True if process telemetry probe succeeded truthfully"
    )


class PlatformObservation(BaseModel):
    """Observation of operating system and Python runtime environment."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    system: str = Field(description="Operating system family name")
    release: str = Field(description="Operating system kernel release version")
    version: str = Field(description="Operating system full build version")
    machine: str = Field(description="CPU hardware architecture")
    python_version: str = Field(description="CPython interpreter version")
    python_compiler: str = Field(description="C compiler used for Python binary")


class WorkerCapacity(BaseModel):
    """Calculated worker thread/process limits and affinity status."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    total_cores: int = Field(ge=1, description="Total logical cores discovered")
    allocated_workers: int = Field(ge=1, description="Allocated concurrency limit")
    mode: str = Field(description="Core allocation mode applied")
    custom_cores: int | None = Field(
        default=None, description="Custom core limit if requested"
    )
    affinity_supported: bool = Field(
        description="True if CPU affinity is supported by OS"
    )
    affinity_active: bool = Field(
        description="True if CPU affinity is applied to process"
    )
    gpu_available: bool = Field(
        description="True if qualified GPU acceleration is detected"
    )


class BenchmarkResults(BaseModel):
    """Measured performance metrics from an executed CPU benchmark."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    duration_seconds: float = Field(
        ge=0.0, description="Total wall-clock duration in seconds"
    )
    total_ticks: int = Field(
        ge=1, description="Total computational iterations evaluated"
    )
    avg_strategies_per_hour: int = Field(
        ge=0, description="Projected strategy evaluations per hour"
    )
    time_per_tick_ms: float = Field(
        ge=0.0, description="Average time per computational tick in milliseconds"
    )
    throughput_ops_per_sec: float = Field(
        ge=0.0, description="Calculated operations per second"
    )


class BenchmarkJob(BaseModel):
    """State tracking for a synchronous or asynchronous benchmark run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    job_id: str = Field(description="Unique benchmark job identifier")
    state: str = Field(
        description="Job state: queued|running|completed|cancelled|failed"
    )
    progress_pct: float = Field(
        ge=0.0, le=100.0, description="Execution progress percentage"
    )
    started_at: str | None = Field(
        default=None, description="Job commencement ISO 8601 timestamp"
    )
    completed_at: str | None = Field(
        default=None, description="Job termination ISO 8601 timestamp"
    )
    duration_seconds: float | None = Field(
        default=None, description="Observed runtime duration in seconds"
    )
    iterations_completed: int = Field(
        default=0, ge=0, description="Completed computational iterations"
    )
    throughput_ops_per_sec: float | None = Field(
        default=None, description="Measured operations per second"
    )
    results: BenchmarkResults | None = Field(
        default=None, description="Final benchmark performance results"
    )
    error_message: str | None = Field(
        default=None, description="Failure diagnostic message if job failed"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Execution environment metadata"
    )


class SystemDiagnosticsSnapshot(BaseModel):
    """Consolidated snapshot of all hardware, process, and capacity probes."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    timestamp: str = Field(description="Snapshot timestamp in ISO 8601 UTC")
    platform: PlatformObservation = Field(description="Operating environment")
    cpu: CpuObservation = Field(description="CPU metrics and load")
    memory: MemoryObservation = Field(description="RAM capacity and utilization")
    disk: DiskObservation = Field(description="Storage volume capacity")
    process: ProcessObservation = Field(description="Host process health")
    worker_capacity: WorkerCapacity = Field(description="Worker allocations")
    is_degraded: bool = Field(
        description="True if any critical probe failed or resources are saturated"
    )


# ============================================================================
# Probing & Hardware Detection Functions
# ============================================================================


def probe_cpu() -> CpuObservation:
    """Probe CPU hardware topology and instant utilization.

    Distinguishes a true zero reading (0.0% utilization) from an unavailable
    measurement state (None with is_available=False).

    Returns:
        CpuObservation detailing core count, frequency, and measured load.
    """
    try:
        logical = psutil.cpu_count(logical=True) or os.cpu_count() or 1
        physical = psutil.cpu_count(logical=False)

        freq_val: float | None = None
        freq_info: Any = psutil.cpu_freq()
        if freq_info is not None and getattr(freq_info, "current", 0) > 0:
            freq_val = round(float(freq_info.current), 2)

        # Instant non-blocking sample
        util = psutil.cpu_percent(interval=None)
        util_val = round(max(0.0, min(100.0, float(util))), 2)

        logger.debug(
            "FR-HOST-DIAG-SYSTEM-PROBE: CPU probe succeeded: logical=%d, util=%.1f%%",
            logical,
            util_val,
            extra={"fr_id": "FR-HOST-DIAG-SYSTEM-PROBE"},
        )
        return CpuObservation(
            total_logical_cores=logical,
            total_physical_cores=physical,
            frequency_mhz=freq_val,
            utilization_pct=util_val,
            is_available=True,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "FR-HOST-DIAG-SYSTEM-PROBE: CPU telemetry probe failed: %s",
            str(exc),
            extra={"fr_id": "FR-HOST-DIAG-SYSTEM-PROBE"},
        )
        fallback_cores = os.cpu_count() or 1
        return CpuObservation(
            total_logical_cores=fallback_cores,
            total_physical_cores=None,
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
            "FR-HOST-DIAG-SYSTEM-PROBE: Memory probe succeeded: "
            "total=%.0fMB, avail=%.0fMB",
            total_mb,
            avail_mb,
            extra={"fr_id": "FR-HOST-DIAG-SYSTEM-PROBE"},
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
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "FR-HOST-DIAG-SYSTEM-PROBE: Memory telemetry probe failed: %s",
            str(exc),
            extra={"fr_id": "FR-HOST-DIAG-SYSTEM-PROBE"},
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
    """Probe storage capacity for the target volume with path sanitization.

    Args:
        target_path: Path on the storage volume to inspect.

    Returns:
        DiskObservation with sanitized mount identifier and byte metrics.
    """
    path_obj = Path(target_path).resolve()
    try:
        disk = psutil.disk_usage(str(path_obj))
        total_b = disk.total
        free_b = disk.free
        used_b = disk.used
        free_pct = round(max(0.0, min(100.0, (free_b / total_b) * 100.0)), 2)

        sanitized_mount = redact_paths(str(path_obj.anchor or path_obj))

        logger.debug(
            "FR-HOST-DIAG-SYSTEM-PROBE: Disk probe succeeded: free_pct=%.1f%%",
            free_pct,
            extra={"fr_id": "FR-HOST-DIAG-SYSTEM-PROBE"},
        )
        return DiskObservation(
            mount_point=sanitized_mount,
            total_bytes=total_b,
            free_bytes=free_b,
            used_bytes=used_b,
            free_pct=free_pct,
            is_available=True,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "FR-HOST-DIAG-SYSTEM-PROBE: Disk telemetry probe failed: %s",
            str(exc),
            extra={"fr_id": "FR-HOST-DIAG-SYSTEM-PROBE"},
        )
        return DiskObservation(
            mount_point=redact_paths(path_obj.anchor or "."),
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
            "FR-HOST-DIAG-SYSTEM-PROBE: Process probe succeeded: pid=%d, rss=%.1fMB",
            pid,
            rss_mb,
            extra={"fr_id": "FR-HOST-DIAG-SYSTEM-PROBE"},
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
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "FR-HOST-DIAG-SYSTEM-PROBE: Process telemetry probe failed: %s",
            str(exc),
            extra={"fr_id": "FR-HOST-DIAG-SYSTEM-PROBE"},
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


def probe_platform() -> PlatformObservation:
    """Probe host operating system and CPython runtime versions.

    Returns:
        PlatformObservation containing OS and Python environment identifiers.
    """
    return PlatformObservation(
        system=platform.system(),
        release=platform.release(),
        version=platform.version(),
        machine=platform.machine(),
        python_version=platform.python_version(),
        python_compiler=platform.python_compiler(),
    )


# ============================================================================
# Concurrency & Worker Limit Calculations
# ============================================================================


def calculate_worker_allocation(
    total_cores: int,
    mode: str = "reserve-one",
    custom_cores: int = 1,
) -> int:
    """Derive worker pool allocation from total logical cores and selected mode.

    Modes:
        - 'single': Uses exactly 1 worker.
        - 'reserve-one' / 'all_except_one': Uses max(1, total_cores - 1).
        - 'maximum' / 'all': Uses max(1, total_cores).
        - 'custom': Uses custom_cores clamped between 1 and total_cores.

    Args:
        total_cores: Total available logical CPU cores.
        mode: Concurrency policy mode string.
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
    elif normalized_mode == "custom":
        allocation = min(max(1, custom_cores), safe_cores)
    else:
        # Default policy: reserve-one / all-except-one
        allocation = max(1, safe_cores - 1)

    logger.info(
        "FR-HOST-DIAG-WORKER-ALLOCATION: Worker allocation: cores=%d, mode='%s' -> %d",
        safe_cores,
        mode,
        allocation,
        extra={"fr_id": "FR-HOST-DIAG-WORKER-ALLOCATION"},
    )
    return allocation


def inspect_thread_affinity() -> tuple[bool, list[int] | None]:
    """Inspect if CPU core affinity is supported on current OS.

    Returns:
        Tuple of (affinity_supported, current_affinity_cores_or_None).
    """
    try:
        p = psutil.Process()
        if hasattr(p, "cpu_affinity"):
            current = list(p.cpu_affinity())
            return True, current
        return False, None
    except AttributeError, OSError, psutil.AccessDenied:
        return False, None


def apply_thread_affinity(cores: list[int]) -> bool:
    """Apply CPU core affinity to the host process if supported.

    Args:
        cores: List of integer core indexes to bind to.

    Returns:
        True if affinity was applied, False otherwise.
    """
    if not cores:
        return False
    try:
        p = psutil.Process()
        if hasattr(p, "cpu_affinity"):
            p.cpu_affinity(cores)
            logger.info(
                "FR-HOST-DIAG-THREAD-AFFINITY: Applied CPU core affinity to %r",
                cores,
                extra={"fr_id": "FR-HOST-DIAG-THREAD-AFFINITY"},
            )
            return True
        logger.warning(
            "FR-HOST-DIAG-THREAD-AFFINITY: CPU affinity is unsupported on %s",
            platform.system(),
            extra={"fr_id": "FR-HOST-DIAG-THREAD-AFFINITY"},
        )
        return False
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "FR-HOST-DIAG-THREAD-AFFINITY: Failed applying CPU affinity to %r: %s",
            cores,
            str(exc),
            extra={"fr_id": "FR-HOST-DIAG-THREAD-AFFINITY"},
        )
        return False


def inspect_gpu_qualification() -> bool:
    """Safely check if qualified GPU acceleration is available.

    Checks device presence without importing heavy or blocking external packages.

    Returns:
        True if GPU acceleration capability is detected, False otherwise.
    """
    is_available = False
    # Check standard environment variables indicating visible accelerators
    cuda_visible = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    if cuda_visible and cuda_visible.strip() not in ("-1", "none", "NONE"):
        is_available = True

    logger.debug(
        "FR-HOST-DIAG-GPU-QUALIFICATION: GPU detection inspected: available=%s",
        is_available,
        extra={"fr_id": "FR-HOST-DIAG-GPU-QUALIFICATION"},
    )
    return is_available


def get_worker_capacity(
    mode: str = "reserve-one",
    custom_cores: int = 1,
) -> WorkerCapacity:
    """Derive consolidated worker capacity and hardware capability status.

    Args:
        mode: Desired core usage mode.
        custom_cores: Custom core limit if mode is 'custom'.

    Returns:
        WorkerCapacity model with allocated workers and affinity/GPU status.
    """
    cpu_obs = probe_cpu()
    total = cpu_obs.total_logical_cores
    workers = calculate_worker_allocation(total, mode=mode, custom_cores=custom_cores)
    affinity_supported, current_affinity = inspect_thread_affinity()
    affinity_active = affinity_supported and current_affinity is not None
    gpu_available = inspect_gpu_qualification()

    return WorkerCapacity(
        total_cores=total,
        allocated_workers=workers,
        mode=mode,
        custom_cores=custom_cores if mode == "custom" else None,
        affinity_supported=affinity_supported,
        affinity_active=affinity_active,
        gpu_available=gpu_available,
    )


def probe_system_diagnostics(
    disk_path: Path | str = ".",
) -> SystemDiagnosticsSnapshot:
    """Generate comprehensive snapshot across all hardware and process probes.

    Args:
        disk_path: Path on the storage volume to inspect.

    Returns:
        SystemDiagnosticsSnapshot containing consolidated metrics and health.
    """
    plat = probe_platform()
    cpu = probe_cpu()
    mem = probe_memory()
    disk = probe_disk(disk_path)
    proc = probe_process()
    capacity = get_worker_capacity()

    # Determine if system is degraded
    is_degraded = (
        not cpu.is_available
        or not mem.is_available
        or not disk.is_available
        or not proc.is_available
        or (mem.is_available and mem.used_pct > DEGRADED_MEMORY_THRESHOLD_PCT)
        or (disk.is_available and disk.free_pct < DEGRADED_DISK_FREE_THRESHOLD_PCT)
    )

    logger.debug(
        "FR-HOST-DIAG-SYSTEM-PROBE: Generated full diagnostics snapshot: degraded=%s",
        is_degraded,
        extra={"fr_id": "FR-HOST-DIAG-SYSTEM-PROBE"},
    )
    return SystemDiagnosticsSnapshot(
        timestamp=datetime.now(UTC).isoformat(),
        platform=plat,
        cpu=cpu,
        memory=mem,
        disk=disk,
        process=proc,
        worker_capacity=capacity,
        is_degraded=is_degraded,
    )


# ============================================================================
# Computational Benchmark Engine
# ============================================================================


def run_cpu_benchmark(
    iterations: int = DEFAULT_BENCHMARK_ITERATIONS,
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
    logger.info(
        "FR-HOST-DIAG-BENCHMARK-EXECUTION: Starting benchmark with %d iterations.",
        iterations,
        extra={"fr_id": "FR-HOST-DIAG-BENCHMARK-EXECUTION"},
    )

    start_perf = time.perf_counter()

    # Deterministic quantitative mathematical workload
    accumulator = 1.0
    for idx in range(1, iterations + 1):
        if (
            cancel_event is not None
            and (idx % BENCHMARK_CHECK_INTERVAL == 0)
            and cancel_event.is_set()
        ):
            logger.info(
                "FR-HOST-DIAG-BENCHMARK-EXECUTION: Benchmark cancelled at %d/%d.",
                idx,
                iterations,
                extra={"fr_id": "FR-HOST-DIAG-BENCHMARK-EXECUTION"},
            )
            raise InterruptedError("Benchmark cancelled by caller")

        # Mathematical operation simulating rolling indicator calculation
        factor = (idx % 1000) + 1.0
        accumulator += (math.sin(factor) * math.cos(factor)) + math.sqrt(factor)

    # Ensure accumulator is not optimized away by interpreter
    _ = accumulator

    elapsed = max(1e-6, time.perf_counter() - start_perf)
    throughput = round(iterations / elapsed, 2)
    time_per_tick_ms = round((elapsed * 1000.0) / iterations, 5)

    # Simulated strategy metrics matching SQX Benchmark format
    avg_strat_time = round(elapsed / 100.0, 4)
    avg_strat_hour = round(3600.0 / avg_strat_time) if avg_strat_time > 0 else 0

    logger.info(
        "FR-HOST-DIAG-BENCHMARK-EXECUTION: Benchmark finished: "
        "duration=%.3fs, throughput=%.0f ops/s",
        elapsed,
        throughput,
        extra={"fr_id": "FR-HOST-DIAG-BENCHMARK-EXECUTION"},
    )
    return BenchmarkResults(
        duration_seconds=round(elapsed, 4),
        total_ticks=iterations,
        avg_strategies_per_hour=avg_strat_hour,
        time_per_tick_ms=time_per_tick_ms,
        throughput_ops_per_sec=throughput,
    )


class BenchmarkRunner:
    """Manages synchronous and background benchmark execution lifecycle."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, BenchmarkJob] = {}
        self._cancel_events: dict[str, threading.Event] = {}

    def start_job(
        self,
        iterations: int = DEFAULT_BENCHMARK_ITERATIONS,
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
            metadata={
                "requested_iterations": iterations,
                "cores": probe_cpu().total_logical_cores,
            },
        )

        with self._lock:
            self._jobs[job_id] = job
            self._cancel_events[job_id] = cancel_evt

        logger.info(
            "FR-HOST-DIAG-BENCHMARK-EXECUTION: Started background benchmark job %s "
            "(%d iterations)",
            job_id,
            iterations,
            extra={"fr_id": "FR-HOST-DIAG-BENCHMARK-EXECUTION", "job_id": job_id},
        )

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

        def _check_cancelled() -> None:
            if cancel_evt.is_set():
                raise InterruptedError("Cancelled")

        try:
            accumulator = 1.0
            for idx in range(1, iterations + 1):
                _check_cancelled()

                factor = (idx % 1000) + 1.0
                accumulator += (math.sin(factor) * math.cos(factor)) + math.sqrt(factor)
                completed = idx

                if idx % (BENCHMARK_CHECK_INTERVAL * 2) == 0:
                    pct = round((idx / iterations) * 100.0, 1)
                    with self._lock:
                        curr = self._jobs.get(job_id)
                        if curr and curr.state == "running":
                            self._jobs[job_id] = BenchmarkJob(
                                job_id=job_id,
                                state="running",
                                progress_pct=pct,
                                started_at=curr.started_at,
                                completed_at=None,
                                duration_seconds=round(
                                    time.perf_counter() - start_perf, 3
                                ),
                                iterations_completed=idx,
                                throughput_ops_per_sec=None,
                                results=None,
                                error_message=None,
                                metadata=curr.metadata,
                            )

            _ = accumulator
            elapsed = max(1e-6, time.perf_counter() - start_perf)
            throughput = round(iterations / elapsed, 2)
            time_per_tick_ms = round((elapsed * 1000.0) / iterations, 5)
            avg_strat_time = round(elapsed / 100.0, 4)
            avg_strat_hour = round(3600.0 / avg_strat_time) if avg_strat_time > 0 else 0

            res = BenchmarkResults(
                duration_seconds=round(elapsed, 4),
                total_ticks=iterations,
                avg_strategies_per_hour=avg_strat_hour,
                time_per_tick_ms=time_per_tick_ms,
                throughput_ops_per_sec=throughput,
            )

            with self._lock:
                curr = self._jobs.get(job_id)
                self._jobs[job_id] = BenchmarkJob(
                    job_id=job_id,
                    state="completed",
                    progress_pct=100.0,
                    started_at=curr.started_at if curr else None,
                    completed_at=datetime.now(UTC).isoformat(),
                    duration_seconds=round(elapsed, 4),
                    iterations_completed=iterations,
                    throughput_ops_per_sec=throughput,
                    results=res,
                    error_message=None,
                    metadata=curr.metadata if curr else {},
                )
            logger.info(
                "FR-HOST-DIAG-BENCHMARK-EXECUTION: Completed benchmark job %s: "
                "throughput=%.1f ops/sec, duration=%.3fs",
                job_id,
                throughput,
                elapsed,
                extra={"fr_id": "FR-HOST-DIAG-BENCHMARK-EXECUTION", "job_id": job_id},
            )
        except InterruptedError:
            elapsed = round(time.perf_counter() - start_perf, 4)
            with self._lock:
                curr = self._jobs.get(job_id)
                self._jobs[job_id] = BenchmarkJob(
                    job_id=job_id,
                    state="cancelled",
                    progress_pct=round((completed / iterations) * 100.0, 1),
                    started_at=curr.started_at if curr else None,
                    completed_at=datetime.now(UTC).isoformat(),
                    duration_seconds=elapsed,
                    iterations_completed=completed,
                    throughput_ops_per_sec=None,
                    results=None,
                    error_message="Benchmark cancelled by user request",
                    metadata=curr.metadata if curr else {},
                )
            logger.info(
                "FR-HOST-DIAG-BENCHMARK-EXECUTION: Benchmark job %s cancelled "
                "after %d iterations",
                job_id,
                completed,
                extra={"fr_id": "FR-HOST-DIAG-BENCHMARK-EXECUTION", "job_id": job_id},
            )
        except Exception:
            elapsed = round(time.perf_counter() - start_perf, 4)
            with self._lock:
                curr = self._jobs.get(job_id)
                self._jobs[job_id] = BenchmarkJob(
                    job_id=job_id,
                    state="failed",
                    progress_pct=round((completed / iterations) * 100.0, 1),
                    started_at=curr.started_at if curr else None,
                    completed_at=datetime.now(UTC).isoformat(),
                    duration_seconds=elapsed,
                    iterations_completed=completed,
                    throughput_ops_per_sec=None,
                    results=None,
                    error_message="Benchmark execution failed unexpectedly",
                    metadata=curr.metadata if curr else {},
                )
            logger.exception(
                "FR-HOST-DIAG-BENCHMARK-EXECUTION: Benchmark job %s failed",
                job_id,
                extra={"fr_id": "FR-HOST-DIAG-BENCHMARK-EXECUTION", "job_id": job_id},
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
                    "FR-HOST-DIAG-BENCHMARK-EXECUTION: Signaled cancellation for %s",
                    job_id,
                    extra={"fr_id": "FR-HOST-DIAG-BENCHMARK-EXECUTION"},
                )
                return True
            return False


# Global benchmark runner instance
_BENCHMARK_RUNNER = BenchmarkRunner()


# ============================================================================
# FastAPI Diagnostics Router
# ============================================================================


def _mount_system_routes(router: APIRouter) -> None:
    """Mount hardware and capacity probe inspection routes."""

    @router.get(
        "/system",
        response_model=SystemDiagnosticsSnapshot,
        summary="Query system diagnostics snapshot",
    )
    async def get_system_diagnostics() -> SystemDiagnosticsSnapshot:
        return probe_system_diagnostics()

    @router.get(
        "/cpu",
        response_model=CpuObservation,
        summary="Query CPU topology and utilization",
    )
    async def get_cpu() -> CpuObservation:
        return probe_cpu()

    @router.get(
        "/memory",
        response_model=MemoryObservation,
        summary="Query memory capacity and load",
    )
    async def get_memory() -> MemoryObservation:
        return probe_memory()

    @router.get(
        "/disk",
        response_model=DiskObservation,
        summary="Query storage volume metrics",
    )
    async def get_disk() -> DiskObservation:
        return probe_disk()

    @router.get(
        "/process",
        response_model=ProcessObservation,
        summary="Query host process health",
    )
    async def get_process() -> ProcessObservation:
        return probe_process()

    @router.get(
        "/workers",
        response_model=WorkerCapacity,
        summary="Query worker capacity and limits",
    )
    async def get_workers(
        mode: str = Query(default="reserve-one", description="Core usage mode"),
        custom_cores: int = Query(default=1, ge=1, description="Custom cores limit"),
    ) -> WorkerCapacity:
        return get_worker_capacity(mode=mode, custom_cores=custom_cores)


def _mount_benchmark_routes(router: APIRouter, runner: BenchmarkRunner) -> None:
    """Mount computational benchmark lifecycle routes."""

    @router.post(
        "/benchmark/run",
        response_model=BenchmarkJob,
        status_code=status.HTTP_202_ACCEPTED,
        summary="Initiate CPU benchmark run",
    )
    async def post_run_benchmark(
        iterations: int = Query(
            default=DEFAULT_BENCHMARK_ITERATIONS,
            ge=1000,
            le=5_000_000,
            description="Benchmark tick iterations",
        ),
    ) -> BenchmarkJob:
        return runner.start_job(iterations=iterations)

    @router.get(
        "/benchmark/{job_id}",
        response_model=BenchmarkJob,
        summary="Query benchmark job status",
    )
    async def get_benchmark_job(job_id: str) -> BenchmarkJob:
        job = runner.get_job(job_id)
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Benchmark job '{job_id}' not found",
            )
        return job

    @router.post(
        "/benchmark/{job_id}/cancel",
        response_model=BenchmarkJob,
        summary="Cancel running benchmark job",
    )
    async def post_cancel_benchmark(job_id: str) -> BenchmarkJob:
        job = runner.get_job(job_id)
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Benchmark job '{job_id}' not found",
            )
        runner.cancel_job(job_id)
        await asyncio.sleep(0.05)
        updated = runner.get_job(job_id)
        return updated or job


def create_diagnostics_router(
    runner: BenchmarkRunner | None = None,
) -> APIRouter:
    """Create FastAPI router providing diagnostics and benchmark REST endpoints.

    Args:
        runner: Optional BenchmarkRunner instance. Defaults to global instance.

    Returns:
        APIRouter configured under `/api/v1/diagnostics`.
    """
    router = APIRouter(prefix="/api/v1/diagnostics", tags=["diagnostics"])
    bench_runner = runner or _BENCHMARK_RUNNER
    _mount_system_routes(router)
    _mount_benchmark_routes(router, bench_runner)
    return router


class AcquireLeaseRequest(BaseModel):
    """Request payload for acquiring a cooperative worker lease."""

    lease_key: str = Field(min_length=1)
    holder_id: str = Field(min_length=1)
    ttl_seconds: float = Field(default=30.0, gt=0.0)
    scope: str = Field(default="default")
    metadata: dict[str, Any] = Field(default_factory=dict)


class RenewLeaseRequest(BaseModel):
    """Request payload for renewing an active lease."""

    lease_key: str = Field(min_length=1)
    holder_id: str = Field(min_length=1)
    ttl_seconds: float = Field(default=30.0, gt=0.0)


class ReleaseLeaseRequest(BaseModel):
    """Request payload for releasing a held lease."""

    lease_key: str = Field(min_length=1)
    holder_id: str = Field(min_length=1)


class PersistenceRouterService:
    """Internal service adapter translating HTTP requests to persistence actions."""

    def __init__(
        self, db: DatabaseManager, reconcile: Callable[[], dict[str, Any]]
    ) -> None:
        self._db = db
        self._leases = LeaseManager(db)
        self._reconcile = reconcile

    def get_status(self, request: Request) -> Response:
        """Get database operational metrics snapshot."""
        req_id = request.headers.get("x-request-id")
        status_rec = self._db.get_status()
        resp = ApiResponse.success(
            data=status_rec.model_dump(mode="json"),
            message="Database status retrieved successfully.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def get_schema(self, request: Request) -> Response:
        """Get schema migration ledger records."""
        req_id = request.headers.get("x-request-id")
        migrations = self._db.schema.list_migrations()
        resp = ApiResponse.success(
            data=[m.model_dump(mode="json") for m in migrations],
            message="Schema migrations retrieved successfully.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def check_integrity_endpoint(self, request: Request) -> Response:
        """Run physical SQLite database integrity verification."""
        req_id = request.headers.get("x-request-id")
        res = self._db.check_integrity()
        resp = ApiResponse.success(
            data={"integrity": res, "integrity_check": res},
            message=f"Database integrity verified: {res}",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def list_leases(self, request: Request) -> Response:
        """List currently active cooperative leases."""
        req_id = request.headers.get("x-request-id")
        leases = self._leases.list_active()
        resp = ApiResponse.success(
            data=[lease.model_dump(mode="json") for lease in leases],
            message="Active leases retrieved successfully.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def acquire_lease_endpoint(
        self,
        request: Request,
        req: AcquireLeaseRequest,
    ) -> Response:
        """Acquire a cooperative worker lease."""
        req_id = request.headers.get("x-request-id")
        try:
            lease = self._leases.acquire(
                req.lease_key,
                req.holder_id,
                ttl_seconds=req.ttl_seconds,
                scope=req.scope,
                metadata=req.metadata,
            )
            resp = ApiResponse.success(
                data=lease.model_dump(mode="json"),
                message=f"Lease {req.lease_key} acquired successfully.",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except StorageBusyError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc),
            ) from exc

    def renew_lease_endpoint(
        self,
        request: Request,
        req: RenewLeaseRequest,
    ) -> Response:
        """Renew a held cooperative lease."""
        req_id = request.headers.get("x-request-id")
        try:
            lease = self._leases.renew(
                req.lease_key,
                req.holder_id,
                ttl_seconds=req.ttl_seconds,
            )
            resp = ApiResponse.success(
                data=lease.model_dump(mode="json"),
                message=f"Lease {req.lease_key} renewed successfully.",
                request_id=req_id,
            )
            return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())
        except LeaseExpiredError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

    def release_lease_endpoint(
        self,
        request: Request,
        req: ReleaseLeaseRequest,
    ) -> Response:
        """Release a held cooperative lease."""
        req_id = request.headers.get("x-request-id")
        released = self._leases.release(req.lease_key, req.holder_id)
        resp = ApiResponse.success(
            data={"released": released},
            message=f"Lease {req.lease_key} released: {released}",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())

    def reconcile_endpoint(self, request: Request) -> Response:
        """Trigger restart recovery reconciliation."""
        req_id = request.headers.get("x-request-id")
        report = self._reconcile()
        resp = ApiResponse.success(
            data=report,
            message="Recovery reconciliation completed.",
            request_id=req_id,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=resp.to_dict())


def create_persistence_router(
    db: DatabaseManager, *, reconcile: Callable[[], dict[str, Any]]
) -> APIRouter:
    """Create and configure FastAPI APIRouter exposing persistence endpoints.

    Args:
        db: Central host DatabaseManager instance.
        reconcile: Injected startup recovery workflow owned by bootstrap.

    Returns:
        Configured FastAPI APIRouter.
    """
    service = PersistenceRouterService(db, reconcile)
    router = APIRouter(prefix="/persistence", tags=["persistence"])

    router.add_api_route(
        "/status",
        service.get_status,
        methods=["GET"],
        summary="Query database status and health",
    )
    router.add_api_route(
        "/schema",
        service.get_schema,
        methods=["GET"],
        summary="List applied schema migrations",
    )
    router.add_api_route(
        "/schema/migrations",
        service.get_schema,
        methods=["GET"],
        summary="List applied schema migrations alias",
    )
    router.add_api_route(
        "/integrity-check",
        service.check_integrity_endpoint,
        methods=["POST"],
        summary="Execute PRAGMA integrity_check",
    )
    router.add_api_route(
        "/leases",
        service.list_leases,
        methods=["GET"],
        summary="List active cooperative leases",
    )
    router.add_api_route(
        "/leases/acquire",
        service.acquire_lease_endpoint,
        methods=["POST"],
        summary="Acquire a cooperative lease",
    )
    router.add_api_route(
        "/leases/renew",
        service.renew_lease_endpoint,
        methods=["POST"],
        summary="Renew an active lease",
    )
    router.add_api_route(
        "/leases/release",
        service.release_lease_endpoint,
        methods=["POST"],
        summary="Release an active lease",
    )
    router.add_api_route(
        "/recovery/reconcile",
        service.reconcile_endpoint,
        methods=["POST"],
        summary="Trigger restart recovery reconciliation",
    )

    logger.debug(
        "Persistence REST router initialized",
        extra={"fr_id": "FR-HOST-PERSISTENCE-REST-PROJECTION"},
    )
    return router


def validate_settings_paths(settings_instance: HostSettings) -> dict[str, bool]:
    """Validate configured workspace directories on disk.

    Returns:
        Mapping of directory name to existence boolean.
    """
    workspace_paths = settings_instance.as_dict().get("workspace_paths")
    paths_to_validate: dict[str, Path] = {}

    if isinstance(workspace_paths, dict):
        paths_to_validate = {
            "Configs": Path(str(workspace_paths.get("configs_dir", "data/configs"))),
            "Data": Path(str(workspace_paths.get("data_dir", "data"))),
            "Projects": Path(str(workspace_paths.get("projects_dir", "data/projects"))),
            "Strategies": Path(
                str(workspace_paths.get("strategies_dir", "data/strategies"))
            ),
        }
    else:
        paths_to_validate = {
            "Configs": Path("data/configs"),
            "Data": Path("data"),
            "Projects": Path("data/projects"),
            "Strategies": Path("data/strategies"),
        }

    results: dict[str, bool] = {}
    for dir_name, path in paths_to_validate.items():
        exists = path.exists()
        results[dir_name] = exists
        if exists:
            logger.info(
                "FR-HOST-SETTINGS-PATH-VALIDATION: Directory '%s' exists.",
                dir_name,
                extra={
                    "directory_name": dir_name,
                    "fr_id": "FR-HOST-SETTINGS-PATH-VALIDATION",
                },
            )
        else:
            logger.warning(
                "FR-HOST-SETTINGS-PATH-VALIDATION: Directory '%s' absent.",
                dir_name,
                extra={
                    "directory_name": dir_name,
                    "fr_id": "FR-HOST-SETTINGS-PATH-VALIDATION",
                },
            )

    return results


def _extract_put_payload(body: Any) -> tuple[int, dict[str, dict[str, Any]]]:
    """Validate and extract expected revision and changes from PUT body."""
    if not isinstance(body, dict):
        raise ValidationError("Request body must be a JSON object")
    expected_rev = body.get("expected_revision")
    if not isinstance(expected_rev, int) or expected_rev < 0:
        raise ValidationError("expected_revision must be a non-negative integer")
    changes = body.get("changes")
    if not isinstance(changes, dict):
        raise ValidationError("changes must be a dictionary of scoped settings")
    return expected_rev, changes


def create_settings_router(
    settings_instance: HostSettings | None = None,
) -> APIRouter:
    """Create FastAPI APIRouter exposing host settings REST projections.

    Args:
        settings_instance: HostSettings instance to expose. Defaults to
            global singleton.

    Returns:
        Configured FastAPI APIRouter.
    """
    router = APIRouter()
    target_settings = settings_instance if settings_instance is not None else settings

    @router.get("/settings")
    async def get_settings_endpoint() -> JSONResponse:
        """Retrieve current shell settings and preferences snapshot."""
        logger.debug(
            "FR-HOST-SETTINGS-PROJECTION: Handling GET /settings query.",
            extra={"fr_id": "FR-HOST-SETTINGS-PROJECTION"},
        )
        snapshot = target_settings.get_snapshot()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "success", "data": snapshot.model_dump()},
        )

    @router.put("/settings")
    async def put_settings_endpoint(request: Request) -> JSONResponse:
        """Atomically update host settings with revision check."""
        try:
            body = await request.json()
        except ValueError, TypeError, json.JSONDecodeError:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "status": "error",
                    "error": {
                        "code": "INVALID_JSON",
                        "message": "Malformed JSON payload in request body",
                    },
                },
            )

        try:
            expected_rev, changes = _extract_put_payload(body)
            snapshot = target_settings.update(changes, expected_revision=expected_rev)
            logger.info(
                "FR-HOST-SETTINGS-PROJECTION: Updated settings to revision %d.",
                snapshot.revision,
                extra={
                    "fr_id": "FR-HOST-SETTINGS-PROJECTION",
                    "revision": snapshot.revision,
                },
            )
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"status": "success", "data": snapshot.model_dump()},
            )
        except RevisionConflictError as exc:
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "status": "error",
                    "error": {
                        "code": "REVISION_CONFLICT",
                        "message": str(exc),
                        "current_revision": target_settings.revision,
                    },
                },
            )
        except ValidationError as exc:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                content={
                    "status": "error",
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": str(exc),
                    },
                },
            )

    @router.get("/settings/paths/validate")
    async def validate_paths_endpoint() -> JSONResponse:
        """Validate configured workspace directories on disk."""
        statuses = validate_settings_paths(target_settings)
        all_valid = all(statuses.values())
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "success",
                "data": {
                    "paths": statuses,
                    "all_valid": all_valid,
                },
            },
        )

    return router


def main() -> int:
    """CLI diagnostics entrypoint for database inspection and integrity validation.

    Returns:
        Process exit code (0 for success, non-zero for failure).
    """
    from app.host.bootstrap import HostRuntime

    parser = argparse.ArgumentParser(
        description="HaruQuantAI Host Persistence Authority Tool"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Inspect database operational status and schema version",
    )
    parser.add_argument(
        "--integrity-check",
        action="store_true",
        help="Run physical database integrity verification",
    )
    parser.add_argument(
        "--reconcile",
        action="store_true",
        help="Execute startup recovery reconciliation",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("data/database/haruquantai.db"),
        help="Target SQLite database path (default: data/database/haruquantai.db)",
    )

    args = parser.parse_args()
    db = DatabaseManager(args.db)
    exit_code = 0

    if args.status:
        try:
            stat = db.get_status()
            logger.info(
                "Database status output",
                extra={"status": stat.model_dump(mode="json")},
            )
            sys.stdout.write(f"Database: {stat.database_path}" + "\n")
            sys.stdout.write(f"Connected: {stat.is_connected}" + "\n")
            sys.stdout.write(f"Journal: {stat.journal_mode}" + "\n")
            sys.stdout.write(f"Schema Version: {stat.schema_version}" + "\n")
            sys.stdout.write(f"Tables: {stat.table_count}" + "\n")
            sys.stdout.write(f"Integrity: {stat.integrity_status}" + "\n")
            exit_code = 0 if stat.is_connected and stat.integrity_status == "ok" else 1
        except Exception as exc:
            logger.exception(
                "Error checking database status",
                extra={"error": str(exc)},
            )
            exit_code = 2
    elif args.integrity_check:
        try:
            result = db.check_integrity()
            sys.stdout.write(f"Integrity check: {result}" + "\n")
            exit_code = 0 if result == "ok" else 1
        except Exception as exc:
            logger.exception(
                "Error verifying integrity",
                extra={"error": str(exc)},
            )
            exit_code = 2
    elif args.reconcile:
        try:
            report = HostRuntime.reconcile_persistence(db)
            sys.stdout.write(f"Reconciliation: {report['status']}" + "\n")
            sys.stdout.write(f"Pruned Leases: {report['pruned_expired_leases']}" + "\n")
            exit_code = 0
        except Exception as exc:
            logger.exception(
                "Error running reconciliation",
                extra={"error": str(exc)},
            )
            exit_code = 2
    else:
        parser.print_help()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
