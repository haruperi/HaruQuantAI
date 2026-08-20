"""Fresh-process execution harness for removability and isolation verification."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

__all__: tuple[str, ...] = ("FreshProcessResult", "run_in_fresh_process")


@dataclass(frozen=True, slots=True)
class FreshProcessResult:
    """Captured output and status from an isolated Python subprocess.

    Attributes:
        returncode: Exit status code of the subprocess.
        stdout: Standard output text captured from the subprocess.
        stderr: Standard error text captured from the subprocess.
    """

    returncode: int
    stdout: str
    stderr: str


def run_in_fresh_process(
    *,
    repository_root: Path,
    script: str,
    timeout_seconds: float = 30.0,
) -> FreshProcessResult:
    """Execute a Python snippet in an isolated fresh Python interpreter process.

    Args:
        repository_root: Absolute path to repo root used as cwd and sys.path entry.
        script: Python code string passed via the `-c` argument.
        timeout_seconds: Maximum execution time before raising AssertionError.

    Returns:
        FreshProcessResult: Execution outcome including exit code and captured streams.

    Raises:
        AssertionError: If subprocess execution exceeds timeout_seconds.
    """
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    resolved_root = str(repository_root.resolve())
    bootstrap = f"import sys; sys.path.insert(0, {resolved_root!r}); "
    cmd = [sys.executable, "-I", "-c", bootstrap + script]

    try:
        completed = subprocess.run(  # noqa: S603
            cmd,
            cwd=repository_root,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=False,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        timeout_message = f"fresh process exceeded {timeout_seconds:.3f}s"
        raise AssertionError(timeout_message) from exc

    return FreshProcessResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
