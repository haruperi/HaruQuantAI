"""Integration execution evidence for static Indicators workflow scripts."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

_STATIC_WORKFLOW_SCRIPTS = ("wf_indi_008_capability_matrix_introspection.py",)


@pytest.mark.parametrize("script_name", _STATIC_WORKFLOW_SCRIPTS)
def test_static_indicator_workflow_executes(script_name: str) -> None:
    """Execute static, network-free workflow scripts in default integration suite."""
    repository_root = Path(__file__).parents[3]
    workflow_directory = Path(__file__).parents[1] / "usage" / "workflows"
    with tempfile.TemporaryDirectory(
        prefix="haruquant-indicators-workflow-"
    ) as temporary_directory:
        temporary_root = Path(temporary_directory)
        log_directory = temporary_root / "logs"
        log_directory.mkdir()
        environment = os.environ.copy()
        environment.update(
            {
                "DATABASE_URL": "sqlite:///workflow.db",
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
