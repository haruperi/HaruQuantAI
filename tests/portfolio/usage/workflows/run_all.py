"""Execute every active Portfolio workflow usage program."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from tests.portfolio.usage.workflows._support import (
    _DATASET_ENV,
    live_market_dataset,
)

WORKFLOWS = (
    "wf_port_001_validate_construction_evidence.py",
    "wf_port_002_construct_allocation_candidate.py",
    "wf_port_003_coordinate_simulation_risk_review.py",
    "wf_port_004_activate_allocation_version.py",
    "wf_port_005_detect_drift_plan_rebalance.py",
    "wf_port_006_submit_measure_rebalance.py",
    "wf_port_007_rollback_allocation.py",
)


def main() -> None:
    """Capture MT5 evidence once and execute workflows in isolated processes."""
    dataset = live_market_dataset()
    with tempfile.TemporaryDirectory(prefix="wf-port-") as directory:
        evidence = Path(directory) / "market-dataset.json"
        evidence.write_text(dataset.model_dump_json(), encoding="utf-8")
        environment = {**os.environ, _DATASET_ENV: str(evidence)}
        for filename in WORKFLOWS:
            subprocess.run(  # noqa: S603 - filenames are a fixed local tuple.
                [sys.executable, str(Path(__file__).with_name(filename))],
                check=True,
                env=environment,
            )
    print(f"\nPortfolio workflows completed: {len(WORKFLOWS)}/{len(WORKFLOWS)}")


if __name__ == "__main__":
    main()
