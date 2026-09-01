import os
import sys

from app.services.plugins.permissions_sandbox.process_limits import ProcessLimits


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
    limits.attach(process)
    limits.terminate(process)
    process.wait(timeout=2)
    assert process.poll() is not None
