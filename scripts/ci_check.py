#!/usr/bin/env python
"""CI check script for HaruQuantAI.

Runs Ruff format check, Ruff lint check, Mypy type check, and Pytest with coverage.
"""

import subprocess
import sys
import time
from pathlib import Path


def run_command(command: list[str], name: str) -> bool:
    """Run a command and print status.

    Args:
        command: Command list.
        name: Name of the step.

    Returns:
        True if the command succeeded, False otherwise.
    """
    print("========================================")
    print(f"Running {name}...")
    print(f"Command: {' '.join(command)}")
    print("========================================\n")

    start_time = time.time()
    full_command = ["uv", "run", *command]
    result = subprocess.run(full_command, capture_output=False, check=False)
    elapsed = time.time() - start_time

    if result.returncode == 0:
        print(f"\n[SUCCESS] {name} passed in {elapsed:.2f}s\n")
        return True

    print(
        f"\n[FAILURE] {name} failed with exit code "
        f"{result.returncode} in {elapsed:.2f}s\n"
    )
    return False


def main() -> None:
    """Run all CI check steps."""
    steps: list[tuple[list[str], str]] = [
        (["ruff", "format", "--check", "."], "Ruff Format Check"),
        (["ruff", "check", "."], "Ruff Lint Check"),
        (["mypy"], "Mypy Type Check"),
        (
            [
                "pytest",
                "--cov=app",
                "--cov-report=term-missing",
                "--cov-report=html",
                "--cov-fail-under=80",
            ],
            "Pytest & Coverage",
        ),
    ]

    # Optional architecture checks when matrices are present
    matrix_path = Path("docs/dev/plugin-decoupling/audit/removability_matrix.json")
    if matrix_path.exists():
        arch_scripts = [
            (
                "scripts/architecture/enforce_provider_boundaries.py",
                "Provider Architecture Boundaries",
            ),
            (
                "scripts/architecture/enforce_provider_manifests.py",
                "Provider Manifests & Graph",
            ),
            (
                "scripts/architecture/enforce_provider_evidence.py",
                "Provider Removability Evidence",
            ),
        ]
        for script_path, step_name in arch_scripts:
            if Path(script_path).exists():
                steps.append(
                    (
                        [
                            "python",
                            script_path,
                            "--root",
                            ".",
                            "--matrix",
                            str(matrix_path),
                        ],
                        step_name,
                    )
                )

    for command, name in steps:
        success = run_command(command, name)
        if not success:
            sys.exit(1)

    print("========================================")
    print("[SUCCESS] All quality gates passed!")
    print("========================================\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
