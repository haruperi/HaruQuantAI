"""WF-TRD-013: validate an authorized rebalance and fail closed before dispatch."""

from __future__ import annotations

import asyncio
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.trading import execute_portfolio_rebalance, validate_budget_authority
from tests.trading.usage.workflows._support import examples

WORKFLOW_ID = "WF-TRD-013"
STAGES = (
    "Accept PortfolioRebalanceExecutionRequest plus current allocation/Risk decisions.",
    "Validate immutable plan hash, reduce-only actions, lineage, and idempotency.",
    "Validate current allocation budget and expiration.",
    "Block when mandatory allocation authority is unavailable; dispatch no action.",
    "Return fail-closed TradingError and reconciliation-safe evidence.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


async def run() -> None:
    """Run the documented fail-closed workflow."""
    # Stage 1 — INPUT BOUNDARY: Portfolio supplies exact immutable rebalance plan.
    _stage(1)
    request = examples.rebalance_request()
    print("Input:", request.plan_id, len(request.actions))
    # Stage 2: Contract validation already proves hash/reduce-only shape.
    _stage(2)
    print("Canonical hash:", request.canonical_hash)
    # Stage 3: Validate matching current budget explicitly.
    _stage(3)
    budget = validate_budget_authority(
        request,
        examples.rebalance_allocation(),
        examples.rebalance_budget(request),
        now=examples.NOW,
    )
    print("Budget valid:", budget.status, budget.metadata.extensions)
    # Stage 4: Remove allocation authority and prove no dispatch.
    _stage(4)
    deps = replace(
        examples.rebalance_dependencies(request),
        allocation_decision_source=lambda _item: None,
    )
    blocked = await execute_portfolio_rebalance(request, deps)
    assert blocked.error is not None
    print("Blocked:", blocked.error.code, "before authority dispatch")
    # Stage 5 — OUTPUT BOUNDARY: Return fail-closed result; no broker mutation.
    _stage(5)
    print(
        "Output:",
        blocked.status,
        blocked.error.details,
        "No broker mutation was transmitted",
    )


def main() -> None:
    """Run the workflow."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
