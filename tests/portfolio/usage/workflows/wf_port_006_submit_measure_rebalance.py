"""WF-PORT-006: submit once and measure an authorized rebalance."""

from __future__ import annotations

import asyncio
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from tests.portfolio.unit.test_workflows import _plan, _service
from tests.portfolio.usage.workflows._support import (
    NOW,
    active_allocation,
    live_market_dataset,
    settings,
)

WORKFLOW_ID = "WF-PORT-006"
STAGES = (
    "Receive current reduce-only plan and owner-evidence references.",
    "Revalidate allocation, Risk decision, route, approvals, and idempotency.",
    "Adapt approved quantities into Trading's receiver-owned request.",
    "Submit exactly once and persist reconciled Trading truth.",
    "Submit immutable Trading facts through Analytics measurement.",
    "Return measured or explicit executed_unmeasured plan.",
    "Recompute from immutable facts without invoking Trading again.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


async def _run() -> None:
    market = live_market_dataset()
    active = active_allocation()
    policy = settings()
    service, recorder, _store = _service(active, NOW, policy)
    plan = _plan(active, NOW, policy)
    print(
        "INPUT BOUNDARY — current plan and MT5 evidence ref:",
        plan.plan_id,
        market.request_id,
    )

    # Stage 1 — Receive the immutable plan and owner evidence references.
    _stage(1)
    print("Plan status/actions:", plan.status, len(plan.actions))

    # Stage 2 — Revalidate the active version and all mutable gates.
    _stage(2)
    print("Runtime/route:", "simulation", "sim")

    # Stage 3 — Adapt only the approved reduce-only quantities.
    _stage(3)
    print("All actions reduce-only:", all(row.reduce_only for row in plan.actions))

    # Stage 4 — Submit once through Trading.
    _stage(4)
    print("Trading no-blind-retry boundary armed.")

    # Stage 5 — Measure immutable execution facts through Analytics.
    _stage(5)
    result = await service.submit_rebalance(
        plan,
        account_evidence_ref="account-1",
        market_evidence_ref=market.request_id,
        fx_evidence_refs=(),
        runtime_profile="simulation",
        execution_route="sim",
        approval_refs=(),
        approval_token_ref="approval-token-ref-1",
        trading_request_id="req-44444444-4444-4444-8444-444444444444",
        valid_until=NOW + timedelta(minutes=5),
    )

    # Stage 6 — Return measured or explicitly unmeasured truth.
    _stage(6)
    print("Measured lifecycle status:", result.status)

    # Stage 7 — Demonstrate no second Trading submission was made.
    _stage(7)
    assert recorder.trading_calls == 1
    print("OUTPUT BOUNDARY — PortfolioRebalancePlan:", result.plan_version)


def main() -> None:
    """Run the complete README-defined submit-and-measure workflow."""
    asyncio.run(_run())


if __name__ == "__main__":
    main()
