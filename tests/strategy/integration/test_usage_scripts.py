"""Integration evidence for standalone real-use Strategy scripts."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

_USAGE_SCRIPTS = (
    "01_contracts.py",
    "02_diagnostics.py",
    "03_registry.py",
    "04_intents.py",
    "05_replay.py",
    "06_checkpoints.py",
    "07_vectorized.py",
    "08_event.py",
    "09_signals.py",
    "10_strategy_library.py",
    "11_proposal_intake.py",
)

assert len(_USAGE_SCRIPTS) == 11, "Strategy must register exactly 11 feature programs"


@pytest.mark.parametrize("script_name", _USAGE_SCRIPTS)
def test_strategy_usage_script_executes_with_genuine_evidence(
    script_name: str,
    tmp_path: Path,
) -> None:
    """Execute one fixed standalone Strategy usage script.

    Args:
        script_name: Fixed repository script selected by parametrization.
        tmp_path: Isolated development storage root.
    """
    usage_directory = Path(__file__).parents[1] / "usage" / "features"
    environment = os.environ.copy()
    state_root = tmp_path / script_name.removesuffix(".py")
    state_root.mkdir()
    (state_root / "logs").mkdir()
    environment["RUN_STRATEGY_STATEFUL_USAGE"] = "1"
    environment["ENVIRONMENT"] = "test"
    environment["DATA_DIR"] = str(state_root)
    environment["DATABASE_URL"] = "sqlite:///strategy_usage.sqlite3"
    environment["SQLITE_BUSY_TIMEOUT_SECONDS"] = "1"
    environment["WRITE_LOCK_LEASE_SECONDS"] = "30"
    environment["LOG_DIRECTORY"] = str(state_root / "logs")
    environment["LOG_FILE_PATH"] = str(state_root / "logs" / "strategy.log")
    environment["STRATEGY_AUDIT_BARS"] = "1"
    completed = subprocess.run(  # noqa: S603 - fixed repository script list.
        [sys.executable, str(usage_directory / script_name)],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parents[3],
        env=environment,
        timeout=180,
    )
    assert completed.returncode == 0, (
        f"{script_name} failed\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
    assert completed.stdout.strip(), f"{script_name} produced no visible output"
