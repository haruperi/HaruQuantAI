"""WF-TRD-006: read route facts and aggregate readiness."""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.trading import assess_execution_readiness, get_route_snapshot
from tests.trading.usage.workflows._support import examples

WORKFLOW_ID = "WF-TRD-006"
STAGES = (
    "Accept canonical request and Data/Simulation route-fact reader.",
    "Call get_route_snapshot to obtain explicit timestamped available/stale evidence.",
    "Accept current Risk, kill-switch, action-policy, and staleness bounds.",
    "Aggregate required checks with assess_execution_readiness.",
    "Return ReadinessAssessment with bounded explicit failure codes.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Runtime supplies request and route-fact reader.
    _stage(1)
    request = examples.readiness_request()
    print("Input:", request.route, request.account_id)
    # Stage 2: Read canonical route facts through public operation.
    _stage(2)
    snapshot_response = get_route_snapshot(
        request, lambda _route, _provider: examples.readiness_snapshot()
    )
    assert snapshot_response.status == "success"
    assert snapshot_response.data is not None
    snapshot = snapshot_response.data
    print("Snapshot:", snapshot.available, snapshot.fresh)
    # Stage 3: Gather remaining authority evidence.
    _stage(3)
    policy = {
        "allowed": True,
        "verdict_id": "verdict-001",
        "action": "submit_order",
        "expires_at": examples.readiness_risk().expires_at.isoformat(),
    }
    bounds = {
        "route_snapshot": Decimal(30),
        "risk_decision": Decimal(30),
        "kill_switch": Decimal(30),
    }
    # Stage 4: Aggregate readiness.
    _stage(4)
    result_response = assess_execution_readiness(
        request,
        snapshot,
        examples.readiness_risk(),
        examples.readiness_switch(),
        policy,
        bounds,
    )
    assert result_response.status == "success"
    assert result_response.data is not None
    result = result_response.data
    print("Passed:", result.passed, "failures:", result.failed_check_codes)
    # Stage 5 — OUTPUT BOUNDARY: Return timestamped ReadinessAssessment.
    _stage(5)
    print("Output:", result.model_dump(mode="json"))


if __name__ == "__main__":
    main()
