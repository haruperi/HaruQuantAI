"""Integration evidence that every documented Portfolio usage script is runnable."""

import subprocess
import sys
from pathlib import Path

_USAGE_SCRIPTS = (
    "01_contracts.py",
    "02_evidence.py",
    "03_construction.py",
    "04_state.py",
    "05_allocation.py",
    "06_rebalancing.py",
    "07_orchestration.py",
    "08_public_api.py",
    "features.py",
)


def test_portfolio_usage_scripts_execute() -> None:
    """Run all standalone Portfolio usage programs serially and visibly."""
    usage_directory = Path(__file__).parents[1] / "usage" / "features"
    for script_name in _USAGE_SCRIPTS:
        completed = subprocess.run(  # noqa: S603 - fixed local command.
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
        assert "logging_configuration_failed" not in completed.stderr
