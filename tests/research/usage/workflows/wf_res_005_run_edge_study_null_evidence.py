"""WF-RES-005: compare one edge study with matching null evidence."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.research import StatisticalConfig, StudyConfig
from app.services.research.leakage import enforce_time_split
from app.services.research.studies import (
    compare_to_null,
    run_eds_mean_reversion,
    run_eds_null_baseline,
)
from tests.research.usage.workflows._support import limits, prepared_dataset

WORKFLOW_ID = "WF-RES-005"
STAGES = (
    "Receive chronological split data, deterministic seed, and study policy.",
    "Build the direction- and horizon-matched null baseline.",
    "Run the selected bounded edge study on the declared test split.",
    "Compare observed and null evidence and return advisory classification.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def main() -> None:
    """Execute the documented edge-study workflow."""
    print(f"{WORKFLOW_ID} — Run Edge Study Against Null Evidence")
    print("INPUT BOUNDARY — split genuine MT5 data plus statistical/study policy")

    # Stage 1 — Receive chronological split data, deterministic seed, and study policy.
    _stage(1)
    split = enforce_time_split(
        prepared_dataset().data,
        train_fraction=0.5,
        validation_fraction=0.2,
    )
    statistics = StatisticalConfig(7, 20, 20, 2, 20, "benjamini_hochberg")
    study = StudyConfig(
        {
            "lookback": 3,
            "entry_zscore": 0.5,
            "hold_bars": 1,
            "side": "buy",
            "minimum_samples": 1,
            "q": 0.05,
            "null_quantile": 0.95,
        },
        {},
        {},
    )

    # Stage 2 — Build the direction- and horizon-matched null baseline.
    _stage(2)
    baseline = run_eds_null_baseline(
        split.test,
        split=split,
        statistics=statistics,
        study=study,
    )

    # Stage 3 — Run the selected bounded edge study on the declared test split.
    _stage(3)
    observed = run_eds_mean_reversion(
        split.test,
        split=split,
        study=study,
        statistics=statistics,
        limits=limits(),
    )

    # Stage 4 — Compare observed and null evidence and return advisory classification.
    _stage(4)
    comparison = compare_to_null(observed, baseline)
    print(
        "OUTPUT BOUNDARY — typed EdgeResult and null comparison:",
        observed.classification,
        comparison["p_value"],
    )


if __name__ == "__main__":
    main()
