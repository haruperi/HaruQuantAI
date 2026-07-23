"""Integration evidence that every documented DATA usage script is runnable."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

_USAGE_SCRIPTS = (
    "01_contracts.py",
    "02_market_data.py",
    "03_local_datasets.py",
    "04_synthetic_data.py",
    "05_tick_derivation.py",
    "06_persistence.py",
    "07_quality.py",
    "08_transformation.py",
    "09_time_sessions.py",
    "10_sources.py",
    "11_economic_calendar.py",
    "12_realtime_feeds.py",
    "13_data_jobs.py",
    "14_evidence.py",
    "15_audit.py",
)


@pytest.mark.parametrize("script_name", _USAGE_SCRIPTS)
def test_documented_usage_script_executes_real_work(script_name: str) -> None:
    """Run one standalone usage script in an isolated Python process."""
    usage_directory = Path(__file__).parents[1] / "usage"
    environment = os.environ.copy()
    environment.pop("DATA_USAGE_LIVE_PROVIDERS", None)
    environment["MT5_ENABLED"] = "false"
    completed = subprocess.run(  # noqa: S603 - fixed repository script invocation.
        [sys.executable, str(usage_directory / script_name)],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parents[3],
        env=environment,
        timeout=120,
    )
    assert completed.returncode == 0, (
        f"{script_name} failed\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
