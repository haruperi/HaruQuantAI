"""WF-ANLT-TER: calculate deterministic grouped Analytics evidence."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.analytics import calculate_grouped_evidence
from tests.analytics.usage.workflows._support import examples

WORKFLOW_ID = "WF-ANLT-TER"
STAGES = (
    "Accept canonical trades and series.",
    "Split only by explicit approved source context.",
    "Run cataloged kernels with finite/semantic validation.",
    "Represent empty or undefined evidence explicitly rather than as zero.",
    "Return ordered SectionEvidence groups.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Canonical Analytics TradingResult enters metric calculation.
    _stage(1)
    result, config = examples._configured_result()
    print("Input trades:", len(result.trades))
    # Stage 2: Source contexts stay explicit.
    _stage(2)
    print("Directions:", tuple(trade.type for trade in result.trades))
    # Stage 3: Execute public grouped metric calculation.
    _stage(3)
    sections = examples.unwrap(calculate_grouped_evidence(result, config=config))
    print("Sections:", tuple(section.section_key for section in sections))
    # Stage 4: Show explicit metric statuses.
    _stage(4)
    print(
        "Statuses:",
        {metric.status for section in sections for metric in section.metrics},
    )
    # Stage 5 — OUTPUT BOUNDARY: Return ordered SectionEvidence tuple.
    _stage(5)
    print("Output:", len(sections), "SectionEvidence values")


if __name__ == "__main__":
    main()
