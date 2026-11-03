"""System diagnostics, hardware inspection, memory watchdog, and resource governance.

Description:
    Provides host resource custody and diagnostics: read-only SQLite probes,
    workspace readiness, filesystem writability, hardware telemetry, worker
    allocation (max(1, cpu_cores - 2)), CPU affinity, GPU qualification, CPU
    benchmarks, 15% RAM Memory Watchdog, DataFrame guards, and scratch sandboxes.

Purpose:
    FEAT-HOST-RESOURCES: Host system diagnostics, hardware inspection, memory
    watchdog, and resource governance.

Key Capabilities:
    - FR-HOST-RESOURCES-WORKSPACE-DIRS: Dirs (inspect_workspace_directories -> INFO).
    - FR-HOST-RESOURCES-PROBE-DATABASE: Probe DB/WAL/tables (probe_database -> DEBUG).
    - FR-HOST-RESOURCES-PROBE-CPU: Probe CPU topology and load (probe_cpu -> DEBUG).
    - FR-HOST-RESOURCES-PROBE-MEMORY: Probe RAM headroom (probe_memory -> DEBUG).
    - FR-HOST-RESOURCES-PROBE-DISK: Probe volume capacity (probe_disk -> DEBUG).
    - FR-HOST-RESOURCES-PROBE-PROCESS: Probe process health (probe_process -> DEBUG).
    - FR-HOST-RESOURCES-PROBE-STORAGE: Storage writability (probe_storage -> DEBUG).
    - FR-HOST-RESOURCES-PROBE-HARDWARE: Hardware telemetry (probe_hardware -> DEBUG).
    - FR-HOST-RESOURCES-PROBE-HEALTH: Health snapshot (inspect_resources -> INFO).
    - FR-HOST-RESOURCES-WORKER-ALLOCATION: Pool (calculate_worker_allocation -> INFO).
    - FR-HOST-RESOURCES-CORE-AFFINITY: CPU core affinity (apply_cpu_affinity -> INFO).
    - FR-HOST-RESOURCES-GPU-ACCELERATION: GPU (inspect_gpu_qualification -> DEBUG).
    - FR-HOST-RESOURCES-BENCHMARK: Execute CPU benchmark (run_cpu_benchmark -> INFO).
    - FR-HOST-RESOURCES-MEMORY-WATCHDOG: 15% RAM floor (check_memory_headroom -> DEBUG).
    - FR-HOST-RESOURCES-SCRATCH-SANDBOX: Job scratch dir (allocate_job_scratch -> INFO).

Python API Usage:
    ```python
    from app.core.host.resources import calculate_worker_allocation, probe_hardware

    workers = calculate_worker_allocation(probe_hardware().cpu_count_logical)
    ```

CLI Usage:
    ```bash
    uv run python -m app.core.host.resources
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
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psutil

from app.core.host.logging import get_logger
from app.core.host.persistence import HostPersistence
from app.core.host.settings import settings as host_settings

__all__ = (
    "DEFAULT_MEMORY_OVER_LIMIT_COUNT",
    "DEFAULT_ONE_TIME_MEMORY_LIMIT_PCT",
    "MemoryProtectionError",
    "MemoryWatchdog",
    "ResourceMonitor",
    "allocate_job_scratch",
    "apply_cpu_affinity",
    "calculate_worker_allocation",
    "check_available_memory",
    "check_memory_headroom",
    "cleanup_job_scratch",
    "evaluate_dataframe_guard",
    "get_available_processors",
    "get_worker_capacity",
    "inspect_resources",
    "inspect_workspace_directories",
    "job_scratch_sandbox",
    "probe_cpu",
    "probe_hardware",
    "probe_memory",
    "resource_manager",
    "run_cpu_benchmark",
)

logger = get_logger(__name__)

WORKSPACE_DIRS_FR = "FR-HOST-RESOURCES-WORKSPACE-DIRS"
PROBE_DATABASE_FR = "FR-HOST-RESOURCES-PROBE-DATABASE"
PROBE_CPU_FR = "FR-HOST-RESOURCES-PROBE-CPU"
PROBE_MEMORY_FR = "FR-HOST-RESOURCES-PROBE-MEMORY"
PROBE_DISK_FR = "FR-HOST-RESOURCES-PROBE-DISK"
PROBE_PROCESS_FR = "FR-HOST-RESOURCES-PROBE-PROCESS"
PROBE_STORAGE_FR = "FR-HOST-RESOURCES-PROBE-STORAGE"
PROBE_HARDWARE_FR = "FR-HOST-RESOURCES-PROBE-HARDWARE"
PROBE_HEALTH_FR = DIAGNOSTICS_FR = "FR-HOST-RESOURCES-PROBE-HEALTH"
WORKER_ALLOCATION_FR = WORKER_CAPACITY_FR = "FR-HOST-RESOURCES-WORKER-ALLOCATION"
CORE_AFFINITY_FR = "FR-HOST-RESOURCES-CORE-AFFINITY"
GPU_ACCELERATION_FR = "FR-HOST-RESOURCES-GPU-ACCELERATION"
BENCHMARK_FR = "FR-HOST-RESOURCES-BENCHMARK"
MEMORY_WATCHDOG_FR = "FR-HOST-RESOURCES-MEMORY-WATCHDOG"
SCRATCH_SANDBOX_FR = "FR-HOST-RESOURCES-SCRATCH-SANDBOX"

DEFAULT_ONE_TIME_MEMORY_LIMIT_PCT: float = 90.0
DEFAULT_MEMORY_OVER_LIMIT_COUNT: int = 15
MIN_FREE_DISK_PCT: float = 2.0
MIN_AVAILABLE_RAM_PCT: float = 15.0
DEFAULT_SCRATCH_ROOT: Path = Path("data/scratch")
BENCHMARK_CHECK_INTERVAL: int = 10_000


class MemoryProtectionError(MemoryError, RuntimeError):
    """Raised when memory consumption exceeds limits (SQMemoryProtectionError)."""


type PathLike = Path | str | None


def _log(level: str, fr_id: str, msg: str, **extra: Any) -> None:
    """Emit structured FR log record with fr_id context."""
    getattr(logger, level)("%s: %s", fr_id, msg, extra={"fr_id": fr_id, **extra})


def normalize_path(path: str) -> str:
    """Render filesystem paths consistently in diagnostic records."""
    return Path(path).as_posix()


@dataclass(frozen=True)
class DatabaseProbe:
    """Diagnostic metrics for active persistence database."""

    path: str
    exists: bool
    size_bytes: int
    wal_exists: bool
    wal_size_bytes: int
    table_count: int | None
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
    started_at: str | None = None
    completed_at: str | None = None
    duration_seconds: float | None = None
    iterations_completed: int = 0
    throughput_ops_per_sec: float | None = None
    results: BenchmarkResults | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


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


type StatusCb = Callable[[MemoryWatchdogStatus], None] | None
type ProbeFn = Callable[[], MemoryObservation] | None


def _extract_workspace_paths(settings: Any = None) -> dict[str, str]:
    """Resolve directory paths mapping from host settings or defaults."""
    eff = settings or host_settings
    ws = getattr(eff, "workspace_paths", None) if eff else None
    if ws and hasattr(ws, "as_dict"):
        return dict(ws.as_dict())
    if isinstance(ws, dict):
        return dict(ws)
    d = {"configs_dir": "data/presets", "data_dir": "data/market"}
    return {**d, "projects_dir": "data/projects", "strategies_dir": "data/strategies"}


def inspect_workspace_directories(settings: Any = None) -> dict[str, bool]:
    """Inspect existence of directories configured in settings.workspace_paths."""
    results: dict[str, bool] = {}
    for name, dir_path in sorted(_extract_workspace_paths(settings).items()):
        p = Path(dir_path).resolve()
        ok = p.exists() and p.is_dir()
        results[name] = ok
        sp = normalize_path(str(p))
        verb = "available" if ok else "absent"
        _log(
            "info" if ok else "warning",
            WORKSPACE_DIRS_FR,
            f"dir '{name}' {verb} at {sp}",
        )
    return results


def probe_database(
    settings: Any = None, *, persistence: HostPersistence | None = None
) -> DatabaseProbe:
    """Perform read-only diagnostic inspection on active database."""
    _ = settings
    gw = persistence or HostPersistence()
    p_str = normalize_path(str(gw.database_path))
    if not gw.database_path.exists():
        _log("warning", PROBE_DATABASE_FR, f"database not found at {p_str}", path=p_str)
        return DatabaseProbe(p_str, False, 0, False, 0, 0, "Database file missing")

    wal = gw.database_path.with_name(f"{gw.database_path.name}-wal")
    wal_sz = wal.stat().st_size if wal.exists() else 0
    err_msg: str | None = None
    try:
        if not gw.read_records("host_settings", limit=1)["success"]:
            err_msg = "Database readiness probe failed"
            _log("warning", PROBE_DATABASE_FR, err_msg)
    except Exception as err:  # noqa: BLE001
        err_msg = str(err)
        _log("exception", PROBE_DATABASE_FR, f"database read failed on {p_str}")

    _log("debug", PROBE_DATABASE_FR, f"probed database at {p_str}", table_count=None)
    sz = gw.database_path.stat().st_size
    return DatabaseProbe(p_str, True, sz, wal.exists(), wal_sz, None, err_msg)


def get_available_processors() -> int:
    """Detect available logical core count (donor CpuInfo.getAvailableProcessors)."""
    sys_cores = psutil.cpu_count(logical=True)
    rt_cores = os.cpu_count()
    cores = max(sys_cores or 0, rt_cores or 0, 1)
    _log("debug", PROBE_CPU_FR, f"cores detected: {cores}")
    return cores


def probe_cpu() -> CpuObservation:
    """Probe host CPU topology, frequency, and current load."""
    try:
        logical = get_available_processors()
        physical = psutil.cpu_count(logical=False)
        f_val = round(float(f.current), 2) if (f := psutil.cpu_freq()) else None
        u_val = round(max(0.0, min(100.0, float(psutil.cpu_percent(interval=None)))), 2)
        _log("debug", PROBE_CPU_FR, f"CPU probe ok: cores={logical}, util={u_val:.1f}%")
        return CpuObservation(logical, physical, f_val, u_val, True)
    except (psutil.Error, OSError, ValueError, TypeError) as exc:
        _log("warning", PROBE_CPU_FR, f"CPU telemetry probe failed: {exc}")
        return CpuObservation(os.cpu_count() or 1, None, None, None, False)


def probe_memory() -> MemoryObservation:
    """Probe physical host memory capacity and current availability."""
    try:
        m = psutil.virtual_memory()
        u_pct = round(max(0.0, min(100.0, float(m.percent))), 2)
        t_mb, a_mb = round(m.total / 1048576, 2), round(m.available / 1048576, 2)
        _log("debug", PROBE_MEMORY_FR, f"RAM ok: {a_mb:.0f}MB avail / {t_mb:.0f}MB")
        return MemoryObservation(m.total, m.available, m.used, u_pct, t_mb, a_mb, True)
    except (psutil.Error, OSError, ValueError, TypeError) as exc:
        _log("warning", PROBE_MEMORY_FR, f"memory telemetry probe failed: {exc}")
        return MemoryObservation(0, 0, 0, 0.0, 0.0, 0.0, False)


def probe_disk(target_path: Path | str = ".") -> DiskObservation:
    """Probe storage capacity for target volume with path sanitization."""
    p_obj = Path(target_path).resolve()
    mnt = normalize_path(str(p_obj.anchor or p_obj))
    try:
        d = psutil.disk_usage(str(p_obj))
        raw_pct = (d.free / d.total) * 100.0 if d.total > 0 else 0.0
        f_pct = round(max(0.0, min(100.0, raw_pct)), 2)
        _log("debug", PROBE_DISK_FR, f"disk ok: {mnt} ({f_pct:.1f}% free)")
        return DiskObservation(mnt, d.total, d.free, d.used, f_pct, True)
    except (psutil.Error, OSError, ValueError, TypeError) as exc:
        _log("warning", PROBE_DISK_FR, f"disk telemetry probe failed: {exc}")
        return DiskObservation(mnt, 0, 0, 0, 0.0, False)


def probe_process() -> ProcessObservation:
    """Probe current host Python process health, memory, and threads."""
    try:
        p = psutil.Process()
        pid, cpu_v = p.pid, round(max(0.0, float(p.cpu_percent(interval=None))), 2)
        rss_b = p.memory_info().rss
        rss_mb = round(rss_b / (1024 * 1024), 2)
        open_f: int | None = None
        try:
            open_f = len(p.open_files())
        except psutil.AccessDenied, OSError:
            open_f = None
        th, up = p.num_threads(), max(0.0, round(time.time() - p.create_time(), 2))
        _log("debug", PROBE_PROCESS_FR, f"process probe ok (pid={pid})")
        return ProcessObservation(pid, cpu_v, rss_b, rss_mb, th, open_f, up, True)
    except (psutil.Error, OSError, ValueError, TypeError) as exc:
        _log("warning", PROBE_PROCESS_FR, f"process telemetry probe failed: {exc}")
        return ProcessObservation(os.getpid(), None, 0, 0.0, 1, None, 0.0, False)


def _check_dir_writable(target_dir: Path) -> bool:
    """Verify target directory can be created and written to."""
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        test_file = target_dir / ".probe_test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def probe_storage(root_path: PathLike = None, settings: Any = None) -> StorageProbe:
    """Check filesystem write permissions and disk space capacity."""
    if root_path:
        root, data_dir = Path(root_path).resolve(), Path(root_path).resolve() / "data"
    elif settings and settings.get("workspace_paths", "data_dir"):
        data_dir = Path(settings.get("workspace_paths", "data_dir")).resolve()
        is_data = data_dir.name == "data"
        root = data_dir.parent.resolve() if is_data else Path.cwd().resolve()
    else:
        root, data_dir = Path.cwd().resolve(), Path.cwd().resolve() / "data"

    l_ok = _check_dir_writable(data_dir / "logs")
    db_ok = _check_dir_writable(data_dir / "database")
    u = shutil.disk_usage(root)
    f_pct = round((u.free / u.total * 100.0) if u.total > 0 else 0.0, 2)
    n_root = normalize_path(str(root))
    _log("debug", PROBE_STORAGE_FR, f"probed storage at {n_root} ({f_pct:.1f}% free)")
    return StorageProbe(n_root, l_ok, db_ok, u.free, u.total, f_pct)


def probe_hardware() -> HardwareProbe:
    """Gather machine hardware metrics via psutil."""
    c, m = probe_cpu(), probe_memory()
    u_pct = c.utilization_pct or 0.0
    _log(
        "debug", PROBE_HARDWARE_FR, f"hw: cpu={c.logical_cores}, ram={m.used_pct:.1f}%"
    )
    a1 = (c.logical_cores, c.physical_cores, u_pct)
    a2 = (m.total_bytes, m.available_bytes, m.used_pct)
    return HardwareProbe(*a1, *a2)


def inspect_resources(
    root_path: PathLike = None, settings: Any = None
) -> HostHealthReport:
    """Coordinate host probes and generate complete health snapshot."""
    db = probe_database(settings=settings)
    st = probe_storage(root_path, settings=settings)
    hw = probe_hardware()
    c1 = db.exists and not db.error and st.logs_dir_writable
    ok = bool(c1 and st.database_dir_writable and st.free_pct > MIN_FREE_DISK_PCT)
    status = "HEALTHY" if ok else "DEGRADED"
    det = f"tables={db.table_count}" if ok else f"db_err={db.error}"
    _log("info" if ok else "warning", PROBE_HEALTH_FR, f"host health: {status} ({det})")
    return HostHealthReport(status, db, st, hw, datetime.now(UTC).isoformat())


def calculate_worker_allocation(
    total_cores: int, mode: str = "reserve-two", custom_cores: int = 1
) -> int:
    """Derive worker pool allocation from total logical cores and selected mode."""
    sc = max(1, total_cores)
    nm = mode.strip().lower().replace("_", "-")
    modes = {"single": 1, "1": 1, "maximum": sc, "all": sc}
    modes.update({"reserve-one": max(1, sc - 1), "all-except-one": max(1, sc - 1)})
    fallback = min(max(1, custom_cores), sc) if nm == "custom" else max(1, sc - 2)
    alloc = modes.get(nm, fallback)

    _log("info", WORKER_ALLOCATION_FR, f"workers (mode={nm}) -> {alloc}")
    return alloc


def get_worker_capacity(
    settings: Any = None, mode: str | None = None, custom_cores: int | None = None
) -> WorkerCapacity:
    """Derive consolidated worker capacity, CPU core affinity, and GPU status."""
    eff = settings or host_settings
    cfg = getattr(eff, "config_cpu", None) if eff else None
    eff_mode = mode or (
        str(cfg.core_usage) if cfg and hasattr(cfg, "core_usage") else "reserve-two"
    )
    eff_custom = (
        custom_cores
        if custom_cores is not None
        else (int(cfg.custom_cores) if cfg and hasattr(cfg, "custom_cores") else 1)
    )
    tc = get_available_processors()
    alloc = calculate_worker_allocation(tc, eff_mode, eff_custom)
    aff_sup, aff_cur = inspect_cpu_affinity()
    gpu_ok = inspect_gpu_qualification()
    _log("info", WORKER_CAPACITY_FR, f"worker capacity resolved: {alloc}/{tc} workers")
    c_val = eff_custom if eff_mode.lower().replace("_", "-") == "custom" else None
    has_aff = aff_sup and aff_cur is not None
    return WorkerCapacity(tc, alloc, eff_mode, c_val, aff_sup, has_aff, gpu_ok)


def inspect_cpu_affinity() -> tuple[bool, list[int] | None]:
    """Inspect if CPU core affinity is supported on current OS."""
    try:
        if hasattr(p := psutil.Process(), "cpu_affinity"):
            cur = list(p.cpu_affinity())
            _log("debug", CORE_AFFINITY_FR, "CPU affinity supported", affinity=cur)
            return True, cur
        _log("debug", CORE_AFFINITY_FR, f"affinity unsupported: {platform.system()}")
    except (AttributeError, OSError, psutil.AccessDenied) as exc:
        _log("debug", CORE_AFFINITY_FR, f"CPU affinity inspection exception: {exc}")
    return False, None


def apply_cpu_affinity(cores: list[int]) -> bool:
    """Apply CPU core affinity to the host process if supported by OS."""
    if not cores:
        _log("warning", CORE_AFFINITY_FR, "empty core list for affinity application")
        return False
    try:
        p = psutil.Process()
        if hasattr(p, "cpu_affinity"):
            p.cpu_affinity(cores)
            _log("info", CORE_AFFINITY_FR, f"applied CPU core affinity to {cores!r}")
            return True
        _log("warning", CORE_AFFINITY_FR, f"affinity unsupported: {platform.system()}")
        return False
    except (psutil.Error, OSError, ValueError) as exc:
        _log("warning", CORE_AFFINITY_FR, f"failed applying CPU affinity: {exc}")
        return False


def inspect_gpu_qualification() -> bool:
    """Safely inspect if qualified GPU acceleration is available."""
    cv = os.environ.get("CUDA_VISIBLE_DEVICES", "").strip()
    cuda_env = os.environ.get("CUDA_PATH") or os.environ.get("NVIDIA_VISIBLE_DEVICES")
    ok = bool((cv and cv not in ("-1", "none", "NONE")) or cuda_env)
    _log("debug", GPU_ACCELERATION_FR, f"GPU detection inspected: available={ok}")
    return ok


def check_memory_headroom(
    min_available_pct: float = MIN_AVAILABLE_RAM_PCT,
    *,
    policy: str = "reject",
    memory_obs: MemoryObservation | None = None,
) -> MemoryWatchdogStatus:
    """Evaluate available system RAM against the 15% memory watchdog threshold."""
    obs = memory_obs if memory_obs is not None else probe_memory()
    thresh = max(0.0, min(100.0, float(min_available_pct)))
    if obs.is_available:
        tot = obs.total_bytes
        ratio = (
            (obs.available_bytes / tot * 100.0) if tot > 0 else (100.0 - obs.used_pct)
        )
        a_pct = round(max(0.0, min(100.0, ratio)), 2)
    else:
        a_pct = 100.0
    pressured = obs.is_available and a_pct < thresh
    pol = policy.strip().lower()
    act = ("PAUSE" if pol == "pause" else "REJECT") if pressured else "ALLOW"
    lvl = "warning" if pressured else "debug"
    _log(lvl, MEMORY_WATCHDOG_FR, f"RAM: {a_pct:.1f}% -> {act}", available_pct=a_pct)
    a1 = (a_pct, obs.used_pct, obs.available_bytes, obs.total_bytes)
    a2 = (thresh, pressured, act, datetime.now(UTC).isoformat())
    return MemoryWatchdogStatus(*a1, *a2)


def check_available_memory(
    memory_obs: MemoryObservation | None = None,
    over_limit_count: int = 0,
    one_time_limit_pct: float = DEFAULT_ONE_TIME_MEMORY_LIMIT_PCT,
    consecutive_threshold: int = DEFAULT_MEMORY_OVER_LIMIT_COUNT,
) -> None:
    """Evaluate memory usage against donor safety limits and raise if exceeded."""
    obs = memory_obs if memory_obs is not None else probe_memory()
    cur = obs.used_pct
    if over_limit_count > consecutive_threshold or cur > one_time_limit_pct:
        msg = f"Memory usage is too high ({int(cur)}%). Please increase memory."
        _log("error", MEMORY_WATCHDOG_FR, f"Memory usage limit reached: {cur:.1f}%")
        raise MemoryProtectionError(msg)


def evaluate_dataframe_guard(
    row_count: int, *, max_rows: int = 5_000_000, mode: str = "warn"
) -> str:
    """Evaluate data-frame size against configured warn/stop/off guard policy."""
    nm = mode.strip().lower()
    if nm == "off" or row_count <= max_rows:
        _log("debug", MEMORY_WATCHDOG_FR, f"dataframe guard passed (rows={row_count})")
        return "ALLOW"
    if nm == "stop":
        _log("error", MEMORY_WATCHDOG_FR, f"dataframe guard stopped (rows={row_count})")
        raise MemoryError(f"Rows ({row_count}) exceeds stop limit ({max_rows}).")
    _log("warning", MEMORY_WATCHDOG_FR, f"dataframe guard warning (rows={row_count})")
    return "WARN"


def run_memory_cleanup() -> int:
    """Execute explicit garbage collection and log reclaimed object count."""
    rec = gc.collect()
    _log(
        "info",
        MEMORY_WATCHDOG_FR,
        f"memory cleanup: reclaimed={rec}",
        reclaimed_objects=rec,
    )
    return rec


class MemoryWatchdog:
    """Active memory monitor rejecting or pausing tasks when available RAM < 15%."""

    def __init__(
        self,
        min_available_pct: float = MIN_AVAILABLE_RAM_PCT,
        *,
        policy: str = "reject",
        poll_interval_seconds: float = 1.0,
        probe_fn: ProbeFn = None,
    ) -> None:
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
        self._over_limit_count: int = 0

    @property
    def min_available_pct(self) -> float:
        """Return configured minimum available RAM percentage threshold."""
        return self._min_available_pct

    @property
    def policy(self) -> str:
        """Return configured enforcement policy ('reject' or 'pause')."""
        return self._policy

    @property
    def over_limit_count(self) -> int:
        """Return count of consecutive samples exceeding memory usage limit."""
        with self._lock:
            return self._over_limit_count

    def register_callbacks(
        self, *, on_pressure: StatusCb = None, on_recovery: StatusCb = None
    ) -> None:
        """Register callbacks invoked when RAM drops below or recovers above 15%."""
        with self._lock:
            if on_pressure is not None:
                self._pressure_callbacks.append(on_pressure)
            if on_recovery is not None:
                self._recovery_callbacks.append(on_recovery)

    def check(self, *, policy: str | None = None) -> MemoryWatchdogStatus:
        """Evaluate current memory headroom and invoke state-transition callbacks."""
        eff_pol = policy if policy is not None else self._policy
        status = check_memory_headroom(
            self._min_available_pct, policy=eff_pol, memory_obs=self._probe_fn()
        )
        with self._lock:
            prev, self._last_status = self._last_status, status
            self._over_limit_count = (
                (self._over_limit_count + 1) if status.is_pressured else 0
            )
            if status.is_pressured:
                _log(
                    "debug",
                    MEMORY_WATCHDOG_FR,
                    f"limit exceeded {self._over_limit_count}x",
                )
            p_cbs, r_cbs = (
                list(self._pressure_callbacks),
                list(self._recovery_callbacks),
            )

        if status.is_pressured:
            for cb in p_cbs:
                cb(status)
        elif prev is not None and prev.is_pressured and not status.is_pressured:
            for cb in r_cbs:
                cb(status)
        return status

    def check_available_memory(
        self,
        one_time_limit_pct: float = DEFAULT_ONE_TIME_MEMORY_LIMIT_PCT,
        consecutive_threshold: int = DEFAULT_MEMORY_OVER_LIMIT_COUNT,
    ) -> None:
        """Evaluate memory usage against consecutive and one-time limit thresholds."""
        with self._lock:
            st, cnt = self._last_status, self._over_limit_count
        obs = MemoryObservation(0, 0, 0, st.used_pct, 0.0, 0.0, True) if st else None
        check_available_memory(obs, cnt, one_time_limit_pct, consecutive_threshold)

    def start(self) -> None:
        """Start background daemon thread monitoring system RAM headroom."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._monitor_loop, name="HostMemWatchdog", daemon=True
            )
            self._thread.start()
        _log("info", MEMORY_WATCHDOG_FR, f"started watchdog (policy={self._policy})")

    def stop(self) -> None:
        """Stop background memory watchdog monitor thread."""
        self._stop_event.set()
        with self._lock:
            thread, self._thread = self._thread, None
        if thread is not None and thread.is_alive():
            thread.join(timeout=2.0)
        _log("info", MEMORY_WATCHDOG_FR, "stopped background memory watchdog")

    def _monitor_loop(self) -> None:
        """Background polling loop checking RAM headroom."""
        while not self._stop_event.is_set():
            self.check()
            self._stop_event.wait(self._poll_interval)


