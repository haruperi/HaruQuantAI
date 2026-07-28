"""WF-TRD-011: build immutable execution and reconciliation evidence."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.trading import build_trading_report
from tests.trading.usage.workflows._support import examples

WORKFLOW_ID = "WF-TRD-011"
STAGES = (
    "Accept Trading-owned receipts, trade records, readiness, incidents, and reconciliation facts.",
    "Read immutable execution evidence through the injected report store.",
    "Assemble the registered execution-evidence schema.",
    "Exclude Analytics performance metrics and preserve unresolved warnings.",
    "Return immutable report to Analytics/Portfolio/UI/API.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Trading report request plus injected evidence store.
    _stage(1)
    request, store = (
        examples.trading_request(action="sync_positions"),
        examples.ReportStore(),
    )
    print("Input:", request.action)
    # Stage 2: Public report builder reads official evidence.
    _stage(2)
    outcome = build_trading_report(request, store)
    # Stage 3: Inspect registered schema.
    _stage(3)
    report = outcome.data["report"]
    print("Schema:", report["schema_id"])
    # Stage 4: Preserve execution-only ownership.
    _stage(4)
    print(
        "Evidence keys:",
        tuple(report["evidence"]),
        "contains performance:",
        "performance" in str(report).lower(),
    )
    # Stage 5 — OUTPUT BOUNDARY: Return StandardResponse with immutable report data.
    _stage(5)
    print("Output:", type(outcome).__name__, outcome.status)


if __name__ == "__main__":
    main()
