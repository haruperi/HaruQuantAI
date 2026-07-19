"""Integration evidence for standalone bounded Trading usage scripts."""

# ruff: noqa: INP001

import subprocess
import sys
from pathlib import Path

import pytest

_USAGE_SCRIPTS = (
    "01_contracts.py",
    "02_state.py",
    "03_validation.py",
    "04_routing.py",
    "05_reconciliation.py",
    "06_monitoring.py",
    "07_live.py",
    "08_actions.py",
    "09_reporting.py",
)


@pytest.mark.parametrize("script_name", _USAGE_SCRIPTS)
def test_trading_usage_script_executes(script_name: str) -> None:
    """Run one fixed standalone Trading usage script successfully.

    Args:
        script_name: Fixed repository script selected by parametrization.
    """
    usage_directory = Path(__file__).parents[1] / "usage"
    completed = subprocess.run(  # noqa: S603 - fixed repository script list.
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
