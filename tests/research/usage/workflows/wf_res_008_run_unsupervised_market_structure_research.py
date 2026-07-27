"""WF-RES-008: run bounded unsupervised research."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.research import UnsupervisedResearchConfig
from app.services.research.modeling import run_unsupervised_research
from tests.research.usage.workflows._support import limits, prepared_dataset

WORKFLOW_ID = "WF-RES-008"
STAGES = (
    "Receive the finite leakage-safe feature frame and explicit seed.",
    "Select and scale approved finite feature columns.",
    "Run bounded PCA and seeded K-Means.",
    "Return factor, cluster, diagnostic, and advisory evidence.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def main() -> None:
    """Execute the documented unsupervised workflow."""
    print(f"{WORKFLOW_ID} — Run Unsupervised Market-Structure Research")
    print("INPUT BOUNDARY — leakage-safe MT5-derived feature frame plus seed")

    # Stage 1 — Receive the finite leakage-safe feature frame and explicit seed.
    _stage(1)
    frame = prepared_dataset().data
    config = UnsupervisedResearchConfig(("close", "volume"), True, 2, 2, 20, 7)

    # Stage 2 — Select and scale approved finite feature columns.
    _stage(2)
    selected = frame.loc[:, list(config.feature_columns)]
    assert selected.notna().all().all()

    # Stage 3 — Run bounded PCA and seeded K-Means.
    _stage(3)
    result = run_unsupervised_research(selected, config=config, limits=limits())

    # Stage 4 — Return factor, cluster, diagnostic, and advisory evidence.
    _stage(4)
    print(
        "OUTPUT BOUNDARY — typed UnsupervisedResearchResult:",
        result.seed,
        result.advisory_only,
    )


if __name__ == "__main__":
    main()
