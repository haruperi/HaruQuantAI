"""WF-PORT-001: validate construction evidence from input to typed output."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.portfolio import execute_portfolio_handle_operation
from tests.portfolio.usage.workflows._support import construction_workflow

WORKFLOW_ID = "WF-PORT-001"
STAGES = (
    "Receive typed PortfolioConstructionRequest.",
    "Resolve immutable Strategy references and current Risk eligibility.",
    "Resolve Data account, genuine MT5 market, FX, and Analytics evidence.",
    "Validate versions, hashes, UTC freshness, coverage, observations, and config.",
    "Return immutable ValidatedConstructionEvidence without publishing a candidate.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def main() -> None:
    """Run the complete README-defined construction-validation workflow."""
    service, request, store, market = construction_workflow()
    print("INPUT BOUNDARY — typed PortfolioConstructionRequest:", request.request_id)

    # Stage 1 — Receive the typed owner request.
    _stage(1)
    print("Portfolio/version:", request.portfolio_id, request.portfolio_version)

    # Stage 2 — Resolve Strategy and Risk owner references through dependencies.
    _stage(2)
    print("Referenced components:", len(request.components))

    # Stage 3 — Resolve genuine MT5 Data evidence and remaining owner evidence.
    _stage(3)
    print(
        "Real market evidence:",
        market.source_metadata["source_id"],
        market.request_id,
        len(market.records),
    )

    # Stage 4 — Run the public fail-closed evidence validator workflow.
    _stage(4)
    evidence = execute_portfolio_handle_operation(
        service, "validate_construction", request
    )

    # Stage 5 — Return typed immutable evidence without publishing candidate state.
    _stage(5)
    assert not store.constructions
    print("OUTPUT BOUNDARY — ValidatedConstructionEvidence:", evidence.evidence_hash)


if __name__ == "__main__":
    main()
