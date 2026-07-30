"""Execute every active Optimization workflow usage program."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from tests.optimization.usage.workflows._support import (
    _DATASET_ENV,
    live_market_dataset,
)

WORKFLOWS = (
    "wf_opt_001_package_optimization_robustness_request.py",
    "wf_opt_pri_execute_bounded_parameter_sweep.py",
    "wf_opt_ter_score_rank_assess_overfit_evidence.py",
    "wf_opt_sec_run_walk_forward_validation.py",
    "wf_opt_005_run_monte_carlo_robustness_analysis.py",
    "wf_opt_006_build_persist_versioned_evidence_handoffs.py",
    "wf_opt_007_compare_runs_parameter_stability.py",
    "wf_opt_008_first_passage_drawdown_sensitivity.py",
)


def main() -> None:
    """Capture MT5 evidence once and execute workflows in isolated processes."""
    dataset = live_market_dataset()
    with tempfile.TemporaryDirectory(prefix="wf-opt-") as directory:
        evidence = Path(directory) / "market-dataset.json"
        evidence.write_text(dataset.model_dump_json(), encoding="utf-8")
        environment = {**os.environ, _DATASET_ENV: str(evidence)}
        for filename in WORKFLOWS:
            subprocess.run(  # noqa: S603 - filenames are a fixed local tuple.
                [sys.executable, str(Path(__file__).with_name(filename))],
                check=True,
                env=environment,
            )
    print(f"\nOptimization workflows completed: {len(WORKFLOWS)}/{len(WORKFLOWS)}")


if __name__ == "__main__":
    main()
