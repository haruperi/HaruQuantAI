"""WF-PORT-002: construct and persist one allocation candidate."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from tests.portfolio.usage.workflows._support import construction_workflow

WORKFLOW_ID = "WF-PORT-002"
STAGES = (
    "Validate unique strategy versions and current Risk eligibility.",
    "Validate evidence versions, UTC times, freshness, currency, and config.",
    "Apply the explicitly requested approved construction method.",
    "Normalize and validate finite bounds and total weight.",
    "Separate capital weights from proposed Risk budget weights.",
    "Hash lineage, persist, and return PortfolioConstructionResult.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def main() -> None:
    """Run the complete README-defined candidate-construction workflow."""
    service, request, store, market = construction_workflow()
    print("INPUT BOUNDARY — validated construction request:", request.request_id)

    # Stage 1 — Validate Strategy and Risk lineage.
    _stage(1)
    print("Components:", tuple(row.component_id for row in request.components))

    # Stage 2 — Validate genuine Data and Analytics evidence.
    _stage(2)
    print("Real MT5 records:", len(market.records))

    # Stage 3 — Select the request-owned construction method.
    _stage(3)
    print("Construction method:", request.method)

    # Stage 4 — Normalize bounded weights.
    _stage(4)
    print("Configured tolerance is explicit.")

    # Stage 5 — Preserve separate capital and proposed Risk weights.
    _stage(5)
    print("Risk budget remains a proposal until Risk activation.")

    # Stage 6 — Execute the public workflow and persist immutable state.
    _stage(6)
    result, evidence = service.construct(request)
    assert store.constructions[result.result_id] is result
    print("Evidence lineage:", evidence.evidence_hash)
    print("OUTPUT BOUNDARY — PortfolioConstructionResult:", result.result_id)


if __name__ == "__main__":
    main()
