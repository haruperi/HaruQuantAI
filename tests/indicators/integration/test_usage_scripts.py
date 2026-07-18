"""Integration evidence that every indicators usage script is runnable."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

_USAGE_SCRIPTS = (
    "01_core.py",
    "02_candles.py",
    "03_trend.py",
    "04_momentum.py",
    "05_volatility.py",
    "06_volume.py",
)


# Exit code a usage script returns when the live market-data source is
# unavailable, signalling a skip rather than a real failure.
_LIVE_DATA_UNAVAILABLE_EXIT = 3


@pytest.mark.parametrize("script_name", _USAGE_SCRIPTS)
def test_indicators_usage_script_executes_successfully(script_name: str) -> None:
    """Run one standalone usage script in an isolated Python process.

    A return code of ``0`` means the example ran fully against real data. A
    return code of ``3`` means the live market-data source was unavailable, so
    the example is skipped rather than failed (this keeps missing-data
    environments from masking a genuine regression). Any other code fails.
    """
    usage_directory = Path(__file__).parents[1] / "usage"
    environment = os.environ.copy()
    completed = subprocess.run(  # noqa: S603 - fixed repository script invocation.
        [sys.executable, str(usage_directory / script_name)],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parents[3],
        env=environment,
        timeout=120,
    )
    if completed.returncode == _LIVE_DATA_UNAVAILABLE_EXIT:
        pytest.skip(f"{script_name}: live market data unavailable")
    assert completed.returncode == 0, (
        f"{script_name} failed\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