def _validate_sandbox_job_id(job_id: str) -> str:
    """Validate job_id to prevent path traversal outside the scratch root."""
    cleaned = job_id.strip()
    if not cleaned or any(sep in cleaned for sep in ("..", "/", "\\", ":")):
        msg = f"rejected unsafe job_id '{job_id}' for scratch sandbox"
        _log("error", SCRATCH_SANDBOX_FR, msg, job_id=job_id)
        raise ValueError(f"Invalid job_id for scratch sandbox: '{job_id}'")
    return cleaned


def _resolve_scratch_target(
    job_id: str, base_dir: PathLike = None
) -> tuple[str, Path, Path]:
    """Resolve and validate root and target path for a per-job scratch directory."""
    safe_id = _validate_sandbox_job_id(job_id)
    root = Path(base_dir if base_dir is not None else DEFAULT_SCRATCH_ROOT).resolve()
    return safe_id, root, (root / safe_id).resolve()


def allocate_job_scratch(job_id: str, base_dir: PathLike = None) -> Path:
    """Allocate an isolated temporary scratch directory for a job."""
    safe_id, root, target = _resolve_scratch_target(job_id, base_dir)
    if root not in target.parents:
        _log("error", SCRATCH_SANDBOX_FR, f"scratch path escaped root for {safe_id}")
        raise ValueError(f"Scratch path escaped containment for job '{safe_id}'")
    target.mkdir(parents=True, exist_ok=True)
    _log("info", SCRATCH_SANDBOX_FR, f"allocated scratch for {safe_id}")
    return target


