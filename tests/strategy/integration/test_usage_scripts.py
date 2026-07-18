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
    "06_vectorized.py",
    "07_event.py",
    "08_naive_ma_trend.py",
    "09_decomposing_trade.py",
    "10_harriet_hedging.py",
    "11_market_structure.py",
    "12_random_walk.py",
    "13_sqx_breakout_atr_trailing.py",
    "14_white_fairy.py",
)
_SIGNAL_SCRIPTS = {
    "08_naive_ma_trend.py",
    "09_decomposing_trade.py",
    "10_harriet_hedging.py",
    "13_sqx_breakout_atr_trailing.py",
    "14_white_fairy.py",
}
_UNAVAILABLE_EXIT = 3


@pytest.mark.parametrize("script_name", _USAGE_SCRIPTS)
def test_strategy_usage_script_executes_or_reports_unavailable(
    script_name: str,
) -> None:
    """Execute one fixed standalone Strategy usage script.

    Args:
        script_name: Fixed repository script selected by parametrization.
    """
    usage_directory = Path(__file__).parents[1] / "usage"
    environment = os.environ.copy()
    environment.pop("RUN_STRATEGY_STATEFUL_USAGE", None)
    completed = subprocess.run(  # noqa: S603 - fixed repository script list.
        [sys.executable, str(usage_directory / script_name)],
        check=False,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parents[3],
        env=environment,
        timeout=120,
    )
    if completed.returncode == _UNAVAILABLE_EXIT:
        pytest.skip(f"{script_name}: required real evidence is unavailable")
    assert completed.returncode == 0, (
        f"{script_name} failed\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
    assert completed.stdout.strip(), f"{script_name} produced no visible output"
    if script_name in _SIGNAL_SCRIPTS:
        assert "active=" in completed.stdout
        assert "Evaluated" in completed.stdout
