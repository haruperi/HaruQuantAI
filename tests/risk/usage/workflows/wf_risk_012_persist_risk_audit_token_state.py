"""WF-RISK-012: persist Risk audit and approval-token state atomically."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from app.services.risk import issue_risk_approval_token, validate_risk_approval_token
from tests.risk.usage.workflows._support import examples, unwrap_risk_response

WORKFLOW_ID = "WF-RISK-012"
STAGES = (
    "Accept one material decision, kill-switch, audit, or token event.",
    "Canonicalize and hash-bind the event to the previous audit record.",
    "Persist issuance plus sealed audit evidence atomically through injected stores.",
    "Verify the chain and durable token state before exposing success.",
    "Return persisted Risk-owned truth or fail closed on partial/unavailable storage.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Material approval decision enters persistence boundary.
    _stage(1)
    service, store, decision, attestation = examples._values(live=True)
    print("Input decision:", decision.decision_id)
    # Stage 2: create_approval_token_service canonicalizes signed token/audit material.
    _stage(2)
    token = unwrap_risk_response(
        issue_risk_approval_token(
            service,
            decision,
            attestation,
            now=examples.NOW,
        ),
        operation="approval_tokens.issue",
    )
    print("Token hash/signature present:", bool(token.signature))
    # Stage 3: Issuance and audit state are durable before return.
    _stage(3)
    print("Persisted token:", token.token_id in store.tokens)
    # Stage 4: Validate and consume to prove durable state path.
    _stage(4)
    result = unwrap_risk_response(
        validate_risk_approval_token(
            service,
            token,
            attestation,
            examples._expected(token),
            now=examples.NOW,
        ),
        operation="approval_tokens.validate_reserve_and_consume",
    )
    print("Durable consumption:", result.consumed, token.token_id in store.consumed)
    # Stage 5 — OUTPUT BOUNDARY: Return persisted token/audit truth.
    _stage(5)
    print("Output:", type(token).__name__, type(result).__name__)


if __name__ == "__main__":
    main()
