"""Execute every active Research workflow usage program."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from tests.research.usage.workflows._support import (
    _DATASET_ENV,
    live_market_dataset,
)

WORKFLOWS = (
    "wf_res_sec_prepare_research_dataset.py",
    "wf_res_002_build_core_metric_profile.py",
    "wf_res_003_build_leakage_safe_feature_frame_time_splits.py",
    "wf_res_004_analyze_session_seasonality_opportunity.py",
    "wf_res_ter_run_edge_study_null_evidence.py",
    "wf_res_006_build_market_structure_profile.py",
    "wf_res_007_forward_validate_calibrate_market_structure.py",
    "wf_res_008_run_unsupervised_market_structure_research.py",
    "wf_res_009_build_research_scorecard_profile_snapshot.py",
    "wf_res_010_render_persist_research_artifact.py",
    "wf_res_012_compare_research_profiles_across_periods.py",
    "wf_res_pri_run_complete_edge_lab_profile.py",
)


def main() -> None:
    """Capture MT5 evidence once and execute workflows in isolated processes."""
    dataset = live_market_dataset()
    with tempfile.TemporaryDirectory(prefix="wf-res-") as directory:
        evidence = Path(directory) / "market-dataset.json"
        evidence.write_text(dataset.model_dump_json(), encoding="utf-8")
        environment = {**os.environ, _DATASET_ENV: str(evidence)}
        for filename in WORKFLOWS:
            subprocess.run(  # noqa: S603 - filenames are a fixed local tuple.
                [sys.executable, str(Path(__file__).with_name(filename))],
                check=True,
                env=environment,
            )
    print(f"\nResearch workflows completed: {len(WORKFLOWS)}/{len(WORKFLOWS)}")


if __name__ == "__main__":
    main()
