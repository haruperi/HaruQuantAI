"""Current-platform process containment adapter for plugin workers."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from dataclasses import dataclass
from typing import cast


class UnsupportedSandboxEnforcementError(RuntimeError):
    """Raised when the host cannot provide the declared hard limits."""


@dataclass(slots=True)
class ProcessLimits:
    """OS enforcement resources for one isolated worker."""

    cpu_limit_cores: float
    memory_limit_mb: int
    _job_handle: int | None = None

    def start(
        self, command: list[str], environment: dict[str, str]
    ) -> subprocess.Popen[bytes]:
        """Launch one worker with platform-specific group creation.

        Returns:
            Binary-pipe child process.

        Raises:
            UnsupportedSandboxEnforcementError: The host has no hard adapter.
        """
        if os.name == "nt":
            return subprocess.Popen(  # noqa: S603
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                env=environment,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )
        if os.name == "posix":
            return subprocess.Popen(  # noqa: S603
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                env=environment,
                start_new_session=True,
            )
        raise UnsupportedSandboxEnforcementError(
            "current platform has no sandbox adapter"
        )

    def launch_options(self) -> dict[str, object]:
        """Return subprocess options with platform containment setup.

        Returns:
            Keyword options for ``subprocess.Popen``.

        Raises:
            UnsupportedSandboxEnforcementError: The host has no hard adapter.
        """
        if os.name == "nt":
            return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
        if os.name == "posix":
            return {"start_new_session": True}
        raise UnsupportedSandboxEnforcementError(
            "current platform has no sandbox adapter"
        )

    def attach(self, process: subprocess.Popen[bytes]) -> None:
        """Attach a launched worker to its hard platform limits.

        Args:
            process: Direct child process launched without a shell.

        Raises:
            UnsupportedSandboxEnforcementError: The OS limit assignment fails.
        """
        if os.name == "nt":
            self._job_handle = _assign_windows_job(
                process, self.cpu_limit_cores, self.memory_limit_mb
            )
        elif os.name == "posix":
            _assign_posix_limits(
                process.pid,
                self.cpu_limit_cores,
                self.memory_limit_mb,
            )
        else:
            raise UnsupportedSandboxEnforcementError(
                "current platform has no sandbox adapter"
            )

    def terminate(self, process: subprocess.Popen[bytes]) -> None:
        """Terminate the entire child group/job and close all OS resources."""
        try:
            if os.name == "nt" and self._job_handle is not None:
                _close_windows_handle(self._job_handle)
                self._job_handle = None
            elif os.name == "posix" and process.poll() is None:
                os.killpg(  # type: ignore[attr-defined]
                    process.pid,
                    signal.SIGKILL,  # type: ignore[attr-defined]
                )
            elif process.poll() is None:
                process.kill()
        except ProcessLookupError:
            pass

    def close(self) -> None:
        """Close an unconsumed Windows Job Object handle."""
        if self._job_handle is not None:
            _close_windows_handle(self._job_handle)
            self._job_handle = None


def _assign_posix_limits(pid: int, cores: float, memory_mb: int) -> None:
    """Apply mandatory CPU/address-space limits to one POSIX process.

    Raises:
        UnsupportedSandboxEnforcementError: ``prlimit`` is unavailable.
    """
    import resource

    prlimit = getattr(resource, "prlimit", None)
    if prlimit is None:
        raise UnsupportedSandboxEnforcementError("POSIX prlimit is unavailable")
    cpu_seconds = max(1, int(cores * 60))
    memory_bytes = memory_mb * 1024 * 1024
    prlimit(pid, resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))  # type: ignore[attr-defined]
    prlimit(pid, resource.RLIMIT_AS, (memory_bytes, memory_bytes))  # type: ignore[attr-defined]


def _assign_windows_job(
    process: subprocess.Popen[bytes], cores: float, memory_mb: int
) -> int:
    """Assign a worker to a kill-on-close Windows Job Object.

    Returns:
        Owned Job Object handle.

    Raises:
        UnsupportedSandboxEnforcementError: Any mandatory limit fails.
    """
    if sys.platform != "win32":
        raise UnsupportedSandboxEnforcementError("Windows Job Object unavailable")
    import ctypes
    from ctypes import wintypes

    class IoCounters(ctypes.Structure):
        _fields_ = [  # type: ignore[mutable-override]
            (name, ctypes.c_ulonglong)
            for name in (
                "ReadOperationCount",
                "WriteOperationCount",
                "OtherOperationCount",
                "ReadTransferCount",
                "WriteTransferCount",
                "OtherTransferCount",
            )
        ]

    class Basic(ctypes.Structure):
        _fields_ = [  # type: ignore[mutable-override]
            ("PerProcessUserTimeLimit", ctypes.c_longlong),
            ("PerJobUserTimeLimit", ctypes.c_longlong),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class Extended(ctypes.Structure):
        _fields_ = [  # type: ignore[mutable-override]
            ("BasicLimitInformation", Basic),
            ("IoInfo", IoCounters),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    class CpuRate(ctypes.Structure):
        _fields_ = [  # type: ignore[mutable-override]
            ("ControlFlags", wintypes.DWORD),
            ("CpuRate", wintypes.DWORD),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR)
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.SetInformationJobObject.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    )
    kernel32.SetInformationJobObject.restype = wintypes.BOOL
    kernel32.AssignProcessToJobObject.argtypes = (
        wintypes.HANDLE,
        wintypes.HANDLE,
    )
    kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        raise UnsupportedSandboxEnforcementError("CreateJobObjectW failed")
    extended = Extended()
    extended.BasicLimitInformation.LimitFlags = 0x00002000 | 0x00000100 | 0x00000008
    extended.BasicLimitInformation.ActiveProcessLimit = 1
    extended.ProcessMemoryLimit = memory_mb * 1024 * 1024
    cpu = CpuRate(0x00000001 | 0x00000004, min(10000, max(1, int(cores * 10000))))
    try:
        _configure_windows_job(kernel32, job, extended, cpu, process)
    except BaseException:
        _close_windows_handle(int(job))
        raise
    return int(job)


def _configure_windows_job(
    kernel32: object,
    job: int,
    extended: object,
    cpu: object,
    process: subprocess.Popen[bytes],
) -> None:
    """Set mandatory Windows Job Object limits and attach the child.

    Raises:
        UnsupportedSandboxEnforcementError: A limit or assignment fails.
    """
    import ctypes

    set_info = kernel32.SetInformationJobObject  # type: ignore[attr-defined]
    assign = kernel32.AssignProcessToJobObject  # type: ignore[attr-defined]
    typed_extended = cast("ctypes.Structure", extended)
    typed_cpu = cast("ctypes.Structure", cpu)
    if not set_info(
        job, 9, ctypes.byref(typed_extended), ctypes.sizeof(typed_extended)
    ):
        raise UnsupportedSandboxEnforcementError(
            "Job Object memory/process limit failed"
        )
    if not set_info(job, 15, ctypes.byref(typed_cpu), ctypes.sizeof(typed_cpu)):
        raise UnsupportedSandboxEnforcementError("Job Object CPU limit failed")
    process_handle = getattr(process, "_handle", None)
    if not process_handle or not assign(job, process_handle):
        raise UnsupportedSandboxEnforcementError("AssignProcessToJobObject failed")


def _close_windows_handle(handle: int) -> None:
    """Close a Windows kernel handle, causing kill-on-close when applicable."""
    import ctypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CloseHandle.argtypes = (ctypes.c_void_p,)
    kernel32.CloseHandle.restype = ctypes.c_int
    kernel32.CloseHandle(handle)
