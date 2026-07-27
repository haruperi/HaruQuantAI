"""WF-STR-008: register one immutable approved Strategy version."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.strategy import (
    StrategyConfig,
    StrategyEnvironment,
    StrategyParameterUpdateRequest,
    StrategyRef,
    register_strategy_version,
    update_strategy_parameters,
)
from tests.strategy.unit.test_catalog import make_registration
from tests.strategy.unit.test_models import COR, NOW, REQ, make_auth, make_policy
from tests.strategy.usage.workflows._support import temporary_storage

WORKFLOW_ID = "WF-STR-008"
STAGES = (
    "Accept an authenticated, externally reviewed registration command.",
    "Validate schema, module allowlist, hashes, lifecycle, environment, and uniqueness.",
    "Write immutable registry truth through injected Data persistence.",
    "Create parameter changes as new hash-addressed configuration records.",
    "Return StrategyMutationResult without storage objects or operational authority.",
)


def _stage(number: int) -> None:
    """Print one README-aligned workflow stage."""
    print(
        f"\n{'=' * 88}\nStage {number}/{len(STAGES)} — {STAGES[number - 1]}\n{'=' * 88}"
    )


def main() -> None:
    """Run the documented input-to-output workflow."""
    # Stage 1 — INPUT BOUNDARY: UI/API-approved immutable registration request.
    _stage(1)
    request, auth, policy = make_registration(), make_auth(), make_policy()
    print("Input:", request.strategy_id, request.strategy_version)

    # Stage 2: Public mutation validates all registration evidence.
    _stage(2)
    with temporary_storage():
        registration = register_strategy_version(request, auth, policy)
        print("Validation/mutation status:", registration.status)

        # Stage 3: Persistence returns direct immutable truth.
        _stage(3)
        mutation = registration.data
        print("Registry result:", mutation.status if mutation else registration.error)

        # Stage 4: Parameter updates create a new immutable record.
        _stage(4)
        if mutation is None or mutation.validated_ref is None:
            raise RuntimeError(f"Registration failed: {registration.error}")
        update_request = StrategyParameterUpdateRequest(
            command_id="workflow-config-update",
            strategy_id="mean-reversion",
            strategy_version="1.0.0",
            parameters={"period": 6},
            principal_id=auth.principal_id,
            reason="approved workflow demonstration",
            ref=StrategyRef(
                strategy_id="mean-reversion",
                exact_version="1.0.0",
                environment=StrategyEnvironment.RESEARCH,
                request_id=REQ,
                correlation_id=COR,
            ),
            config=StrategyConfig(
                strategy_id="mean-reversion",
                strategy_version="1.0.0",
                config_schema_version="v1",
                parameters={"period": 6},
                request_id=REQ,
            ),
            authorization_ref="workflow-approval",
            requested_at=NOW,
            request_id=REQ,
            correlation_id=COR,
        )
        update = update_strategy_parameters(update_request, auth)
        print("Parameter update:", update.status)

    # Stage 5 — OUTPUT BOUNDARY: Return typed mutation truth only.
    _stage(5)
    print("Output:", type(mutation).__name__, mutation.record_ref)


if __name__ == "__main__":
    main()
