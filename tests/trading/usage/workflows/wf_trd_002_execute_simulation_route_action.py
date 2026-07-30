"""WF-TRD-002: execute one governed Simulation-route action."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.trading import (
    build_execution_plan,
    create_readiness_assessment,
    dispatch_order_intent,
    validate_order_request,
)
from tests.trading.usage.workflows._support import examples

WORKFLOW_ID = "WF-TRD-002"
STAGES = (
    "Accept an approved route='sim' TradingRequest.",
    "Validate canonical request and build OrderIntent material.",
    "Dispatch through Simulation authority only.",
    "Let Simulation mutate simulated state and return canonical receipt.",
    "Return canonical ExecutionReceipt without inventing a local fill.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


async def run() -> None:
    """Run the asynchronous documented workflow."""
    # Stage 1 — INPUT BOUNDARY: Approved sim request enters Trading.
    _stage(1)
    request = examples.trading_request()
    print("Input:", request.route, request.action)
    # Stage 2: Validate request before authority selection.
    _stage(2)
    capability, _ = examples.symbol_capability(
        request.route, request.provider_id, request.symbol
    )
    validated_response = validate_order_request(
        request, examples.account_snapshot(), capability
    )
    assert validated_response.data is not None
    readiness = create_readiness_assessment(
        passed=True,
        failed_check_codes=(),
        evidence_refs={"simulation": "current"},
        assessed_at=examples.NOW,
    )
    intent_response = build_execution_plan(validated_response.data, readiness)
    assert intent_response.data is not None
    intent = intent_response.data
    print("Validation passed; intent:", intent.client_order_id)
    # Stage 3: Dispatch selects Simulation authority.
    _stage(3)
    dependencies = examples.trading_dependencies()
    receipt_response = await dispatch_order_intent(
        intent,
        dependencies.connection,
        dependencies.broker_adapter,
        dependencies.simulation_dispatch,
        operation_timeout_seconds=dependencies.broker_operation_timeout_seconds,
        clock=dependencies.clock,
    )
    assert receipt_response.data is not None
    receipt = receipt_response.data
    print("Authority:", receipt.authority)
    # Stage 4: Read canonical simulated receipt truth.
    _stage(4)
    print("Receipt route/status:", receipt.route, receipt.status)
    # Stage 5 — OUTPUT BOUNDARY: Return canonical envelope.
    _stage(5)
    print("Output:", type(receipt).__name__, receipt.status)


def main() -> None:
    """Run the workflow."""
    asyncio.run(run())


if __name__ == "__main__":
    main()
