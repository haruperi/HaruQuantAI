"""Integration evidence that every documented Optimization usage script is runnable."""

import subprocess
import sys
from pathlib import Path

import pytest

_USAGE_SCRIPTS = (
    "01_parameters.py",
    "02_scoring.py",
    "03_search.py",
    "04_execution.py",
    "05_robustness.py",
    "06_state.py",
    "07_evidence.py",
    "08_validation.py",
    "09_public_api.py",
)


@pytest.mark.parametrize("script_name", _USAGE_SCRIPTS)
def test_optimization_usage_script_executes(script_name: str) -> None:
    """Run one standalone Optimization usage script in an isolated Python process."""
    usage_directory = Path(__file__).parents[1] / "usage"
    completed = subprocess.run(
        [sys.executable, str(usage_directory / script_name)],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parents[3],
        timeout=120,
    )
    assert completed.returncode == 0, (
        f"{script_name} failed\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
    assert completed.stdout.strip(), f"{script_name} produced no visible output"
