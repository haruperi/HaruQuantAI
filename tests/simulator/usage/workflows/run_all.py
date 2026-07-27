"""Execute every active Simulator workflow usage program."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from tests.simulator.usage.workflows._support import (
    _DATASET_ENV,
    live_market_dataset,
)

WORKFLOWS = (
    "wf_sim_001_official_fx_backtest.py",
    "wf_sim_002_simulation_trader_operations.py",
    "wf_sim_003_optimization_candidate_execution.py",
    "wf_sim_004_severe_data_quality_blocked_run.py",
    "wf_sim_005_deterministic_replay.py",
    "wf_sim_006_registered_strategy_security_rejection.py",
    "wf_sim_007_non_canonical_fast_research.py",
    "wf_sim_009_portfolio_backtest.py",
    "wf_sim_010_tick_series_acquisition.py",
)


def main() -> None:
    """Capture MT5 evidence once and execute workflows in isolated processes."""
    dataset = live_market_dataset()
    with tempfile.TemporaryDirectory(prefix="wf-sim-") as directory:
        evidence = Path(directory) / "market-dataset.json"
        evidence.write_text(dataset.model_dump_json(), encoding="utf-8")
        environment = {**os.environ, _DATASET_ENV: str(evidence)}
        for filename in WORKFLOWS:
            subprocess.run(  # noqa: S603 - filenames are a fixed local tuple.
                [sys.executable, str(Path(__file__).with_name(filename))],
                check=True,
                env=environment,
            )
    print(f"\nSimulator workflows completed: {len(WORKFLOWS)}/{len(WORKFLOWS)}")


if __name__ == "__main__":
    main()
