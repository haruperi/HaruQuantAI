"""Integration evidence for `WF-AGT-008` — submit trade proposal.

Exercises the path a proposal must traverse: mandate and roster validation, a
supported thesis composed into a non-executable proposal, mapping onto
Strategy's **own** `StrategyProposalEvaluationRequest` through the receiver's
own factory, and a receipt that says no more than the receiver said.

The receiver contract is real throughout. `create_strategy_proposal_evaluation_request`
derives the request identity and idempotency key from a content digest and
refuses a caller that supplies either, and `StrategyProposalEvaluationRequest`
itself rejects an expiry beyond the declared horizon — so "no privileged route"
is demonstrated with Strategy's code rather than a stand-in.

What is **not** exercised: no signal has been evaluated and no intent produced.
`evaluate_strategy_proposal` needs a hash-bound `SignalEvaluator`, a strategy
config, point-in-time indicators, and an execution context — a full Strategy
composition that belongs to a composition root. The intake here is a
deterministic double, and the final test asserts that boundary rather than
papering over it.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from app.agentic import (
    build_agent_task,
    build_model_profile,
    get_role_registry,
    resolve_role_manifest,
    validate_firm_mandate,
)
from app.agentic.agents.strategy_desk.trader import (
    TradeProposal,
    submit_trade_proposal,
)
from app.agentic.agents.strategy_desk.trader.agent import propose_trade
from app.agentic.agents.strategy_desk.trader.handoff import build_evaluation_request
from app.agentic.agents.strategy_desk.trader.schemas import forbidden_fields
from app.agentic.runtime import ModelOutcome
from app.services.strategy import create_strategy_proposal_evaluation_request
from app.utils import derive_stable_id, generate_id
from pydantic import ValidationError

from tests.agentic.fixtures import (
    NOW,
    PROPOSAL_EVIDENCE_REFS,
    PROPOSAL_INSTRUMENT,
    PROPOSAL_STRATEGY_ID,
    PROPOSAL_STRATEGY_VERSION,
    TRADER_ROLE_ID,
    build_proposable_thesis,
    build_trader_mandate,
    build_trader_role_manifest,
    receiver_result,
    trader_model_output,
)

TASK_ID = derive_stable_id("id", "task-trade-proposal-council")
SCOPE = {"environment": "sandbox", "asset_class": "fx"}
HORIZON = 4 * 60 * 60
PRINCIPAL = "operator-owner"


class _Runtime:
    """Deterministic runtime returning declared structured output."""

    def __init__(self, output=None) -> None:
        self.output = output or trader_model_output()
        self.nodes: list[str] = []

    def execute_node(self, node_id, profile, invocation):
        self.nodes.append(node_id)
        return ModelOutcome.model_validate(
            {
                "invocation_id": invocation.invocation_id,
                "status": "ok",
                "output": self.output,
                "reasons": (),
                "provider": profile.provider,
                "model_identifier": profile.model_identifier,
                "tokens_used": 820,
                "latency_ms": 105,
                "cost": Decimal("0.04"),
            },
        )


class _Intake:
    """Deterministic stand-in for the receiver-owned proposal intake.

    It validates nothing itself. What it demonstrates is that the request it
    receives is the receiver's own contract, already validated by the
    receiver's own factory before it ever arrives.
    """

    def __init__(self, result=None) -> None:
        self.result = receiver_result() if result is None else result
        self.requests: list[object] = []

    def submit(self, request):
        self.requests.append(request)
        return {
            "source_proposal_id": request.source_proposal_id,
            "source_content_hash": request.source_content_hash,
            **self.result,
        }


def _profile():
    return build_model_profile(
        {
            "profile_id": "profile-market-analysis-a",
            "version": "1.0.0",
            "provider": "gemini",
            "model_identifier": "gemini-3.0-pro-002",
            "region": "europe-west4",
            "credential_ref": "vault://agentic/gemini",
            "structured_output_mode": "json_schema",
            "max_context_tokens": 120_000,
            "max_output_tokens": 8_000,
            "max_latency_ms": 30_000,
            "max_cost_per_call": Decimal("0.50"),
            "retention_policy": "zero-retention",
            "training_use_permitted": False,
            "fallback_profile_id": None,
            "evaluation_state": "evaluated",
            "enabled": True,
        },
    )


def _task():
    return build_agent_task(
        {
            "created_at": NOW,
            "request_id": generate_id("req"),
            "workflow_id": generate_id("wf"),
            "correlation_id": generate_id("cor"),
            "causation_id": None,
            "task_id": TASK_ID,
            "workflow_name": "submit_trade_proposal",
            "workflow_version": "1.0.0",
            "objective": "Turn the overlap thesis into an evaluable proposal.",
            "input_refs": PROPOSAL_EVIDENCE_REFS,
            "principal_id": PRINCIPAL,
            "scope": dict(SCOPE),
            "deadline_at": NOW + timedelta(minutes=45),
            "idempotency_key": "idem-trade-proposal",
            "budgets": {"cost": Decimal("2.00")},
        },
    )


def _compose(**overrides: object) -> TradeProposal:
    data: dict[str, object] = {
        "registry": get_role_registry(
            build_trader_mandate(),
            (build_trader_role_manifest(),),
            NOW,
        ),
        "task": _task(),
        "runtime": _Runtime(),
        "profile": _profile(),
        "thesis": build_proposable_thesis(),
        "strategy_id": PROPOSAL_STRATEGY_ID,
        "strategy_version": PROPOSAL_STRATEGY_VERSION,
        "instrument": PROPOSAL_INSTRUMENT,
        "direction": "BUY",
        "horizon_seconds": HORIZON,
        "evaluation_scope": "SIGNAL_ONLY",
        "at_time": NOW,
    }
    data.update(overrides)
    payload = propose_trade(**data).payload
    assert payload is not None
    return payload


def test_a_proposal_traverses_the_full_governed_path() -> None:
    # 1. Mandate and roster validate, and the prompt hash chain holds.
    mandate = build_trader_mandate()
    assert validate_firm_mandate(mandate, NOW) is mandate
    registry = get_role_registry(mandate, (build_trader_role_manifest(),), NOW)
    manifest = resolve_role_manifest(registry, TRADER_ROLE_ID)
    # The trader registers no tool: it reads nothing through the tool path.
    assert manifest.tools == ()

    # 2. A supported thesis becomes a proposal carrying nothing executable.
    runtime = _Runtime()
    proposal = _compose(registry=registry, runtime=runtime)
    assert runtime.nodes == ["propose_trade"]
    assert forbidden_fields(TradeProposal) == ()
    assert proposal.evidence_refs == PROPOSAL_EVIDENCE_REFS

    # 3. The receiver's own factory builds the request Strategy will evaluate.
    port = _Intake()
    receipt = submit_trade_proposal(
        proposal,
        port,
        PRINCIPAL,
        generate_id("req"),
        generate_id("wf"),
        generate_id("cor"),
        at_time=NOW,
    )
    (submitted,) = port.requests
    assert submitted.schema_id == "strategy.proposal_evaluation_request.v1"
    assert submitted.source_content_hash == proposal.content_hash
    assert submitted.evaluation_request_id.startswith("proposal-eval-")

    # 4. The receipt says what the receiver said, and no more.
    assert receipt.status == "accepted_for_evaluation"
    assert receipt.intent_produced is False
    assert receipt.proposal_content_hash == proposal.content_hash


def test_the_receiver_derives_the_request_identity_itself() -> None:
    # Supplying either derived identity is refused by Strategy, so a proposal
    # cannot arrive pre-stamped with an identity it chose for itself.
    with pytest.raises(ValueError, match="identities are derived"):
        create_strategy_proposal_evaluation_request(
            evaluation_request_id="proposal-eval-forged",
        )
    with pytest.raises(ValueError, match="identities are derived"):
        create_strategy_proposal_evaluation_request(idempotency_key="a" * 64)


def test_the_receiver_rejects_an_expiry_beyond_the_declared_horizon() -> None:
    proposal = _compose(horizon_seconds=600, validity_seconds=600)
    lineage = (PRINCIPAL, generate_id("req"), generate_id("wf"), generate_id("cor"))
    # The proposal contract already refuses this, so reaching the receiver with
    # one requires bypassing the contract; the receiver refuses it too.
    with pytest.raises(ValidationError, match="expiry exceeds its declared horizon"):
        create_strategy_proposal_evaluation_request(
            principal_id=lineage[0],
            source_proposal_id=proposal.proposal_id,
            source_task_id=proposal.task_id,
            source_content_hash=proposal.content_hash,
            strategy_id=proposal.strategy_id,
            strategy_version=proposal.strategy_version,
            instrument=proposal.instrument,
            requested_direction=proposal.direction,
            horizon_seconds=600,
            thesis_evidence_refs=proposal.evidence_refs,
            invalidation_evidence_refs=proposal.invalidation,
            evaluation_scope=proposal.evaluation_scope,
            requested_at=NOW,
            expires_at=NOW + timedelta(seconds=601),
            request_id=lineage[1],
            workflow_id=lineage[2],
            correlation_id=lineage[3],
        )


def test_the_receiver_rejects_duplicated_evidence_references() -> None:
    proposal = _compose()
    with pytest.raises(ValidationError, match="non-empty and unique"):
        create_strategy_proposal_evaluation_request(
            principal_id=PRINCIPAL,
            source_proposal_id=proposal.proposal_id,
            source_task_id=proposal.task_id,
            source_content_hash=proposal.content_hash,
            strategy_id=proposal.strategy_id,
            strategy_version=proposal.strategy_version,
            instrument=proposal.instrument,
            requested_direction=proposal.direction,
            horizon_seconds=proposal.horizon_seconds,
            thesis_evidence_refs=(PROPOSAL_EVIDENCE_REFS[0], PROPOSAL_EVIDENCE_REFS[0]),
            invalidation_evidence_refs=proposal.invalidation,
            evaluation_scope=proposal.evaluation_scope,
            requested_at=NOW,
            expires_at=NOW + timedelta(seconds=proposal.horizon_seconds),
            request_id=generate_id("req"),
            workflow_id=generate_id("wf"),
            correlation_id=generate_id("cor"),
        )


def test_the_mapped_request_carries_no_broker_native_field() -> None:
    proposal = _compose()
    request = build_evaluation_request(
        proposal,
        PRINCIPAL,
        generate_id("req"),
        generate_id("wf"),
        generate_id("cor"),
    )
    # Strategy's own intake contract has no place to put one, which is what
    # makes "no broker-native fields" a property of the boundary and not a
    # promise Agentic makes about itself.
    for field in ("price", "quantity", "lot_size", "order_type", "venue", "account"):
        assert field not in type(request).model_fields


@pytest.mark.parametrize("status", ["rejected", "expired", "no_signal"])
def test_an_unfavourable_outcome_is_the_outcome(status) -> None:
    proposal = _compose()
    port = _Intake(receiver_result(status=status, signals_evaluated=0))
    receipt = submit_trade_proposal(
        proposal,
        port,
        PRINCIPAL,
        generate_id("req"),
        generate_id("wf"),
        generate_id("cor"),
        at_time=NOW,
    )
    assert receipt.status == status
    assert receipt.intent_produced is False


def test_the_proposal_stops_at_the_receiver_boundary() -> None:
    # `WF-AGT-008` steps 3 and 4 belong to Risk and Trading. Nothing in this
    # package reaches them, and no signal has been evaluated here: the intake
    # above is a double, because `evaluate_strategy_proposal` needs a full
    # Strategy composition that a composition root owns.
    from pathlib import Path

    package = Path("app/agentic/agents/strategy_desk/trader")
    sources = "".join(path.read_text(encoding="utf-8") for path in package.glob("*.py"))
    for forbidden in (
        "app.services.risk",
        "app.services.trading",
        "app.services.brokers",
        "dispatch_order_intent",
        "evaluate_live_gate",
    ):
        assert forbidden not in sources

    # Exactly one receiver operation is imported, and it only builds a request.
    imports = [
        line.strip()
        for line in sources.splitlines()
        if line.startswith("from app.services")
    ]
    assert imports == [
        "from app.services.strategy import create_strategy_proposal_evaluation_request",
    ]
