"""Fresh-process execution harness for removability verification."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

__all__: tuple[str, ...] = ("FreshProcessResult", "run_in_fresh_process")


@dataclass(frozen=True, slots=True)
class FreshProcessResult:
    """Captured output and status from an isolated Python subprocess."""

    returncode: int
    stdout: str
    stderr: str


def run_in_fresh_process(
    *,
    repository_root: Path,
    script: str,
    timeout_seconds: float = 30.0,
) -> FreshProcessResult:
    """Execute a Python snippet in an isolated interpreter process.

    Args:
        repository_root: Repository root used as the process working directory.
        script: Python code passed through the interpreter ``-c`` argument.
        timeout_seconds: Maximum permitted subprocess duration.

    Returns:
        Captured process status and streams.

    Raises:
        AssertionError: If execution exceeds ``timeout_seconds``.
    """
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    resolved_root = str(repository_root.resolve())
    bootstrap = f"import sys; sys.path.insert(0, {resolved_root!r}); "
    command = [sys.executable, "-I", "-c", bootstrap + script]

    try:
        completed = subprocess.run(  # noqa: S603
            command,
            cwd=repository_root,
            env=environment,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=False,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        message = f"fresh process exceeded {timeout_seconds:.3f}s"
        raise AssertionError(message) from exc

    return FreshProcessResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
