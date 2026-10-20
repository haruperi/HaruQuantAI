# ruff: noqa: INP001
"""System diagnostics, hardware inspection, memory watchdog, and resource governance.

Description:
    Provides the unified host resource custody and system diagnostics authority
    for the HaruQuantAI workstation. Consolidates read-only SQLite database probes,
    workspace directory readiness checks, filesystem writability probes, psutil
    hardware telemetry, worker concurrency allocation (workers = max(1, cpu_cores - 2)),
    CPU core affinity, GPU qualification, deterministic CPU benchmarks, active 15%
    RAM Memory Watchdog, DataFrame guards, and isolated per-job scratch sandboxes.

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
    - FR-HOST-RESOURCES-PROBE-HEALTH: Health snapshot (get_system_health -> INFO).
    - FR-HOST-RESOURCES-WORKER-ALLOCATION: Pool (calculate_worker_allocation -> INFO).
    - FR-HOST-RESOURCES-CORE-AFFINITY: CPU core affinity (apply_cpu_affinity -> INFO).
    - FR-HOST-RESOURCES-GPU-ACCELERATION: GPU (inspect_gpu_qualification -> DEBUG).
    - FR-HOST-RESOURCES-BENCHMARK: Execute CPU benchmark (run_cpu_benchmark -> INFO).
    - FR-HOST-RESOURCES-MEMORY-WATCHDOG: 15% RAM floor (check_memory_headroom -> DEBUG).
    - FR-HOST-RESOURCES-SCRATCH-SANDBOX: Job scratch dir (allocate_job_scratch -> INFO).

Python API Usage:
    ```python
    from app.host.resources import calculate_worker_allocation, probe_hardware

    hw = probe_hardware()
    workers = calculate_worker_allocation(hw.cpu_count_logical)
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
from app.host.persistence import HostPersistence
from app.host.settings import settings as host_settings

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

type PathLike = Path | str | None


def _log(level: str, fr_id: str, msg: str, **extra: Any) -> None:
    """Emit structured FR log record with fr_id context."""
    getattr(logger, level)("%s: %s", fr_id, msg, extra={"fr_id": fr_id, **extra})


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


type StatusCb = Callable[[MemoryWatchdogStatus], None] | None
type ProbeFn = Callable[[], MemoryObservation] | None


def _extract_workspace_paths(settings: Any = None) -> dict[str, str]:
    """Resolve directory paths mapping from host settings or defaults."""
    eff = settings if settings is not None else host_settings
    ws_node = getattr(eff, "workspace_paths", None) if eff is not None else None
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


def inspect_workspace_directories(settings: Any = None) -> dict[str, bool]:
    """Inspect existence of directories configured in settings.workspace_paths."""
    results: dict[str, bool] = {}
    for name, dir_path in sorted(_extract_workspace_paths(settings).items()):
        p = Path(dir_path).resolve()
        ok = p.exists() and p.is_dir()
        results[name] = ok
        sp = normalize_path(str(p))
        lvl = "info" if ok else "warning"
        verb, st = ("available", "AVAILABLE") if ok else ("absent", "ABSENT")
        msg = f"workspace directory '{name}' is {verb} at {sp}"
        _log(lvl, WORKSPACE_DIRS_FR, msg, directory=name, path=sp, status=st)
    return results


def probe_database(settings: Any = None) -> DatabaseProbe:
    """Perform read-only diagnostic inspection on active database."""
    _ = settings
    target = Path(HostPersistence.DEFAULT_DB_PATH)
    p_str = normalize_path(str(target))
    if not target.exists():
        _log("warning", PROBE_DATABASE_FR, f"database not found at {p_str}", path=p_str)
        return DatabaseProbe(
            p_str, False, 0, False, 0, 0, "Database file does not exist"
        )

    wal = target.with_name(f"{target.name}-wal")
    sz, wal_ok = target.stat().st_size, wal.exists()
    wal_sz = wal.stat().st_size if wal_ok else 0
    t_cnt, err_msg = 0, None
    try:
        HostPersistence.read_records("host_settings", limit=1)
        t_cnt = len(HostPersistence.PERSISTENCE_TABLES)
    except Exception as err:  # noqa: BLE001
        err_msg = str(err)
        _log("exception", PROBE_DATABASE_FR, f"database read failed on {p_str}")

    msg = f"probed database at {p_str} (tables={t_cnt}, size={sz})"
    _log("debug", PROBE_DATABASE_FR, msg, table_count=t_cnt)
    return DatabaseProbe(p_str, True, sz, wal_ok, wal_sz, t_cnt, err_msg)


def probe_cpu() -> CpuObservation:
    """Probe host CPU topology, frequency, and current load."""
    try:
        logical = psutil.cpu_count(logical=True) or 1
        physical = psutil.cpu_count(logical=False)
        freq = psutil.cpu_freq()
        f_val = round(float(freq.current), 2) if freq else None
        u_val = round(max(0.0, min(100.0, float(psutil.cpu_percent(interval=None)))), 2)
        msg = f"CPU probe succeeded (cores={logical}, util={u_val:.1f}%)"
        _log("debug", PROBE_CPU_FR, msg, cores=logical, util=u_val)
        return CpuObservation(logical, physical, f_val, u_val, True)
    except (psutil.Error, OSError, ValueError, TypeError) as exc:
        _log("warning", PROBE_CPU_FR, f"CPU telemetry probe failed: {exc}")
        return CpuObservation(os.cpu_count() or 1, None, None, None, False)


def probe_memory() -> MemoryObservation:
    """Probe physical host memory capacity and current availability."""
    try:
        m = psutil.virtual_memory()
        u_pct = round(max(0.0, min(100.0, float(m.percent))), 2)
        t_mb = round(m.total / (1024 * 1024), 2)
        a_mb = round(m.available / (1024 * 1024), 2)
        msg = f"memory probe succeeded (total={t_mb:.0f}MB, avail={a_mb:.0f}MB)"
        _log("debug", PROBE_MEMORY_FR, msg, total_mb=t_mb)
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
        msg = f"disk probe succeeded (mount={mnt}, free_pct={f_pct:.1f}%)"
        _log("debug", PROBE_DISK_FR, msg, free_pct=f_pct)
        return DiskObservation(mnt, d.total, d.free, d.used, f_pct, True)
    except (psutil.Error, OSError, ValueError, TypeError) as exc:
        _log("warning", PROBE_DISK_FR, f"disk telemetry probe failed: {exc}")
        return DiskObservation(mnt, 0, 0, 0, 0.0, False)


def probe_process() -> ProcessObservation:
    """Probe current host Python process health, memory, and threads."""
    try:
        p = psutil.Process()
        pid = p.pid
        cpu_v = round(max(0.0, float(p.cpu_percent(interval=None))), 2)
        rss_b = p.memory_info().rss
        rss_mb = round(rss_b / (1024 * 1024), 2)
        open_f: int | None = None
        try:
            open_f = len(p.open_files())
        except psutil.AccessDenied, OSError:
            open_f = None
        up = max(0.0, round(time.time() - p.create_time(), 2))
        _log("debug", PROBE_PROCESS_FR, f"process probe succeeded (pid={pid})")
        a1 = (pid, cpu_v, rss_b, rss_mb)
        a2 = (p.num_threads(), open_f, up, True)
        return ProcessObservation(*a1, *a2)
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
    if root_path is not None:
        root = Path(root_path).resolve()
        data_dir = root / "data"
    elif settings is not None and settings.get("workspace_paths", "data_dir"):
        data_dir = Path(settings.get("workspace_paths", "data_dir")).resolve()
        is_data = data_dir.name == "data"
        root = data_dir.parent.resolve() if is_data else Path.cwd().resolve()
    else:
        root = Path.cwd().resolve()
        data_dir = root / "data"

    l_ok = _check_dir_writable(data_dir / "logs")
    db_ok = _check_dir_writable(data_dir / "database")
    u = shutil.disk_usage(root)
    f_pct = (u.free / u.total * 100.0) if u.total > 0 else 0.0
    n_root = normalize_path(str(root))
    info = f"logs_ok={l_ok}, db_ok={db_ok}, free_pct={f_pct:.1f}"
    _log("debug", PROBE_STORAGE_FR, f"probed storage at {n_root} ({info})")
    return StorageProbe(n_root, l_ok, db_ok, u.free, u.total, round(f_pct, 2))


def probe_hardware() -> HardwareProbe:
    """Gather machine hardware metrics via psutil."""
    c, m = probe_cpu(), probe_memory()
    u_pct = c.utilization_pct or 0.0
    msg = f"probed hardware (cpus={c.logical_cores}, ram_pct={m.used_pct:.1f})"
    _log("debug", PROBE_HARDWARE_FR, msg, cpu_percent=u_pct)
    a1 = (c.logical_cores, c.physical_cores, u_pct)
    a2 = (m.total_bytes, m.available_bytes, m.used_pct)
    return HardwareProbe(*a1, *a2)


def get_system_health(
    root_path: PathLike = None, settings: Any = None
) -> HostHealthReport:
    """Coordinate host probes and generate complete health snapshot."""
    db = probe_database(settings=settings)
    st = probe_storage(root_path, settings=settings)
    hw = probe_hardware()
    ok = (
        db.exists
        and db.error is None
        and st.logs_dir_writable
        and st.database_dir_writable
        and st.free_pct > MIN_FREE_DISK_PCT
    )
    status = "HEALTHY" if ok else "DEGRADED"
    if ok:
        det = f"tables={db.table_count}, free_gb={st.free_bytes / (1024**3):.1f}"
        _log("info", PROBE_HEALTH_FR, f"host health status is {status} ({det})")
    else:
        det = f"db_err={db.error}, logs_ok={st.logs_dir_writable}"
        _log("warning", PROBE_HEALTH_FR, f"host health status is {status} ({det})")
    return HostHealthReport(status, db, st, hw, datetime.now(UTC).isoformat())


def calculate_worker_allocation(
    total_cores: int, mode: str = "reserve-two", custom_cores: int = 1
) -> int:
    """Derive worker pool allocation from total logical cores and selected mode."""
    sc = max(1, total_cores)
    nm = mode.strip().lower().replace("_", "-")
    if nm in ("single", "1"):
        alloc = 1
    elif nm in ("maximum", "all"):
        alloc = sc
    elif nm in ("reserve-one", "all-except-one"):
        alloc = max(1, sc - 1)
    elif nm == "custom":
        alloc = min(max(1, custom_cores), sc)
    else:
        alloc = max(1, sc - 2)

    det = f"cores={sc}, mode='{mode}', custom={custom_cores} -> {alloc}"
    _log("info", WORKER_ALLOCATION_FR, f"derived worker allocation ({det})")
    return alloc


def get_worker_capacity(
    settings: Any = None, mode: str | None = None, custom_cores: int | None = None
) -> WorkerCapacity:
    """Derive consolidated worker capacity, CPU core affinity, and GPU status."""
    eff = settings if settings is not None else host_settings
    eff_mode, eff_custom = mode, custom_cores
    cfg_cpu = getattr(eff, "config_cpu", None) if eff is not None else None
    if cfg_cpu is not None:
        if eff_mode is None and hasattr(cfg_cpu, "core_usage"):
            eff_mode = str(cfg_cpu.core_usage)
        if eff_custom is None and hasattr(cfg_cpu, "custom_cores"):
            eff_custom = int(cfg_cpu.custom_cores)

    eff_mode = eff_mode or "reserve-two"
    eff_custom = 1 if eff_custom is None else eff_custom
    tc = probe_cpu().logical_cores
    alloc = calculate_worker_allocation(tc, eff_mode, eff_custom)
    aff_sup, aff_cur = inspect_cpu_affinity()
    gpu_ok = inspect_gpu_qualification()
    det = f"workers={alloc}/{tc}, mode='{eff_mode}', gpu={gpu_ok}"
    _log("info", WORKER_CAPACITY_FR, f"worker capacity resolved ({det})")
    c_val = eff_custom if eff_mode.lower().replace("_", "-") == "custom" else None
    aff_act = aff_sup and aff_cur is not None
    return WorkerCapacity(tc, alloc, eff_mode, c_val, aff_sup, aff_act, gpu_ok)


def inspect_cpu_affinity() -> tuple[bool, list[int] | None]:
    """Inspect if CPU core affinity is supported on current OS."""
    try:
        p = psutil.Process()
        if hasattr(p, "cpu_affinity"):
            cur = list(p.cpu_affinity())
            msg = f"CPU affinity supported on process (current={cur!r})"
            _log("debug", CORE_AFFINITY_FR, msg, affinity=cur)
            return True, cur
        _log(
            "debug",
            CORE_AFFINITY_FR,
            f"CPU affinity unsupported on {platform.system()}",
        )
        return False, None
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
        _log(
            "warning",
            CORE_AFFINITY_FR,
            f"CPU affinity unsupported on {platform.system()}",
        )
        return False
    except (psutil.Error, OSError, ValueError) as exc:
        _log("warning", CORE_AFFINITY_FR, f"failed applying CPU affinity: {exc}")
        return False


def inspect_gpu_qualification() -> bool:
    """Safely inspect if qualified GPU acceleration is available."""
    cv = os.environ.get("CUDA_VISIBLE_DEVICES", "").strip()
    ok = bool(
        (cv and cv not in ("-1", "none", "NONE"))
        or os.environ.get("CUDA_PATH")
        or os.environ.get("NVIDIA_VISIBLE_DEVICES")
    )
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
    if obs.is_available and obs.total_bytes > 0:
        raw_a = (obs.available_bytes / obs.total_bytes) * 100.0
        a_pct = round(max(0.0, min(100.0, raw_a)), 2)
    elif obs.is_available:
        a_pct = round(max(0.0, min(100.0, 100.0 - obs.used_pct)), 2)
    else:
        a_pct = 100.0

    pressured = obs.is_available and a_pct < thresh
    p_act = "PAUSE" if policy.strip().lower() == "pause" else "REJECT"
    act = p_act if pressured else "ALLOW"
    kw = {"available_pct": a_pct, "threshold_pct": thresh, "action": act}
    if pressured:
        det = f"available={a_pct:.1f}% < {thresh:.1f}%"
        _log("warning", MEMORY_WATCHDOG_FR, f"RAM headroom low ({det}) -> {act}", **kw)
    else:
        det = f"available={a_pct:.1f}% >= {thresh:.1f}%"
        _log("debug", MEMORY_WATCHDOG_FR, f"RAM headroom healthy ({det})", **kw)
    a1 = (a_pct, obs.used_pct, obs.available_bytes, obs.total_bytes)
    a2 = (thresh, pressured, act, datetime.now(UTC).isoformat())
    return MemoryWatchdogStatus(*a1, *a2)


def evaluate_dataframe_guard(
    row_count: int, *, max_rows: int = 5_000_000, mode: str = "warn"
) -> str:
    """Evaluate data-frame size against configured warn/stop/off guard policy."""
    nm = mode.strip().lower()
    if nm == "off" or row_count <= max_rows:
        msg = f"dataframe guard passed (rows={row_count}, max={max_rows}, mode={nm})"
        _log("debug", MEMORY_WATCHDOG_FR, msg, rows=row_count)
        return "ALLOW"
    if nm == "stop":
        msg = f"dataframe guard stopped execution (rows={row_count} > max={max_rows})"
        _log("error", MEMORY_WATCHDOG_FR, msg, rows=row_count)
        raise MemoryError(
            f"DataFrame row count ({row_count}) exceeds stop limit ({max_rows})."
        )
    msg = f"dataframe guard warning (rows={row_count} > max={max_rows})"
    _log("warning", MEMORY_WATCHDOG_FR, msg, rows=row_count)
    return "WARN"


def run_memory_cleanup() -> int:
    """Execute explicit garbage collection and log reclaimed object count."""
    reclaimed = gc.collect()
    msg = f"executed memory cleanup (reclaimed_objects={reclaimed})"
    _log("info", MEMORY_WATCHDOG_FR, msg, reclaimed_objects=reclaimed)
    return reclaimed


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

    @property
    def min_available_pct(self) -> float:
        """Return configured minimum available RAM percentage threshold."""
        return self._min_available_pct

    @property
    def policy(self) -> str:
        """Return configured enforcement policy ('reject' or 'pause')."""
        return self._policy

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
            p_cbs = list(self._pressure_callbacks)
            r_cbs = list(self._recovery_callbacks)

        if status.is_pressured:
            for cb in p_cbs:
                cb(status)
        elif prev is not None and prev.is_pressured and not status.is_pressured:
            for cb in r_cbs:
                cb(status)
        return status

    def start(self) -> None:
        """Start background daemon thread monitoring system RAM headroom."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._monitor_loop, name="HostMemoryWatchdog", daemon=True
            )
            self._thread.start()
        det = f"threshold={self._min_available_pct:.1f}%, policy={self._policy}"
        _log("info", MEMORY_WATCHDOG_FR, f"started memory watchdog ({det})")

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
        msg = f"scratch path escaped root containment for job {safe_id}"
        _log("error", SCRATCH_SANDBOX_FR, msg, job_id=safe_id)
        raise ValueError(f"Scratch path escaped containment for job '{safe_id}'")
    target.mkdir(parents=True, exist_ok=True)
    t_str = normalize_path(str(target))
    _log("info", SCRATCH_SANDBOX_FR, f"allocated scratch for {safe_id} at {t_str}")
    return target


