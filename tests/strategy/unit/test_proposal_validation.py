"""Fail-closed external proposal validation tests."""

from datetime import timedelta
from types import SimpleNamespace

import pytest
from app.services.strategy import (
    create_strategy_config,
    create_strategy_ref,
    get_strategy_environment,
    validate_strategy_proposal,
)
from app.utils import get_logger

from tests.strategy.unit.test_models import (
    COR,
    NOW,
    REQ,
    make_auth,
    make_config,
    make_context,
    make_market,
    make_policy,
    make_ref,
    make_signal_evidence,
)
from tests.strategy.unit.test_proposal_contracts import make_proposal_request

logger = get_logger(__name__)


def _dependencies() -> tuple[object, object, object, object, object, object]:
    """Build proposal validation dependencies."""
    ref = create_strategy_ref(
        strategy_id="mean-reversion",
        exact_version="1.0.0",
        environment=get_strategy_environment("RESEARCH"),
        request_id=REQ,
        correlation_id=COR,
    )
    config = create_strategy_config(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        config_schema_version="v1",
        parameters={"period": 5},
        request_id=REQ,
    )
    market = make_market((("1", "2", "0.5", "1.5"), ("1.5", "2", "1", "1.8")))
    evaluator = SimpleNamespace(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        module_path="approved.strategies.mean_reversion",
        source_hash="a" * 64,
        artifact_hash="a" * 64,
        dependency_hash="a" * 64,
    )
    auth = make_auth().model_copy(
        update={
            "permissions": ("strategy:evaluate_proposal",),
            "scopes": ("strategy:proposal_evaluation",),
        }
    )
    return (
        auth,
        ref,
        config,
        make_policy(),
        make_signal_evidence(market),
        evaluator,
    )


def test_validation_accepts_exact_authorized_dependencies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify exact receiver authority and registry evidence are accepted."""
    logger.debug("Testing accepted proposal validation")
    module = __import__(
        "app.services.strategy.proposal_intake.validation",
        fromlist=["validation"],
    )
    monkeypatch.setattr(
        module,
        "validate_strategy_ref",
        lambda _ref, _policy: make_ref(),
    )
    monkeypatch.setattr(
        module,
        "validate_strategy_config",
        lambda _ref, _config: make_config(),
    )
    monkeypatch.setattr(module, "unwrap_strategy_response", lambda value, **_: value)
    auth, ref, config, policy, evidence, evaluator = _dependencies()
    outcome = validate_strategy_proposal(
        make_proposal_request(),
        auth,
        ref,
        config,
        policy,
        evidence,
        make_context(),
        evaluator,
    )
    assert outcome.data is not None
    assert outcome.data.status == "accepted_for_evaluation"


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        ({"auth_permissions": ()}, "AUTHORIZATION_DENIED"),
        ({"auth_principal": "other"}, "AUTHORIZATION_CONTEXT_MISMATCH"),
        ({"context_workflow": "wf-other"}, "TRACE_CONTEXT_MISMATCH"),
        ({"instrument": "GBPUSD"}, "PROPOSAL_INSTRUMENT_MISMATCH"),
    ],
)
def test_validation_rejects_boundary_mismatches(
    change: dict[str, object],
    reason: str,
) -> None:
    """Verify authority, trace, and market mismatches fail closed."""
    logger.debug("Testing rejected proposal validation branch")
    auth, ref, config, policy, evidence, evaluator = _dependencies()
    if "auth_permissions" in change:
        auth = auth.model_copy(update={"permissions": change["auth_permissions"]})
    if "auth_principal" in change:
        auth = auth.model_copy(update={"principal_id": change["auth_principal"]})
    context = make_context()
    if "context_workflow" in change:
        context = context.model_copy(update={"workflow_id": change["context_workflow"]})
    request = make_proposal_request(
        instrument=change.get("instrument", "EURUSD"),
    )
    outcome = validate_strategy_proposal(
        request,
        auth,
        ref,
        config,
        policy,
        evidence,
        context,
        evaluator,
    )
    assert outcome.data is not None
    assert outcome.data.status == "rejected"
    assert outcome.data.reason_codes == (reason,)


def test_validation_reports_expired_without_registry_execution() -> None:
    """Verify the fixed Strategy clock expires stale proposals deterministically."""
    logger.debug("Testing expired proposal validation")
    auth, ref, config, policy, evidence, evaluator = _dependencies()
    request = make_proposal_request(
        requested_at=NOW - timedelta(hours=2),
        expires_at=NOW - timedelta(hours=1),
        horizon_seconds=7_200,
    )
    outcome = validate_strategy_proposal(
        request,
        auth,
        ref,
        config,
        policy,
        evidence,
        make_context(),
        evaluator,
    )
    assert outcome.data is not None
    assert outcome.data.status == "expired"
    assert outcome.data.reason_codes == ("PROPOSAL_EXPIRED",)
