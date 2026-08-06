"""Live execution evidence for MT5-backed Indicators workflow scripts.

This suite is isolated under tests/indicators/live and requires explicit opt-in
via INDICATORS_USAGE_LIVE_MT5=1 and ENVIRONMENT=dev.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

pytestmark = [
    pytest.mark.skipif(
        os.environ.get("INDICATORS_USAGE_LIVE_MT5") != "1",
        reason="genuine MT5 workflow evidence requires explicit INDICATORS_USAGE_LIVE_MT5=1 opt-in",
    ),
    pytest.mark.skipif(
        os.environ.get("ENVIRONMENT", "dev") != "dev",
        reason="live workflow tests are restricted to ENVIRONMENT=dev",
    ),
]

_LIVE_WORKFLOW_SCRIPTS = (
    "wf_indi_006_candlestick_pattern_detection.py",
    "wf_indi_007_volume_profile_distribution.py",
)


@pytest.mark.parametrize("script_name", _LIVE_WORKFLOW_SCRIPTS)
def test_live_indicator_workflow_executes(script_name: str) -> None:
    """Execute one MT5-backed workflow script in opt-in live test suite."""
    repository_root = Path(__file__).parents[3]
    workflow_directory = Path(__file__).parents[1] / "usage" / "workflows"
    with tempfile.TemporaryDirectory(
        prefix="haruquant-indicators-live-workflow-"
    ) as temporary_directory:
        temporary_root = Path(temporary_directory)
        log_directory = temporary_root / "logs"
        log_directory.mkdir()
        environment = os.environ.copy()
        environment.update(
            {
                "DATABASE_URL": "sqlite:///workflow_live.db",
                "DATA_DIR": str(temporary_root),
                "ENVIRONMENT": "dev",
                "LOG_DIRECTORY": str(log_directory),
                "LOG_FILE_PATH": str(log_directory / "app.log"),
                "PYTHONDONTWRITEBYTECODE": "1",
                "RUNTIME_PROFILE": "research",
                "SQLITE_BUSY_TIMEOUT_SECONDS": "1",
                "WRITE_LOCK_LEASE_SECONDS": "30",
            }
        )
        completed = subprocess.run(  # noqa: S603 - repository-controlled command
            [sys.executable, str(workflow_directory / script_name)],
            check=False,
            capture_output=True,
            text=True,
            cwd=repository_root,
            env=environment,
            timeout=120,
        )
    assert completed.returncode == 0, (
        f"{script_name} failed\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
    assert "Genuine input" in completed.stdout
