"""WF-TRD-SEC: validate and package one route-aware action."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.trading import (
    ReadinessAssessment,
    build_execution_plan,
    validate_order_request,
)
from tests.trading.usage.workflows._support import examples

WORKFLOW_ID = "WF-TRD-SEC"
STAGES = (
    "Accept canonical TradingRequest with immutable route, intent, Risk, approval, and trace references.",
    "Validate Decimal values, instrument constraints, identity, and operation preconditions.",
    "Accept explicit current readiness evidence.",
    "Build deterministic execution-plan material without mutation authority.",
    "Return validated package or structured TradingError.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Upstream supplies canonical governed request.
    _stage(1)
    request = examples.trading_request()
    capability, _ = examples.symbol_capability(
        request.route, request.provider_id, request.symbol
    )
    print("Input:", request.action, request.route, request.symbol)
    # Stage 2: Validate through the public boundary.
    _stage(2)
    validated = validate_order_request(request, examples.account_snapshot(), capability)
    print("Validated:", validated.request_id)
    # Stage 3: Supply explicit readiness evidence.
    _stage(3)
    readiness = ReadinessAssessment(
        passed=True,
        failed_check_codes=(),
        evidence_refs={"data": "snapshot"},
        assessed_at=examples.NOW,
    )
    print("Readiness:", readiness.passed)
    # Stage 4: Build deterministic package material.
    _stage(4)
    plan = build_execution_plan(validated, readiness)
    print("Packaged volume:", plan.approved_volume)
    # Stage 5 — OUTPUT BOUNDARY: Return package; no authority mutation occurs.
    _stage(5)
    print("Output:", type(plan).__name__, "No broker mutation was transmitted")


if __name__ == "__main__":
    main()
