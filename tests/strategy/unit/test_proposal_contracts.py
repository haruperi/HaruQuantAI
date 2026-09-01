"""External proposal contract and lineage tests."""

from datetime import timedelta

import pytest
from app.composition.logging import get_logger
from app.services.strategy import (
    bind_proposal_lineage,
    build_trade_intent,
    create_strategy_proposal_evaluation_request,
    create_strategy_proposal_evaluation_result,
)
from pydantic import ValidationError

from tests.strategy.unit.test_models import (
    COR,
    HASH,
    NOW,
    REQ,
    WF,
    make_context,
    make_decision,
)

logger = get_logger(__name__)


def make_proposal_request(**updates: object) -> object:
    """Build one valid receiver-owned proposal request."""
    values: dict[str, object] = {
        "principal_id": "builder",
        "source_proposal_id": "proposal-1",
        "source_task_id": "task-1",
        "source_content_hash": HASH,
        "strategy_id": "mean-reversion",
        "strategy_version": "1.0.0",
        "instrument": "EURUSD",
        "requested_direction": "BUY",
        "horizon_seconds": 3_600,
        "thesis_evidence_refs": ("evidence-thesis",),
        "invalidation_evidence_refs": ("evidence-invalidation",),
        "evaluation_scope": "TRADE_INTENT_IF_SUPPORTED",
        "requested_at": NOW - timedelta(minutes=5),
        "expires_at": NOW + timedelta(minutes=5),
        "request_id": REQ,
        "workflow_id": WF,
        "correlation_id": COR,
    }
    values.update(updates)
    return create_strategy_proposal_evaluation_request(**values)


def test_request_factory_derives_repeatable_content_identity() -> None:
    """Verify identical proposal material produces one stable identity."""
    logger.debug("Testing proposal request content identity")
    first = make_proposal_request()
    second = make_proposal_request()
    assert first == second
    assert first.evaluation_request_id == f"proposal-eval-{first.idempotency_key}"
    assert len(first.idempotency_key) == 64


def test_request_rejects_invalid_time_evidence_and_derived_fields() -> None:
    """Verify malformed requests fail before proposal evaluation."""
    logger.debug("Testing proposal request fail-closed contracts")
    with pytest.raises(ValueError, match="identities are derived"):
        make_proposal_request(evaluation_request_id="caller-selected")
    with pytest.raises(ValidationError):
        make_proposal_request(thesis_evidence_refs=())
    with pytest.raises(ValidationError):
        make_proposal_request(expires_at=NOW + timedelta(hours=2))


def test_result_contract_enforces_status_payload_consistency() -> None:
    """Verify rejected and accepted result shapes cannot be confused."""
    logger.debug("Testing proposal result status invariants")
    request = make_proposal_request()
    with pytest.raises(ValidationError):
        create_strategy_proposal_evaluation_result(
            evaluation_id="proposal-result-1",
            evaluation_request_id=request.evaluation_request_id,
            status="rejected",
            source_proposal_id=request.source_proposal_id,
            source_task_id=request.source_task_id,
            source_content_hash=request.source_content_hash,
            strategy_id=request.strategy_id,
            strategy_version=request.strategy_version,
            request_id=request.request_id,
            correlation_id=request.correlation_id,
        )


def test_lineage_binding_changes_only_lineage() -> None:
    """Verify external identity cannot alter canonical intent fields."""
    logger.debug("Testing proposal lineage-only binding")
    request = make_proposal_request()
    intent = build_trade_intent(make_decision(), make_context(), 0).data
    assert intent is not None
    outcome = bind_proposal_lineage(intent, request)
    assert outcome.data is not None
    bound = outcome.data
    assert bound.model_copy(update={"lineage": intent.lineage}) == intent
    assert bound.lineage["source_proposal_id"] == request.source_proposal_id
    assert bound.lineage["source_content_hash"] == request.source_content_hash
