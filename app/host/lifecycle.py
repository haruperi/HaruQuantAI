"""Host lifecycle state: status probe and graceful shutdown.

The web-satellite analog of the SQX supervision endpoints (ledger
SQX144-EV-000002): where SQX's Electron satellite probes the engine's
``/status`` and dies with it, our browser satellite polls
``GET /api/v1/status`` for liveness, and an authenticated operator asks
``POST /api/v1/shutdown`` for a graceful exit instead of killing a process.
"""

from __future__ import annotations

import os
import platform
import sys
import time
from pathlib import Path

from starlette.requests import Request
from starlette.responses import JSONResponse

from app.host.envelope import success_payload
from app.host.http import envelope_response, request_id_of


def _windows_memory() -> tuple[int | None, int | None]:
    """Return (total_bytes, available_bytes) on Windows using ctypes."""
    try:
        import ctypes

        if not hasattr(ctypes, "windll"):
            return (None, None)

        class _MEMORYSTATUSEX(ctypes.Structure):
            pass

        _MEMORYSTATUSEX._fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

        stat = _MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(stat)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            return (int(stat.ullTotalPhys), int(stat.ullAvailPhys))
    except OSError, AttributeError, ValueError:
        return (None, None)
    return (None, None)


def _linux_memory() -> tuple[int | None, int | None]:
    """Return (total_bytes, available_bytes) on Linux via /proc/meminfo."""
    meminfo = Path("/proc/meminfo")
    if not meminfo.is_file():
        return (None, None)
    try:
        total: int | None = None
        avail: int | None = None
        for line in meminfo.read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                total = int(line.split()[1]) * 1024
            elif line.startswith("MemAvailable:"):
                avail = int(line.split()[1]) * 1024
        return (total, avail)
    except OSError, ValueError, IndexError:
        return (None, None)


def _system_memory() -> tuple[int | None, int | None]:
    """Return (total_bytes, available_bytes) using standard library."""
    current_system = platform.system().lower()
    if current_system == "windows":
        return _windows_memory()
    if current_system == "linux":
        return _linux_memory()
    return (None, None)


class LifecycleState:
    """Tracks host start time, shutdown flag, and platform resources.

    Deliberately tiny and dependency-free so tests (and any future
    supervisor) can drive it directly.
    """

    def __init__(self) -> None:
        """Start the uptime clock and clear the shutdown flag."""
        self._started_monotonic = time.monotonic()
        self.shutdown_requested = False
        self.ui_ready = False

    def mark_ui_ready(self) -> None:
        """Record that the frontend UI has completed its initial load."""
        self.ui_ready = True

    def uptime_seconds(self) -> float:
        """Return seconds since host start (monotonic, restart-safe)."""
        return time.monotonic() - self._started_monotonic

    def status_payload(self, version: str) -> dict[str, object]:
        """Return the status document for the probe endpoint.

        Args:
            version: Host version string to report.

        Returns:
            A JSON-ready dict with ``status``, ``version``, ``ui_ready``, rounded
            ``uptime_seconds``, process ``pid``, CPU count, platform, and
            memory sizing.
        """
        total_mem, avail_mem = _system_memory()
        return {
            "status": "running",
            "version": version,
            "ui_ready": self.ui_ready,
            "uptime_seconds": round(self.uptime_seconds(), 3),
            "pid": os.getpid(),
            "cpu_count": os.cpu_count() or 1,
            "platform": sys.platform,
            "system": platform.system(),
            "python_version": platform.python_version(),
            "memory_total_bytes": total_mem,
            "memory_available_bytes": avail_mem,
        }


async def status_endpoint(request: Request) -> JSONResponse:
    """Handle ``GET /api/v1/status`` (public: auth-exempt liveness probe)."""
    request_id = request_id_of(request)
    lifecycle: LifecycleState = request.app.state.services.lifecycle
    version: str = request.app.state.version
    return envelope_response(
        request_id, success_payload(request_id, lifecycle.status_payload(version))
    )


async def shutdown_endpoint(request: Request) -> JSONResponse:
    """Handle ``POST /api/v1/shutdown``: request a graceful stop.

    Sets the lifecycle flag and flips the uvicorn server's graceful-exit
    bit when the bootstrapper attached one, letting in-flight requests
    finish. The route is session-protected (see the auth middleware
    exemptions), so only an authenticated caller can stop the host.
    """
    request_id = request_id_of(request)
    lifecycle: LifecycleState = request.app.state.services.lifecycle
    lifecycle.shutdown_requested = True
    server = getattr(request.app.state, "uvicorn_server", None)
    if server is not None:
        server.should_exit = True
    logger = request.app.state.logger
    logger.info("Graceful shutdown requested (request %s)", request_id)
    return envelope_response(
        request_id, success_payload(request_id, {"shutdown": "requested"})
    )
