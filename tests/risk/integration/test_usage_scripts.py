"""Integration evidence that every documented Risk usage script is runnable."""

import subprocess
import sys
from pathlib import Path

import pytest

_USAGE_SCRIPTS = (
    "01_contracts.py",
    "02_config.py",
    "03_portfolio.py",
    "04_sizing.py",
    "05_audit.py",
    "06_limits.py",
    "07_regimes.py",
    "08_admission.py",
    "09_allocation.py",
    "10_approvals.py",
    "11_validity.py",
    "12_governor.py",
    "13_kill_switch.py",
    "14_scenarios.py",
    "15_reporting.py",
)


@pytest.mark.parametrize("script_name", _USAGE_SCRIPTS)
def test_risk_usage_script_executes(script_name: str) -> None:
    """Run one standalone Risk usage script in an isolated Python process."""
    usage_directory = Path(__file__).parents[1] / "usage"
    # Argument vector is the running interpreter plus a path built from a
    # hard-coded literal name joined to this file's own directory. No external
    # or caller-supplied input reaches the process boundary.
    completed = subprocess.run(  # noqa: S603
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
