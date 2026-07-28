"""WF-RISK-008: issue, validate, reserve, and consume one approval token."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from tests.risk.usage.workflows._support import examples, unwrap_risk_response

WORKFLOW_ID = "WF-RISK-008"
STAGES = (
    "Accept eligible decision, UI/API attestation, expected scope, config, and injected time.",
    "Issue a signed decision/config-bound Risk approval token.",
    "Validate schema, signature, scope, expiry, revocation, nonce, and attestation.",
    "Atomically reserve and consume the workflow/action scope with audit evidence.",
    "Return ApprovalValidationResult; replay remains blocked.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: Risk receives decision, attestation, and expected binding.
    _stage(1)
    service, store, decision, attestation = examples._values(live=True)
    print("Input decision:", decision.decision_id)
    # Stage 2: Issue through ApprovalTokenService.
    _stage(2)
    token = unwrap_risk_response(
        service.issue(decision, attestation, now=examples.NOW),
        operation="approval_tokens.issue",
    )
    print("Issued:", token.token_id)
    # Stage 3: Build exact expected binding.
    _stage(3)
    expected = examples._expected(token)
    print("Expected action:", expected["action"])
    # Stage 4: Validate, reserve, consume, and audit atomically.
    _stage(4)
    result = unwrap_risk_response(
        service.validate_reserve_and_consume(
            token, attestation, expected, now=examples.NOW
        ),
        operation="approval_tokens.validate_reserve_and_consume",
    )
    print("Consumed:", result.consumed, token.token_id in store.consumed)
    # Stage 5 — OUTPUT BOUNDARY: Return ApprovalValidationResult only.
    _stage(5)
    print("Output:", type(result).__name__, result.valid)


if __name__ == "__main__":
    main()
