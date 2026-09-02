"""Tests for ProcessLimits OS containment adapter."""

from __future__ import annotations

import ctypes
import os
import signal
import subprocess
import sys
import types
from unittest.mock import MagicMock, patch

import pytest
from app.services.plugins.permissions_sandbox.process_limits import (
    ProcessLimits,
    UnsupportedSandboxEnforcementError,
    _assign_posix_limits,
    _assign_windows_job,
    _configure_windows_job,
)


def test_current_platform_launch_attach_and_cleanup() -> None:
    limits = ProcessLimits(cpu_limit_cores=1.0, memory_limit_mb=128)
    process = limits.start(
        [
            str(getattr(sys, "_base_executable", sys.executable)),
            "-I",
            "-c",
            "import time; time.sleep(0.05)",
        ],
        {
            "PATH": os.environ.get("PATH", ""),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
        },
    )
    try:
        limits.attach(process)
        _, stderr = process.communicate(timeout=2)
        assert process.returncode == 0, stderr.decode(errors="replace")
    finally:
        if process.poll() is None:
            limits.terminate(process)
        limits.close()


def test_terminate_kills_real_worker_group() -> None:
    limits = ProcessLimits(cpu_limit_cores=1.0, memory_limit_mb=128)
    process = limits.start(
        [
            str(getattr(sys, "_base_executable", sys.executable)),
            "-I",
            "-c",
            "import time; time.sleep(30)",
        ],
        {
            "PATH": os.environ.get("PATH", ""),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
        },
    )
    try:
        limits.attach(process)
        limits.terminate(process)
        process.wait(timeout=2)
        assert process.poll() is not None
    finally:
        limits.close()


def test_launch_options():
    limits = ProcessLimits(cpu_limit_cores=1.0, memory_limit_mb=128)
    with patch("os.name", "nt"):
        assert limits.launch_options() == {
            "creationflags": subprocess.CREATE_NEW_PROCESS_GROUP
        }
    with patch("os.name", "posix"):
        assert limits.launch_options() == {"start_new_session": True}
    with patch("os.name", "unknown"), pytest.raises(UnsupportedSandboxEnforcementError):
        limits.launch_options()


def test_start_platform_branches():
    limits = ProcessLimits(cpu_limit_cores=1.0, memory_limit_mb=128)

    with patch("os.name", "posix"), patch("subprocess.Popen") as mock_popen:
        limits.start(["cmd"], {"ENV": "1"})
        mock_popen.assert_called_once()
        assert mock_popen.call_args.kwargs.get("start_new_session") is True

    with patch("os.name", "unknown"), pytest.raises(UnsupportedSandboxEnforcementError):
        limits.start(["cmd"], {})


def test_attach_platform_branches():
    limits = ProcessLimits(cpu_limit_cores=1.0, memory_limit_mb=128)
    mock_process = MagicMock()

    with (
        patch("os.name", "posix"),
        patch(
            "app.services.plugins.permissions_sandbox.process_limits._assign_posix_limits"
        ) as mock_posix,
    ):
        limits.attach(mock_process)
        mock_posix.assert_called_once()

    with patch("os.name", "unknown"), pytest.raises(UnsupportedSandboxEnforcementError):
        limits.attach(mock_process)


def test_terminate_posix():
    limits = ProcessLimits(cpu_limit_cores=1.0, memory_limit_mb=128)
    mock_process = MagicMock()
    mock_process.poll.return_value = None
    mock_process.pid = 12345

    with (
        patch("os.name", "posix"),
        patch("os.killpg", create=True) as mock_killpg,
        patch.object(signal, "SIGKILL", 9, create=True),
    ):
        limits.terminate(mock_process)
        mock_killpg.assert_called_once_with(12345, 9)


def test_terminate_process_lookup_error():
    limits = ProcessLimits(cpu_limit_cores=1.0, memory_limit_mb=128)
    mock_process = MagicMock()
    mock_process.poll.return_value = None
    mock_process.kill.side_effect = ProcessLookupError

    with patch("os.name", "other"):
        limits.terminate(mock_process)  # should not raise


def test_close_without_handle():
    limits = ProcessLimits(cpu_limit_cores=1.0, memory_limit_mb=128)
    limits.close()
    assert limits._job_handle is None


def test_assign_posix_limits():
    mock_resource = types.ModuleType("resource")
    mock_resource.RLIMIT_CPU = 0  # type: ignore[attr-defined]
    mock_resource.RLIMIT_AS = 1  # type: ignore[attr-defined]
    mock_resource.prlimit = MagicMock()  # type: ignore[attr-defined]

    with patch.dict(sys.modules, {"resource": mock_resource}):
        _assign_posix_limits(1234, 1.5, 256)
        assert mock_resource.prlimit.call_count == 2

    # Prlimit missing
    mock_resource_no_prlimit = types.ModuleType("resource")
    with (
        patch.dict(sys.modules, {"resource": mock_resource_no_prlimit}),
        pytest.raises(
            UnsupportedSandboxEnforcementError, match="prlimit is unavailable"
        ),
    ):
        _assign_posix_limits(1234, 1.5, 256)


def test_assign_windows_job_non_win32():
    with (
        patch("sys.platform", "linux"),
        pytest.raises(
            UnsupportedSandboxEnforcementError, match="Windows Job Object unavailable"
        ),
    ):
        _assign_windows_job(MagicMock(), 1.0, 128)


class _DummyStructure(ctypes.Structure):
    _fields_ = [("val", ctypes.c_int)]


def test_configure_windows_job_errors():
    dummy_ext = _DummyStructure(val=1)
    dummy_cpu = _DummyStructure(val=2)

    mock_kernel32 = MagicMock()
    mock_kernel32.SetInformationJobObject.side_effect = [False]

    with pytest.raises(
        UnsupportedSandboxEnforcementError, match="memory/process limit failed"
    ):
        _configure_windows_job(mock_kernel32, 1, dummy_ext, dummy_cpu, MagicMock())

    mock_kernel32.SetInformationJobObject.side_effect = [True, False]
    with pytest.raises(UnsupportedSandboxEnforcementError, match="CPU limit failed"):
        _configure_windows_job(mock_kernel32, 1, dummy_ext, dummy_cpu, MagicMock())

    mock_kernel32.SetInformationJobObject.side_effect = [True, True]
    mock_kernel32.AssignProcessToJobObject.return_value = False
    mock_proc = MagicMock()
    mock_proc._handle = 123
    with pytest.raises(
        UnsupportedSandboxEnforcementError, match="AssignProcessToJobObject failed"
    ):
        _configure_windows_job(mock_kernel32, 1, dummy_ext, dummy_cpu, mock_proc)
