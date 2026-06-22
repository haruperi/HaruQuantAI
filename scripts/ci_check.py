#!/usr/bin/env python
"""CI check script for HaruQuantAI.

Runs Ruff format check, Ruff check, mypy, and pytest in sequence.
"""

import subprocess
import sys
import time


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
    # On Windows, we run commands via uv run
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
    steps = [
        (["ruff", "format", "--check", "."], "Ruff Format Check"),
        (["ruff", "check", "."], "Ruff Lint Check"),
        (["mypy", "."], "Mypy Type Check"),
        (["pytest"], "Pytest & Coverage"),
    ]

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
