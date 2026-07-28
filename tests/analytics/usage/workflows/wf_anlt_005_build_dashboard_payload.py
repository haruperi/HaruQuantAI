"""WF-ANLT-005: project a bounded dashboard payload."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.analytics import build_dashboard_payload, truncate_series
from tests.analytics.usage.workflows._support import examples

WORKFLOW_ID = "WF-ANLT-005"
STAGES = (
    "Accept a validated canonical PerformanceReport.",
    "Project approved summary, equity, drawdown, warning, and quality sections.",
    "Apply deterministic series point limits with truncate_series.",
    "Preserve skipped/degraded status without recomputing metrics.",
    "Return versioned non-binding DashboardPayload to UI/API.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: UI/API requests projection of a validated report.
    _stage(1)
    report, _ = examples._report()
    print("Input report:", report.report_id)
    # Stage 2: Project without recomputation.
    _stage(2)
    payload = examples.unwrap(build_dashboard_payload(report))
    print(
        "Projected classes:",
        tuple(section["payload_class"] for section in payload.sections),
    )
    # Stage 3: Demonstrate deterministic point bounding.
    _stage(3)
    result, _ = examples._configured_result()
    truncation_response = truncate_series(result.equity_curve, max_points=2)
    selected = examples.unwrap(truncation_response)
    metadata = truncation_response.metadata.extensions["truncation"]
    print("Selected points:", len(selected), metadata)
    # Stage 4: Preserve report warnings/quality evidence.
    _stage(4)
    print("Warnings preserved:", payload.warnings == report.caveats)
    # Stage 5 — OUTPUT BOUNDARY: Return bounded DashboardPayload.
    _stage(5)
    print("Output:", type(payload).__name__, payload.non_binding)


if __name__ == "__main__":
    main()
