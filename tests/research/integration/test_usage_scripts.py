"""Integration evidence that every documented Research usage script is runnable."""

import subprocess
import sys
from pathlib import Path

import pytest

_USAGE_SCRIPTS = (
    "01_contracts.py",
    "02_data.py",
    "03_features.py",
    "04_leakage.py",
    "05_metrics.py",
    "06_statistics.py",
)


@pytest.mark.parametrize("script_name", _USAGE_SCRIPTS)
def test_research_usage_script_executes(script_name: str) -> None:
    """Run one standalone Research usage script in an isolated Python process."""
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