def cleanup_job_scratch(job_id: str, base_dir: PathLike = None) -> bool:
    """Remove the isolated temporary scratch directory for a completed/cancelled job."""
    safe_id, root, target = _resolve_scratch_target(job_id, base_dir)
    if root not in target.parents or not target.exists():
        return False
    shutil.rmtree(target, ignore_errors=True)
    _log("info", SCRATCH_SANDBOX_FR, f"cleaned up scratch sandbox for job {safe_id}")
    return True


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
    elapsed = max(1e-6, time.perf_counter() - start_perf)
    tput = round(n / elapsed, 2)
    t_ms = round((elapsed * 1000.0) / n, 5)
    avg_st = round(elapsed / 100.0, 4)
    avg_sh = round(3600.0 / avg_st) if avg_st > 0 else 0
    msg = f"benchmark finished: duration={elapsed:.4f}s, throughput={tput:.0f} ops/s"
    _log("info", BENCHMARK_FR, msg, duration=elapsed, throughput=tput)
    return BenchmarkResults(round(elapsed, 4), n, avg_sh, t_ms, tput)


class BenchmarkRunner:
    """Manages synchronous and background benchmark execution lifecycle."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, BenchmarkJob] = {}
        self._cancel_events: dict[str, threading.Event] = {}

    def start_job(self, iterations: int = 100_000) -> BenchmarkJob:
        """Start a new benchmark job in a background worker thread."""
        job_id = f"bench-{uuid.uuid4().hex[:8]}"
        cancel_evt = threading.Event()
        now = datetime.now(UTC).isoformat()
        meta = {"requested_iterations": iterations}
        job = BenchmarkJob(
            job_id, "running", 0.0, now, None, None, 0, None, None, None, meta
        )
        with self._lock:
            self._jobs[job_id] = job
            self._cancel_events[job_id] = cancel_evt
        threading.Thread(
            target=self._execute_worker,
            args=(job_id, iterations, cancel_evt),
            name=f"BenchmarkWorker-{job_id}",
            daemon=True,
        ).start()
        return job

    def _finish_job(
        self,
        job_id: str,
        state: str,
        duration: float,
        *,
        progress_pct: float = 0.0,
        completed: int = 0,
        results: BenchmarkResults | None = None,
        error_msg: str | None = None,
    ) -> None:
        """Update BenchmarkJob state under lock."""
        with self._lock:
            curr = self._jobs.get(job_id)
            st_at = curr.started_at if curr else None
            meta = curr.metadata if curr else {}
            tput = results.throughput_ops_per_sec if results else None
            now = datetime.now(UTC).isoformat()
            a1 = (job_id, state, progress_pct, st_at, now, duration)
            a2 = (completed, tput, results, error_msg, meta)
            self._jobs[job_id] = BenchmarkJob(*a1, *a2)

    def _execute_worker(
        self, job_id: str, iterations: int, cancel_evt: threading.Event
    ) -> None:
        """Worker thread executing the benchmark computation."""
        start_perf = time.perf_counter()
        try:
            res = run_cpu_benchmark(iterations=iterations, cancel_event=cancel_evt)
            self._finish_job(
                job_id,
                "completed",
                res.duration_seconds,
                progress_pct=100.0,
                completed=iterations,
                results=res,
            )
        except InterruptedError:
            el = round(time.perf_counter() - start_perf, 4)
            err = "Benchmark cancelled by user request"
            self._finish_job(job_id, "cancelled", el, error_msg=err)
        except Exception as exc:  # noqa: BLE001
            el = round(time.perf_counter() - start_perf, 4)
            self._finish_job(job_id, "failed", el, error_msg=str(exc))

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
                _log("info", BENCHMARK_FR, f"signaled cancellation for {job_id}")
                return True
            return False


class ResourceManager:
    """Unified custodian for diagnostics, worker sizing, watchdog, and sandboxes."""

    def __init__(
        self,
        *,
        min_available_ram_pct: float = MIN_AVAILABLE_RAM_PCT,
        watchdog_policy: str = "reject",
        scratch_root: PathLike = None,
        probe_memory_fn: ProbeFn = None,
    ) -> None:
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
        self, root_path: PathLike = None, settings: Any = None
    ) -> HostHealthReport:
        """Return complete host health report."""
        return get_system_health(root_path=root_path, settings=settings)

    def get_worker_allocation(
        self, mode: str = "reserve-two", custom_cores: int = 1
    ) -> int:
        """Calculate worker count via workers = max(1, cpu_cores - 2) default policy."""
        return calculate_worker_allocation(
            probe_cpu().logical_cores, mode=mode, custom_cores=custom_cores
        )

    def check_memory_headroom(
        self, *, policy: str | None = None
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


def main() -> None:
    """Demonstrate probes, worker limits, watchdog, sandbox, and benchmark."""
    inspect_workspace_directories()
    probe_cpu()
    probe_memory()
    probe_disk()
    probe_process()
    get_worker_capacity()
    resource_manager.check_memory_headroom()
    with resource_manager.scratch_sandbox("demo-job-001") as sandbox_dir:
        (sandbox_dir / "task.txt").write_text("sandbox active", encoding="utf-8")
    run_memory_cleanup()
    run_cpu_benchmark(iterations=2_000)
    get_system_health()


if __name__ == "__main__":
    main()