def cleanup_job_scratch(job_id: str, base_dir: PathLike = None) -> bool:
    """Remove the isolated temporary scratch directory for a completed/cancelled job."""
    safe_id, root, target = _resolve_scratch_target(job_id, base_dir)
    if root in target.parents and target.exists():
        shutil.rmtree(target, ignore_errors=True)
        _log(
            "info", SCRATCH_SANDBOX_FR, f"cleaned up scratch sandbox for job {safe_id}"
        )
        return True
    return False


@contextmanager
def job_scratch_sandbox(job_id: str, base_dir: PathLike = None) -> Generator[Path]:
    """Context manager allocating and cleaning up a job scratch sandbox."""
    scratch_path = allocate_job_scratch(job_id, base_dir=base_dir)
    try:
        yield scratch_path
    finally:
        cleanup_job_scratch(job_id, base_dir=base_dir)


def run_cpu_benchmark(
    iterations: int = 100_000, cancel_event: threading.Event | None = None
) -> BenchmarkResults:
    """Execute real, deterministic computational CPU benchmark."""
    n = max(1, iterations)
    _log("info", BENCHMARK_FR, f"starting CPU benchmark with {n} iterations.")
    start_perf = time.perf_counter()
    accumulator = 1.0
    chk = max(1, min(BENCHMARK_CHECK_INTERVAL, n // 5))

    for idx in range(1, n + 1):
        if cancel_event is not None and (idx % chk == 0) and cancel_event.is_set():
            _log("info", BENCHMARK_FR, f"benchmark cancelled at {idx}/{n}.")
            raise InterruptedError("Benchmark cancelled by caller")
        factor = (idx % 1000) + 1.0
        accumulator += (math.sin(factor) * math.cos(factor)) + math.sqrt(factor)

    _ = accumulator
    el = max(1e-6, time.perf_counter() - start_perf)
    tput, avg_st = round(n / el, 2), round(el / 100.0, 4)
    avg_sh = round(3600.0 / avg_st) if avg_st > 0 else 0
    _log("info", BENCHMARK_FR, f"benchmark finished: duration={el:.4f}s")
    return BenchmarkResults(round(el, 4), n, avg_sh, round((el * 1000.0) / n, 5), tput)


class BenchmarkRunner:
    """Manages synchronous and background benchmark execution lifecycle."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, BenchmarkJob] = {}
        self._cancel_events: dict[str, threading.Event] = {}

    def start_job(self, iterations: int = 100_000) -> BenchmarkJob:
        """Start a new benchmark job in a background worker thread."""
        job_id, evt = f"bench-{uuid.uuid4().hex[:8]}", threading.Event()
        meta = {"requested_iterations": iterations}
        now = datetime.now(UTC).isoformat()
        job = BenchmarkJob(job_id, "running", 0.0, now, metadata=meta)
        with self._lock:
            self._jobs[job_id], self._cancel_events[job_id] = job, evt
        t_args = (job_id, iterations, evt)
        t = threading.Thread(
            target=self._execute_worker,
            args=t_args,
            daemon=True,
            name=f"bench-{job_id}",
        )
        t.start()
        return job

    def _finish_job(
        self,
        job_id: str,
        state: str,
        duration: float,
        *,
        results: BenchmarkResults | None = None,
        error_msg: str | None = None,
        completed: int = 0,
    ) -> None:
        """Update BenchmarkJob state under lock."""
        pct = 100.0 if state == "completed" else 0.0
        with self._lock:
            c = self._jobs.get(job_id)
            tp = results.throughput_ops_per_sec if results else None
            meta = c.metadata if c else {}
            st = c.started_at if c else None
            now = datetime.now(UTC).isoformat()
            self._jobs[job_id] = BenchmarkJob(
                job_id,
                state,
                pct,
                st,
                now,
                duration,
                completed,
                tp,
                results,
                error_msg,
                meta,
            )

    def _execute_worker(
        self, job_id: str, iterations: int, cancel_evt: threading.Event
    ) -> None:
        """Worker thread executing the benchmark computation."""
        t0 = time.perf_counter()
        try:
            res = run_cpu_benchmark(iterations=iterations, cancel_event=cancel_evt)
            self._finish_job(
                job_id,
                "completed",
                res.duration_seconds,
                results=res,
                completed=iterations,
            )
        except (InterruptedError, Exception) as exc:  # noqa: BLE001
            el = round(time.perf_counter() - t0, 4)
            is_cancel = isinstance(exc, InterruptedError)
            st = "cancelled" if is_cancel else "failed"
            msg = "Benchmark cancelled" if is_cancel else str(exc)
            self._finish_job(job_id, st, el, error_msg=msg)

    def get_job(self, job_id: str) -> BenchmarkJob | None:
        """Retrieve status of an existing benchmark job."""
        with self._lock:
            return self._jobs.get(job_id)

    def cancel_job(self, job_id: str) -> bool:
        """Signal cooperative cancellation to a running benchmark job."""
        with self._lock:
            evt = self._cancel_events.get(job_id)
        if evt:
            evt.set()
            _log("info", BENCHMARK_FR, f"signaled cancellation for {job_id}")
        return evt is not None


class ResourceMonitor:
    """Unified custodian for diagnostics, worker sizing, watchdog, and sandboxes."""

    def __init__(
        self,
        *,
        min_available_ram_pct: float = MIN_AVAILABLE_RAM_PCT,
        watchdog_policy: str = "reject",
        scratch_root: PathLike = None,
        probe_memory_fn: ProbeFn = None,
    ) -> None:
        self._scratch_root = Path(scratch_root or DEFAULT_SCRATCH_ROOT)
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

    def inspect_resources(
        self, root: PathLike = None, s: Any = None
    ) -> HostHealthReport:
        """Return complete host health report."""
        return inspect_resources(root_path=root, settings=s)

    def get_worker_allocation(self, mode: str = "reserve-two", custom: int = 1) -> int:
        """Calculate worker count via workers = max(1, cpu_cores - 2) default policy."""
        return calculate_worker_allocation(probe_cpu().logical_cores, mode, custom)

    def check_memory_headroom(
        self, *, policy: str | None = None
    ) -> MemoryWatchdogStatus:
        """Evaluate available system RAM headroom via the memory watchdog."""
        return self._watchdog.check(policy=policy)

    def check_available_memory(
        self,
        one_time_limit_pct: float = DEFAULT_ONE_TIME_MEMORY_LIMIT_PCT,
        consecutive_threshold: int = DEFAULT_MEMORY_OVER_LIMIT_COUNT,
    ) -> None:
        """Evaluate memory usage against donor memory guard thresholds."""
        self._watchdog.check_available_memory(one_time_limit_pct, consecutive_threshold)

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


resource_manager = ResourceMonitor()


def main() -> None:
    """Demonstrate probes, worker limits, watchdog, sandbox, and benchmark."""
    inspect_workspace_directories(), probe_cpu(), probe_memory()
    probe_disk(), probe_process(), get_worker_capacity()
    resource_manager.check_memory_headroom()
    with resource_manager.scratch_sandbox("demo-job-001") as sbox:
        (sbox / "task.txt").write_text("sandbox active", encoding="utf-8")
    run_memory_cleanup(), run_cpu_benchmark(iterations=2_000), inspect_resources()


if __name__ == "__main__":
    main()
