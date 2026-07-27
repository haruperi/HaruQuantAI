"""WF-OPT-006: assemble, persist, and hand off versioned evidence."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.optimization.evidence import (
    build_optimization_evidence,
    build_report_package,
)
from app.services.optimization.public_api import build_optimization_handoff
from app.services.optimization.state import persist_optimization_result
from tests.optimization.unit.test_evidence_contracts import evidence_request
from tests.optimization.unit.test_state_contracts import MemoryOptimizationStore

WORKFLOW_ID = "WF-OPT-006"
STAGES = (
    "Receive completed or explicitly incomplete Optimization-owned evidence.",
    "Build OptimizationResult v1 without recomputing owner evidence.",
    "Build a chart-ready report package without rendering.",
    "Persist result and ranked evidence atomically through the injected store.",
    "Build and return the advisory Optimization handoff.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def main() -> None:
    """Execute the documented evidence/handoff workflow."""
    print(f"{WORKFLOW_ID} — Build Versioned Evidence and Handoffs")
    print("INPUT BOUNDARY — Optimization evidence assembly request")

    # Stage 1 — Receive completed or explicitly incomplete Optimization-owned evidence.
    _stage(1)
    request = evidence_request()

    # Stage 2 — Build OptimizationResult v1 without recomputing owner evidence.
    _stage(2)
    result = build_optimization_evidence(request)

    # Stage 3 — Build a chart-ready report package without rendering.
    _stage(3)
    report = build_report_package(result)

    # Stage 4 — Persist result and ranked evidence atomically through the injected store.
    _stage(4)
    receipt = persist_optimization_result(result, MemoryOptimizationStore())

    # Stage 5 — Build and return the advisory Optimization handoff.
    _stage(5)
    handoff = build_optimization_handoff(request)
    print("Report/durable:", report["schema_id"], receipt.durable)
    print("OUTPUT BOUNDARY — typed OptimizationResult v1:", handoff.schema_id)


if __name__ == "__main__":
    main()
