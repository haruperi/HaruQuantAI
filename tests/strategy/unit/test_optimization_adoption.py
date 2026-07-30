"""Strategy-owned Optimization handoff receiver tests."""

import importlib

import pytest
from app.services.strategy import (
    adopt_approved_optimization_parameters,
    create_strategy_config,
    create_strategy_mutation_result,
    create_strategy_parameter_update_request,
    create_strategy_ref,
    get_strategy_environment,
)
from app.utils import canonical_digest, get_logger

from tests.strategy.unit.test_models import COR, NOW, REQ, WF, make_auth

logger = get_logger(__name__)


def make_optimization_update() -> object:
    """Build one governed Strategy update bound to Optimization evidence."""
    parameters = {"period": 7}
    return create_strategy_parameter_update_request(
        command_id="command-optimization-1",
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        parameters=parameters,
        optimization_result_ref="search-1",
        principal_id="builder",
        reason="owner approved ranked candidate",
        ref=create_strategy_ref(
            strategy_id="mean-reversion",
            exact_version="1.0.0",
            environment=get_strategy_environment("RESEARCH"),
            request_id=REQ,
            correlation_id=COR,
        ),
        config=create_strategy_config(
            strategy_id="mean-reversion",
            strategy_version="1.0.0",
            config_schema_version="v1",
            parameters=parameters,
            request_id=REQ,
        ),
        authorization_ref="approval-optimization",
        requested_at=NOW,
        request_id=REQ,
        correlation_id=COR,
    )


def make_optimization_handoff(**updates: object) -> dict[str, object]:
    """Build a structurally compatible OptimizationResult v1 projection."""
    handoff: dict[str, object] = {
        "contract_version": "v1",
        "schema_id": "optimization.result.v1",
        "search_id": "search-1",
        "final_decision": "ready_for_risk_review",
        "reproducibility_hash": canonical_digest({"search_id": "search-1"}),
        "ranked_candidates": ({"executable_parameters": {"period": 7}},),
    }
    handoff.update(updates)
    return handoff


def _auth() -> object:
    """Build explicit adoption authority."""
    return make_auth().model_copy(update={"scopes": ("approval-optimization",)})


def test_approved_candidate_delegates_to_immutable_update(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify a compatible approved candidate reaches the existing mutation path."""
    logger.debug("Testing approved Optimization candidate adoption")
    module = importlib.import_module("app.services.strategy.registry.optimization")
    accepted = create_strategy_mutation_result(
        mutation_id="mutation-optimization-1",
        mutation_type="UPDATE_PARAMETERS",
        status="ACCEPTED",
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        validated_config=__import__(
            "tests.strategy.unit.test_models",
            fromlist=["make_config"],
        ).make_config(),
        request_id=REQ,
        correlation_id=COR,
        workflow_id=WF,
        completed_at=NOW,
    )
    monkeypatch.setattr(
        module,
        "update_strategy_parameters",
        lambda *_args: accepted,
    )
    monkeypatch.setattr(module, "unwrap_strategy_response", lambda value, **_: value)
    outcome = adopt_approved_optimization_parameters(
        make_optimization_update(),
        _auth(),
        make_optimization_handoff(),
    )
    assert outcome.data == accepted


@pytest.mark.parametrize(
    ("handoff", "reason"),
    [
        (None, "OPTIMIZATION_HANDOFF_UNAVAILABLE"),
        (
            make_optimization_handoff(schema_id="optimization.future.v2"),
            "OPTIMIZATION_HANDOFF_MISMATCH",
        ),
        (
            make_optimization_handoff(reproducibility_hash="not-a-hash"),
            "OPTIMIZATION_EVIDENCE_INVALID",
        ),
        (
            make_optimization_handoff(
                ranked_candidates=({"executable_parameters": {"period": 99}},)
            ),
            "OPTIMIZATION_CANDIDATE_MISMATCH",
        ),
    ],
)
def test_handoff_rejections_never_delegate(
    monkeypatch: pytest.MonkeyPatch,
    handoff: object | None,
    reason: str,
) -> None:
    """Verify unavailable or incompatible upstream evidence fails closed."""
    logger.debug("Testing Optimization handoff rejection")
    module = importlib.import_module("app.services.strategy.registry.optimization")
    monkeypatch.setattr(
        module,
        "update_strategy_parameters",
        lambda *_args: pytest.fail("rejected handoff reached mutation"),
    )
    outcome = adopt_approved_optimization_parameters(
        make_optimization_update(),
        _auth(),
        handoff,
    )
    assert outcome.data is not None
    assert outcome.data.status == "REJECTED"
    assert outcome.data.reason_codes == (reason,)


def test_adoption_requires_owner_permission_and_approval_scope() -> None:
    """Verify a producer result cannot self-authorize Strategy mutation."""
    logger.debug("Testing Optimization adoption authority")
    outcome = adopt_approved_optimization_parameters(
        make_optimization_update(),
        make_auth(),
        make_optimization_handoff(),
    )
    assert outcome.data is not None
    assert outcome.data.reason_codes == ("AUTHORIZATION_DENIED",)


def test_adoption_requires_request_optimization_reference() -> None:
    """Verify a handoff cannot be adopted without request-side source binding."""
    logger.debug("Testing required Optimization result reference")
    request = make_optimization_update().model_copy(
        update={"optimization_result_ref": None}
    )
    outcome = adopt_approved_optimization_parameters(
        request,
        _auth(),
        make_optimization_handoff(),
    )
    assert outcome.data is not None
    assert outcome.data.reason_codes == ("OPTIMIZATION_REFERENCE_REQUIRED",)


def test_adoption_accepts_structural_model_dump(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify producer models cross the boundary through their wire projection."""
    logger.debug("Testing Optimization model projection")
    module = importlib.import_module("app.services.strategy.registry.optimization")
    accepted = create_strategy_mutation_result(
        mutation_id="mutation-optimization-model",
        mutation_type="UPDATE_PARAMETERS",
        status="ACCEPTED",
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        validated_config=__import__(
            "tests.strategy.unit.test_models",
            fromlist=["make_config"],
        ).make_config(),
        request_id=REQ,
        correlation_id=COR,
        workflow_id=WF,
        completed_at=NOW,
    )

    class _ProducerModel:
        """Minimal producer model exposing its documented wire projection."""

        def model_dump(self, *, mode: str) -> dict[str, object]:
            """Return a detached handoff projection."""
            assert mode == "python"
            return make_optimization_handoff()

    monkeypatch.setattr(
        module,
        "update_strategy_parameters",
        lambda *_args: accepted,
    )
    monkeypatch.setattr(module, "unwrap_strategy_response", lambda value, **_: value)
    outcome = adopt_approved_optimization_parameters(
        make_optimization_update(),
        _auth(),
        _ProducerModel(),
    )
    assert outcome.data == accepted


@pytest.mark.parametrize(
    "handoff",
    [
        object(),
        make_optimization_handoff(ranked_candidates="not-a-sequence"),
        make_optimization_handoff(
            ranked_candidates=(
                "not-a-candidate",
                {"candidate_id": "missing-parameters"},
            )
        ),
    ],
)
def test_structurally_invalid_handoffs_are_rejected(handoff: object) -> None:
    """Verify invalid objects and candidate collections fail closed."""
    logger.debug("Testing invalid Optimization structural projection")
    outcome = adopt_approved_optimization_parameters(
        make_optimization_update(),
        _auth(),
        handoff,
    )
    assert outcome.data is not None
    assert outcome.data.status == "REJECTED"
