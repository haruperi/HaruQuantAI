"""WF-TRD-012: accept only a governed immutable upstream request."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.trading import create_trading_request, validate_order_request
from pydantic import ValidationError
from tests.trading.usage.workflows._support import examples

WORKFLOW_ID = "WF-TRD-012"
STAGES = (
    "Accept approved RiskDecision and immutable Strategy/Portfolio lineage.",
    "Construct exact TradingRequest; reject raw signals or translation fields.",
    "Validate request identity, route, action, Risk, approval, and instrument evidence.",
    "Retain upstream lineage without reinterpreting signals or sizing.",
    "Return validated TradingRequest or structured validation failure.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented governed boundary."""
    # Stage 1 — INPUT BOUNDARY: Upstream supplies canonical Risk-governed material.
    _stage(1)
    request = examples.trading_request()
    print("Input:", request.intent_id, request.risk_decision_id)
    # Stage 2: Raw signal translation is rejected by exact contract.
    _stage(2)
    material = request.model_dump(mode="python")
    material["raw_signal"] = {"direction": "BUY"}
    try:
        create_trading_request(**material)
    except ValidationError:
        print("Raw signal rejected:", True)
    # Stage 3: Validate the canonical request through the public boundary.
    _stage(3)
    capability, _ = examples.symbol_capability(
        request.route, request.provider_id, request.symbol
    )
    validation = validate_order_request(
        request, examples.account_snapshot(), capability
    )
    assert validation.data is not None
    validated = validation.data
    print("Validated:", validated.request_id)
    # Stage 4: Preserve upstream identifiers/approved size.
    _stage(4)
    print("Lineage:", validated.intent_id, validated.quantity)
    # Stage 5 — OUTPUT BOUNDARY: Return validated TradingRequest.
    _stage(5)
    print("Output:", type(validated).__name__)


if __name__ == "__main__":
    main()
