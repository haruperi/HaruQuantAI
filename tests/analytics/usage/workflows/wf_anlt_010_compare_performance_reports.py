"""WF-ANLT-010: compare compatible performance reports."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.analytics import compare_performance_reports
from tests.analytics.usage.workflows._support import examples

WORKFLOW_ID = "WF-ANLT-010"
STAGES = (
    "Accept compatible reference and candidate PerformanceReport values.",
    "Validate schemas and pairing metadata without mutating either report.",
    "Match only approved common metrics.",
    "Calculate actual deltas plus explicit missing metrics and caveats.",
    "Return comparison SectionEvidence without fixed zero differences.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Caller supplies reference and candidate reports.
    _stage(1)
    reference, _ = examples._report(profit=Decimal(10))
    candidate, _ = examples._report(profit=Decimal(30))
    print("Input:", reference.report_id, candidate.report_id)
    # Stage 2: Preserve immutable report values.
    _stage(2)
    before = repr(reference)
    # Stage 3: Public comparer matches approved common metrics.
    _stage(3)
    comparison = compare_performance_reports(reference, candidate)
    print("Common metrics:", len(comparison.metrics))
    # Stage 4: Show real nonzero delta evidence.
    _stage(4)
    print(
        "Deltas:", tuple(metric.value for metric in comparison.metrics if metric.value)
    )
    # Stage 5 — OUTPUT BOUNDARY: Return comparison SectionEvidence.
    _stage(5)
    print(
        "Output:",
        type(comparison).__name__,
        "reference unchanged:",
        before == repr(reference),
    )


if __name__ == "__main__":
    main()
