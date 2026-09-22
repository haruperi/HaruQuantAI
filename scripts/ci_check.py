"""Run the same bounded checks locally and in CI; stop on the first failure."""

import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Return the first failing validation command's exit code."""
    root = Path(__file__).resolve().parents[1]
    commands = [
        ["ruff", "check", "."],
        ["ruff", "format", "--check", "."],
        ["mypy"],
        ["scripts.architecture_check"],
        ["scripts.generate_ui_contracts", "--check"],
        [
            "pytest",
            "tests",
            "--cov",
            "--cov-report=term-missing",
        ],
        ["tests.examples.composition"],
        ["tests.examples.telemetry_usage"],
        ["tests.examples.catalog_usage"],
        ["tests.examples.slice_usage"],
        ["tests.examples.gateway_usage"],
    ]
    for command in commands:
        result = subprocess.run([sys.executable, "-m", *command], cwd=root, check=False)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
