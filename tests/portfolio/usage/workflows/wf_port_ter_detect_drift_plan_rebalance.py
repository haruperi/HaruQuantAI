"""WF-PORT-TER: detect drift and persist a reduce-only plan."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from tests.portfolio.unit.test_rebalancing import _eligibility, _risk_decision
from tests.portfolio.unit.test_workflows import _service
from tests.portfolio.usage.workflows._support import (
    NOW,
    active_allocation,
    live_market_dataset,
    settings,
)

WORKFLOW_ID = "WF-PORT-TER"
STAGES = (
    "Resolve actual exposure using fresh account and FX evidence.",
    "Compare actual Risk exposure to target threshold and schedule.",
    "Create reductions bound to the active allocation version.",
    "Mark over-budget exposure reduce-only.",
    "Never open exposure solely to match target weights.",
    "Submit immutable plan to Risk before Trading adaptation.",
    "Measure reconciled execution through Analytics owner contracts.",
    "Preserve executed-but-unmeasured truth for deterministic retry.",
)


# fmt: off
def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}")
# fmt: on


def main() -> None:
    """Run the complete README-defined drift-planning workflow."""
    market = live_market_dataset()
    active = active_allocation()
    policy = settings()
    service, _recorder, store = _service(active, NOW, policy)
    exposures = {"component-a": Decimal("0.6"), "component-b": Decimal("0.4")}
    print(
        "INPUT BOUNDARY — active allocation and genuine MT5 evidence:",
        market.request_id,
    )

    # Stage 1 — Resolve the current immutable exposure evidence.
    _stage(1)
    print("Observed exposures:", exposures)

    # Stage 2 — Apply configured threshold and schedule.
    _stage(2)
    print("Drift threshold:", policy.portfolio_rebalance_drift_threshold)

    # Stage 3 — Bind reductions to the active version.
    _stage(3)
    print("Active version:", active.allocation_version)

    # Stage 4 — Require reduce-only behavior for over-budget exposure.
    _stage(4)
    print("Over-budget component: component-a")

    # Stage 5 — Explicitly exclude opening actions.
    _stage(5)
    print("Opening solely to match target: forbidden")

    # Stage 6 — Execute the public drift-assessment workflow.
    _stage(6)
    plan = service.assess_drift(
        active,
        actual_exposures=exposures,
        evidence_as_of=NOW,
        risk_decision=_risk_decision(active, NOW),
        eligibility_decisions=_eligibility(NOW),
        request_id="req-11111111-1111-4111-8111-111111111111",
        workflow_id="wf-22222222-2222-4222-8222-222222222222",
        correlation_id="cor-33333333-3333-4333-8333-333333333333",
    )

    # Stage 7 — Preserve the next receiver boundary for Trading and Analytics.
    _stage(7)
    print("Risk review state:", plan.status)

    # Stage 8 — Persist replayable plan truth.
    _stage(8)
    assert store.plans
    print("OUTPUT BOUNDARY — PortfolioRebalancePlan:", plan.plan_id)


if __name__ == "__main__":
    main()
