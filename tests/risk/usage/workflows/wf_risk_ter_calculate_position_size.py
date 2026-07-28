"""WF-RISK-TER: calculate a bounded position size from current evidence."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from decimal import Decimal

from app.services.risk import PositionSizingRequest, calculate_position_size
from tests.risk._support import unwrap_risk_response
from tests.risk.usage.workflows._support import examples

WORKFLOW_ID = "WF-RISK-TER"
STAGES = (
    "Accept PositionSizingRequest and current portfolio, stop, broker, and model evidence.",
    "Validate required method-specific evidence and deterministic fallback policy.",
    "Calculate raw size using the selected supported method.",
    "Clamp or reject against supplied constraints without a synthetic lot fallback.",
    "Return PositionSizingResult for inclusion in a RiskDecision.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Risk receives current sizing request and evidence.
    _stage(1)
    config = examples._config()
    snapshot = examples._snapshot(config)
    request = PositionSizingRequest(
        method="fixed_risk",
        requested_size=None,
        fixed_lot=None,
        risk_amount=Decimal(1000),
        risk_fraction=None,
        stop_distance=Decimal(100),
        unit_value=Decimal(10),
        milestone_multiplier=None,
        win_rate=None,
        payoff_ratio=None,
        trade_count=None,
        volatility_multiplier=None,
        asset_volatility=None,
        broker_min_size=Decimal("0.01"),
        broker_max_size=Decimal(100),
        broker_size_step=Decimal("0.01"),
        evidence_refs={"snapshot": snapshot.snapshot_id},
        request_id=examples.REQUEST_ID,
    )
    print("Input method:", request.method)
    # Stage 2: Inspect complete evidence before sizing.
    _stage(2)
    print("Snapshot:", snapshot.snapshot_id, snapshot.equity)
    # Stage 3: Execute the selected calculator.
    _stage(3)
    result = unwrap_risk_response(
        calculate_position_size(request, snapshot, config),
        operation="calculate_position_size",
    )
    print("Calculated size:", result.calculated_size)
    # Stage 4: Report the applied constraint/fallback evidence.
    _stage(4)
    print(
        "Constraints/fallback:",
        result.constraints_applied,
        result.fallback_used,
    )
    # Stage 5 — OUTPUT BOUNDARY: Return internal PositionSizingResult only.
    _stage(5)
    print("Output:", type(result).__name__, result.normalized_size)


if __name__ == "__main__":
    main()
