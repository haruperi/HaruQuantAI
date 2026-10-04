"""Run candidate qualification checks against the current repository baseline."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Run bounded checks in order, returning the first failing exit status."""
    root = Path(__file__).resolve().parents[1]
    commands = (
        (sys.executable, "-m", "ruff", "check", "app", "tests", "scripts"),
        (sys.executable, "-m", "ruff", "format", "--check", "app", "tests", "scripts"),
        (
            sys.executable,
            "-m",
            "mypy",
            "--explicit-package-bases",
            "app",
            "tests",
            "scripts",
        ),
        (
            sys.executable,
            "-m",
            "pytest",
            "tests",
            "--cov=app",
            "--cov-report=term-missing",
        ),
    )
    for command in commands:
        print("Running:", " ".join(command), flush=True)
        result = subprocess.run(command, cwd=root, check=False)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
