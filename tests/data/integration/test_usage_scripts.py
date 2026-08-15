"""Integration evidence that every documented DATA usage script is runnable."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

_USAGE_SCRIPTS = (
    "01_market_data.py",
    "02_datasets.py",
    "03_synthetic_data.py",
    "04_transformation.py",
    "05_alignment.py",
    "06_integrity.py",
    "07_time_sessions.py",
    "08_economic_calendar.py",
    "09_sources.py",
    "10_market_events.py",
    "11_data_jobs.py",
    "12_evidence.py",
    "13_runtime_stores.py",
    "14_replay.py",
)


@pytest.mark.parametrize("script_name", _USAGE_SCRIPTS)
def test_documented_usage_script_executes_real_work(script_name: str) -> None:
    """Run one network-free standalone usage script in an isolated process.

    Provider-dependent programs must report honest unavailability and still
    execute their deterministic contract evidence without inventing live data.
    """
    usage_directory = Path(__file__).parents[1] / "usage" / "features"
    environment = os.environ.copy()
    environment.pop("DATA_USAGE_LIVE_PROVIDERS", None)
    environment["LOG_LEVEL"] = "ERROR"
    for setting_name in (
        "MT5_ENABLED",
        "CTRADER_ENABLED",
        "BINANCE_ENABLED",
        "DUKASCOPY_ENABLED",
        "YAHOO_ENABLED",
    ):
        environment[setting_name] = "false"
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
    assert completed.stdout.strip(), f"{script_name} produced no actual evidence"
    normalized_output = completed.stdout.lower()
    assert "data" in normalized_output, f"{script_name} omitted actual data evidence"
    assert "success" in normalized_output, f"{script_name} omitted success evidence"


def test_supplemental_legacy_feature_catalog_executes() -> None:
    """Run the unnumbered legacy-logic catalogue without adding a feature row."""
    usage_directory = Path(__file__).parents[1] / "usage" / "features"
    environment = os.environ.copy()
    environment["LOG_LEVEL"] = "CRITICAL"
    for setting_name in (
        "MT5_ENABLED",
        "CTRADER_ENABLED",
        "BINANCE_ENABLED",
        "DUKASCOPY_ENABLED",
        "YAHOO_ENABLED",
    ):
        environment[setting_name] = "false"
    completed = subprocess.run(  # noqa: S603 - fixed repository script invocation.
        [sys.executable, str(usage_directory / "features.py"), "--offline"],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parents[3],
        env=environment,
        timeout=120,
    )
    assert completed.returncode == 0, (
        f"features.py failed\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
    )
    assert "Data scenarios directly" in completed.stdout
    assert "registered feature count remains 14" in completed.stdout
    assert "Traceback" not in completed.stdout
