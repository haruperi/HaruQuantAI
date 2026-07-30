"""WF-RES-009: build the advisory scorecard and profile snapshot."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.research import (
    build_core_metric_profile,
    build_research_profile_snapshot,
    build_research_scorecard,
)
from tests.research.usage.workflows._support import limits, prepared_dataset

WORKFLOW_ID = "WF-RES-009"
STAGES = (
    "Receive approved typed stage outputs derived from genuine MT5 evidence.",
    "Build one deterministic ResearchScorecard.",
    "Normalize stage evidence into one versioned ResearchProfileSnapshot.",
    "Return readiness, uncertainty, versions, hashes, and advisory status.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def main() -> None:
    """Execute the documented scorecard/snapshot workflow."""
    print(f"{WORKFLOW_ID} — Build Research Scorecard and Profile Snapshot")
    print("INPUT BOUNDARY — approved Research stage outputs")

    # Stage 1 — Receive approved typed stage outputs derived from genuine MT5 evidence.
    _stage(1)
    prepared = prepared_dataset()
    metrics = build_core_metric_profile(prepared, limits=limits())

    # Stage 2 — Build one deterministic ResearchScorecard.
    _stage(2)
    scorecard = build_research_scorecard(
        metric_profile=metrics,
        seasonality=None,
        edges=(),
        market_structure=None,
        modeling=None,
    )

    # Stage 3 — Normalize stage evidence into one versioned ResearchProfileSnapshot.
    _stage(3)
    snapshot = build_research_profile_snapshot(
        stages={"data": {"schema_version": "v1", "rows": len(prepared.data)}},
        scorecard=scorecard,
        dataset_hash=prepared.dataset_hash,
        configuration_hash=prepared.configuration_hash,
    )

    # Stage 4 — Return readiness, uncertainty, versions, hashes, and advisory status.
    _stage(4)
    print(
        "OUTPUT BOUNDARY — ResearchScorecard and ResearchProfileSnapshot:",
        scorecard.readiness,
        snapshot.schema_version,
    )


if __name__ == "__main__":
    main()
