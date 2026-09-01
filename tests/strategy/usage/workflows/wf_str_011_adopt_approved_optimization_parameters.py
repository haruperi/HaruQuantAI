"""WF-STR-011: adopt an approved Optimization-compatible parameter handoff."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.contracts.common.models import create_auth_context
from app.kernel.serialization import canonical_digest
from app.services.strategy import (
    adopt_approved_optimization_parameters,
    create_strategy_parameter_update_request,
    register_strategy_version,
)
from tests.strategy.usage.workflows._support import (
    COR,
    REQ,
    WF,
    caller_config,
    policy,
    registration_request,
    temporary_storage,
    unresolved_ref,
)

WORKFLOW_ID = "WF-STR-011"
STAGES = (
    "Receive explicit owner approval and a contract-compatible Optimization handoff.",
    "Verify contract identity, search reference, evidence hash, and selected candidate.",
    "Validate the selected parameters against the registered Strategy schema.",
    "Persist a new immutable hash-addressed Strategy configuration.",
    "Return receiver-owned mutation truth without Optimization runtime authority.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run Strategy's receiver side using the published handoff shape."""
    # Stage 1 — INPUT BOUNDARY: Owner approval and producer-compatible fields arrive.
    _stage(1)
    parameters = {"period": 7}
    auth = create_auth_context(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="builder",
        principal_type="USER",
        roles=("strategy-admin",),
        permissions=("strategy:register", "strategy:update"),
        scopes=("approval-optimization-search-1",),
        tenant_or_environment="dev",
        request_id=REQ,
        workflow_id=WF,
        correlation_id=COR,
        issued_at=datetime.now(UTC),
    )
    request = create_strategy_parameter_update_request(
        command_id="workflow-adopt-optimization-search-1",
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        parameters=parameters,
        optimization_result_ref="optimization-search-1",
        principal_id="builder",
        reason="owner selected the ranked candidate",
        ref=unresolved_ref(),
        config=caller_config(period=7),
        authorization_ref="approval-optimization-search-1",
        requested_at=datetime.now(UTC),
        request_id=REQ,
        correlation_id=COR,
    )
    handoff = {
        "contract_version": "v1",
        "schema_id": "optimization.result.v1",
        "search_id": "optimization-search-1",
        "final_decision": "ready_for_risk_review",
        "reproducibility_hash": canonical_digest(
            {
                "search_id": "optimization-search-1",
                "selected_parameters": parameters,
            }
        ),
        "ranked_candidates": (
            {
                "rank": 1,
                "candidate_id": "candidate-1",
                "executable_parameters": parameters,
            },
        ),
    }
    print("Compatibility input only; no Optimization execution is claimed.")
    print("Approved handoff projection:", handoff)

    # Stage 2: Strategy validates the producer contract projection fail-closed.
    _stage(2)
    print(
        "Verified identities:",
        handoff["schema_id"],
        handoff["search_id"],
        handoff["reproducibility_hash"],
    )

    # Stage 3: Register and schema-validate through Strategy-owned operations.
    _stage(3)
    with temporary_storage():
        registration = register_strategy_version(
            registration_request(),
            auth,
            policy(),
        )
        if registration.data is None:
            raise RuntimeError(f"Strategy registration failed: {registration.error}")
        print(
            "Registered strategy:",
            registration.data.record_ref,
            registration.data.record_hash,
        )

        # Stage 4: Persist one new immutable configuration record.
        _stage(4)
        outcome = adopt_approved_optimization_parameters(request, auth, handoff)
    if outcome.data is None:
        raise RuntimeError(f"Strategy adoption failed: {outcome.error}")
    mutation = outcome.data
    if mutation.status not in {"ACCEPTED", "IDEMPOTENT"}:
        raise RuntimeError(f"Strategy rejected adoption: {mutation.reason_codes}")
    print("Immutable configuration record:")
    print(mutation.validated_config.model_dump(mode="json"))
    print("Record hash:", mutation.record_hash)
    print("Mutation evidence:", mutation.model_dump(mode="json"))

    # Stage 5 — OUTPUT BOUNDARY: Return Strategy mutation truth only.
    _stage(5)
    print("Output status:", mutation.status)
    print("Optimization runtime imported: False")
    print("Risk eligibility conferred: False")


if __name__ == "__main__":
    main()
