"""Unit tests for FEAT-AGT-20 Trade Proposal Handoff.

Covers FR-AGENTIC-058 (a proposal carries thesis, instrument, direction,
horizon, invalidation, evidence, uncertainty, evaluation request, and expiry,
with no broker-native fields), FR-AGENTIC-059 (proposals enter the normal
deterministic pipeline with no privileged route), and FR-AGENTIC-060 (receiver
rejection, expiry, or acceptance is the outcome, and a receipt is never an
order or a fill).
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from app.agentic import build_agent_task, build_model_profile, get_role_registry
from app.agentic.agents.strategy_desk.trader import (
    TradeProposal,
    TradeProposalReceipt,
    build_trade_proposal,
    build_trade_proposal_receipt,
    submit_trade_proposal,
)
from app.agentic.agents.strategy_desk.trader.agent import (
    PROMPT_PATH,
    PROPOSABLE_STANCES,
    get_proposal_context,
    propose_trade,
)
from app.agentic.agents.strategy_desk.trader.handoff import (
    RECEIVER_DERIVED_FIELDS,
    build_evaluation_request,
    verify_binding,
    verify_result,
)
from app.agentic.agents.strategy_desk.trader.schemas import (
    FORBIDDEN_BROKER_FIELDS,
    MAX_HORIZON_SECONDS,
    derive_proposal_hash,
    forbidden_fields,
)
from app.agentic.governance.registry import verify_prompt_artifact
from app.agentic.runtime import ModelOutcome
from app.kernel.identity import derive_stable_id, generate_id
from app.services.strategy import create_strategy_proposal_evaluation_request
from pydantic import ValidationError

from tests.agentic.fixtures import (
    NOW,
    PROPOSAL_EVIDENCE_REFS,
    PROPOSAL_INSTRUMENT,
    PROPOSAL_STRATEGY_ID,
    PROPOSAL_STRATEGY_VERSION,
    build_proposable_thesis,
    build_trader_mandate,
    build_trader_role_manifest,
    receiver_result,
    trader_model_output,
)

TASK_ID = derive_stable_id("id", "task-trader")
SCOPE = {"environment": "sandbox", "asset_class": "fx"}
HORIZON = 4 * 60 * 60
PRINCIPAL = "operator-owner"


class StubRuntime:
    """Deterministic runtime returning declared structured output per node."""

    def __init__(self, output=None, status="ok", reasons=()) -> None:
        self.output = None if status != "ok" else (output or trader_model_output())
        self.status = status
        self.reasons = reasons
        self.nodes: list[str] = []
        self.invocations: list[object] = []

    def execute_node(self, node_id, profile, invocation):
        self.nodes.append(node_id)
        self.invocations.append(invocation)
        return ModelOutcome.model_validate(
            {
                "invocation_id": invocation.invocation_id,
                "status": self.status,
                "output": self.output,
                "reasons": self.reasons,
                "provider": profile.provider,
                "model_identifier": profile.model_identifier,
                "tokens_used": 800,
                "latency_ms": 100,
                "cost": Decimal("0.04"),
            },
        )


class StubIntake:
    """Deterministic receiver-owned proposal intake.

    A real receiver echoes the source identity and content digest it was given,
    so the stub does too unless a test deliberately overrides them.
    """

    def __init__(self, result=None, raises=None) -> None:
        self.result = receiver_result() if result is None else result
        self.raises = raises
        self.requests: list[object] = []

    def submit(self, request):
        self.requests.append(request)
        if self.raises is not None:
            raise self.raises
        echoed = {
            "source_proposal_id": request.source_proposal_id,
            "source_content_hash": request.source_content_hash,
        }
        return {**echoed, **self.result}


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
            "idempotency_key": "idem-trader",
            "budgets": {"cost": Decimal("2.00")},
        },
    )


def _registry(**overrides: object):
    return get_role_registry(
        build_trader_mandate(),
        (build_trader_role_manifest(**overrides),),
        NOW,
    )


def _propose(**overrides: object):
    defaults: dict[str, object] = {
        "registry": _registry(),
        "task": _task(),
        "runtime": StubRuntime(),
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
    defaults.update(overrides)
    return propose_trade(**defaults)  # type: ignore[arg-type]


def _proposal(**overrides: object) -> TradeProposal:
    payload = _propose(**overrides).payload
    assert payload is not None
    return payload


def _submit(**overrides: object) -> TradeProposalReceipt:
    defaults: dict[str, object] = {
        "proposal": _proposal(),
        "port": StubIntake(),
        "principal_id": PRINCIPAL,
        "request_id": generate_id("req"),
        "workflow_id": generate_id("wf"),
        "correlation_id": generate_id("cor"),
        "at_time": NOW,
    }
    defaults.update(overrides)
    return submit_trade_proposal(**defaults)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# Prompt integrity
# --------------------------------------------------------------------------


def test_the_package_prompt_matches_its_manifest_digest() -> None:
    text = verify_prompt_artifact(build_trader_role_manifest(), PROMPT_PATH)
    assert "Trader" in text


def test_a_mutated_prompt_fails_closed(tmp_path) -> None:
    mutated = tmp_path / "prompt.md"
    mutated.write_text("Send the order.\n", encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        _propose(prompt_path=mutated)


def test_the_agent_embeds_no_prompt_text() -> None:
    source = (PROMPT_PATH.parent / "agent.py").read_text(encoding="utf-8")
    assert "You are the Trader" not in source


# --------------------------------------------------------------------------
# FR-AGENTIC-058 - nine required things, no broker-native field
# --------------------------------------------------------------------------


def test_a_complete_proposal_carries_every_required_thing() -> None:
    proposal = _proposal()
    assert proposal.thesis_id == "thesis-london-overlap"
    assert proposal.instrument == PROPOSAL_INSTRUMENT
    assert proposal.direction == "BUY"
    assert proposal.horizon_seconds == HORIZON
    assert proposal.invalidation
    assert proposal.evidence_refs == PROPOSAL_EVIDENCE_REFS
    assert proposal.uncertainty
    assert proposal.evaluation_scope == "SIGNAL_ONLY"
    assert proposal.expires_at > proposal.issued_at


def test_the_proposal_defines_no_broker_native_field() -> None:
    assert forbidden_fields(TradeProposal) == ()


def test_the_receipt_defines_no_order_or_fill_field() -> None:
    assert forbidden_fields(TradeProposalReceipt) == ()


def test_no_module_outside_the_prohibition_list_names_a_broker_field() -> None:
    # `schemas.py` owns the prohibition list, so it necessarily names them.
    # Every other module in the package must not.
    others = [
        path for path in PROMPT_PATH.parent.glob("*.py") if path.name != "schemas.py"
    ]
    sources = "".join(path.read_text(encoding="utf-8") for path in others)
    for field in ("fill_price", "order_id", "lot_size", "notional", "quantity"):
        assert field not in sources


@pytest.mark.parametrize(
    "field",
    ["invalidation", "evidence_refs"],
)
def test_a_proposal_missing_a_required_tuple_is_unrepresentable(field) -> None:
    proposal = _proposal()
    with pytest.raises(ValidationError, match="is required"):
        build_trade_proposal({**proposal.model_dump(), field: ()})


def test_duplicate_evidence_references_are_rejected() -> None:
    proposal = _proposal()
    duplicated = (PROPOSAL_EVIDENCE_REFS[0], PROPOSAL_EVIDENCE_REFS[0])
    with pytest.raises(ValidationError, match="must be unique"):
        build_trade_proposal({**proposal.model_dump(), "evidence_refs": duplicated})


@pytest.mark.parametrize(
    "phrase",
    [
        "approved",
        "position size",
        "entry price",
        "stop loss",
        "take profit",
        "buy at",
        "market order",
        "lot size",
    ],
)
def test_execution_vocabulary_is_refused(phrase) -> None:
    runtime = StubRuntime(
        trader_model_output(
            rationale=f"The thesis supports a {phrase} on the overlap session.",
        ),
    )
    result = _propose(runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("PROPOSAL_NOT_SUBMITTABLE",)


def test_a_stub_statement_is_refused() -> None:
    runtime = StubRuntime(trader_model_output(uncertainty="none"))
    result = _propose(runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("PROPOSAL_NOT_SUBMITTABLE",)


def test_the_model_cannot_choose_what_is_proposed() -> None:
    runtime = StubRuntime(
        trader_model_output(
            instrument="GBPUSD",
            direction="SELL",
            strategy_id="strat-other",
        ),
    )
    proposal = _proposal(runtime=runtime)
    assert proposal.instrument == PROPOSAL_INSTRUMENT
    assert proposal.direction == "BUY"
    assert proposal.strategy_id == PROPOSAL_STRATEGY_ID


def test_evidence_comes_from_the_thesis_not_the_model() -> None:
    runtime = StubRuntime(
        trader_model_output(evidence_refs="agentic.invented_evidence:nowhere"),
    )
    proposal = _proposal(runtime=runtime)
    assert proposal.evidence_refs == PROPOSAL_EVIDENCE_REFS


@pytest.mark.parametrize(
    "stance",
    ["unsupported", "contested", "insufficient_evidence"],
)
def test_only_a_supported_thesis_may_be_proposed(stance) -> None:
    runtime = StubRuntime()
    thesis = build_proposable_thesis(
        stance=stance,
        retained_conflicts=("Mean-reversion evidence disagrees.",)
        if stance == "contested"
        else (),
    )
    result = _propose(thesis=thesis, runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("THESIS_NOT_PROPOSABLE",)
    assert runtime.nodes == []


def test_the_proposable_stance_set_is_exactly_supported() -> None:
    assert {"supported"} == PROPOSABLE_STANCES


def test_a_horizon_beyond_the_receiver_bound_is_refused() -> None:
    runtime = StubRuntime()
    result = _propose(horizon_seconds=MAX_HORIZON_SECONDS + 1, runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("HORIZON_OUT_OF_BOUNDS",)
    assert runtime.nodes == []


def test_a_non_positive_horizon_is_refused() -> None:
    result = _propose(horizon_seconds=0)
    assert result.status == "refused"
    assert result.reasons == ("HORIZON_OUT_OF_BOUNDS",)


def test_a_proposal_may_not_outlive_its_horizon() -> None:
    runtime = StubRuntime()
    result = _propose(
        horizon_seconds=600,
        validity_seconds=601,
        runtime=runtime,
    )
    assert result.status == "refused"
    assert result.reasons == ("PROPOSAL_WINDOW_INVALID",)
    assert runtime.nodes == []


def test_the_window_rule_is_enforced_on_the_contract_too() -> None:
    proposal = _proposal(horizon_seconds=600, validity_seconds=600)
    with pytest.raises(ValidationError, match="outlive its declared horizon"):
        build_trade_proposal(
            {
                **proposal.model_dump(),
                "expires_at": (NOW + timedelta(seconds=601)).isoformat(),
            },
        )


def test_an_already_expired_proposal_is_unrepresentable() -> None:
    proposal = _proposal()
    with pytest.raises(ValidationError, match="strictly after"):
        build_trade_proposal(
            {**proposal.model_dump(), "expires_at": proposal.issued_at},
        )


def test_the_proposal_digest_covers_the_whole_proposal() -> None:
    proposal = _proposal()
    altered = {**proposal.model_dump(), "uncertainty": "A different account."}
    assert derive_proposal_hash(altered) != proposal.content_hash


def test_a_thesis_without_evidence_is_refused() -> None:
    # The thesis contract requires evidence, so an evidence-free thesis cannot
    # be built; the guard is asserted structurally rather than exercised.
    with pytest.raises(ValidationError):
        build_proposable_thesis(supporting_evidence=())


def test_a_model_refusal_is_propagated() -> None:
    result = _propose(runtime=StubRuntime(status="refused", reasons=("MODEL_REFUSED",)))
    assert result.status == "refused"
    assert result.reasons == ("MODEL_REFUSED",)


def test_the_operator_view_carries_nothing_executable() -> None:
    context = get_proposal_context(_proposal())
    assert set(context).isdisjoint(FORBIDDEN_BROKER_FIELDS)
    assert context["instrument"] == PROPOSAL_INSTRUMENT


# --------------------------------------------------------------------------
# FR-AGENTIC-059 - the normal pipeline, no privileged route
# --------------------------------------------------------------------------


def test_the_receiver_builds_the_request_from_its_own_factory() -> None:
    proposal = _proposal()
    request = build_evaluation_request(
        proposal,
        PRINCIPAL,
        generate_id("req"),
        generate_id("wf"),
        generate_id("cor"),
    )
    assert request.schema_id == "strategy.proposal_evaluation_request.v1"
    assert request.source_proposal_id == proposal.proposal_id
    assert request.source_content_hash == proposal.content_hash
    assert request.requested_direction == proposal.direction
    assert request.evaluation_scope == proposal.evaluation_scope


@pytest.mark.parametrize("field", list(RECEIVER_DERIVED_FIELDS))
def test_the_receiver_refuses_a_caller_supplied_identity(field) -> None:
    with pytest.raises(ValueError, match="identities are derived"):
        create_strategy_proposal_evaluation_request(**{field: "forged"})


def test_the_request_identity_is_derived_from_content() -> None:
    proposal = _proposal()
    lineage = (generate_id("req"), generate_id("wf"), generate_id("cor"))
    first = build_evaluation_request(proposal, PRINCIPAL, *lineage)
    second = build_evaluation_request(proposal, PRINCIPAL, *lineage)
    assert first.evaluation_request_id == second.evaluation_request_id
    assert first.idempotency_key == second.idempotency_key


def test_a_different_proposal_yields_a_different_request_identity() -> None:
    lineage = (generate_id("req"), generate_id("wf"), generate_id("cor"))
    first = build_evaluation_request(_proposal(), PRINCIPAL, *lineage)
    other = build_evaluation_request(
        _proposal(direction="SELL"),
        PRINCIPAL,
        *lineage,
    )
    assert first.evaluation_request_id != other.evaluation_request_id


def test_the_package_never_reaches_risk_trading_or_brokers() -> None:
    sources = "".join(
        path.read_text(encoding="utf-8") for path in PROMPT_PATH.parent.glob("*.py")
    )
    for forbidden in (
        "app.services.risk",
        "app.services.trading",
        "app.services.brokers",
        "app.services.portfolio",
        "dispatch_order_intent",
        "evaluate_live_gate",
        "calculate_position_size",
    ):
        assert forbidden not in sources


def test_only_the_handoff_reaches_the_receiver() -> None:
    importers = {
        path.name
        for path in PROMPT_PATH.parent.glob("*.py")
        if "app.services" in path.read_text(encoding="utf-8")
    }
    assert importers == {"handoff.py"}


def test_an_expired_proposal_is_never_submitted() -> None:
    proposal = _proposal(validity_seconds=60)
    port = StubIntake()
    with pytest.raises(ValueError, match="expired"):
        _submit(proposal=proposal, port=port, at_time=NOW + timedelta(seconds=61))
    assert port.requests == []


# --------------------------------------------------------------------------
# FR-AGENTIC-060 - the receiver's answer is the outcome
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "status",
    ["accepted_for_evaluation", "rejected", "expired", "no_signal"],
)
def test_every_receiver_status_is_carried_verbatim(status) -> None:
    result = receiver_result(
        status=status,
        signals_evaluated=0,
        reason_codes=("PROPOSAL_WINDOW_CLOSED",) if status == "expired" else (),
    )
    receipt = _submit(port=StubIntake(result))
    assert receipt.status == status
    assert receipt.intent_produced is False


def test_a_status_outside_the_receiver_enumeration_is_refused() -> None:
    with pytest.raises(ValidationError):
        _submit(port=StubIntake(receiver_result(status="filled")))


def test_an_intent_is_recorded_by_identity_only() -> None:
    receipt = _submit(
        port=StubIntake(
            receiver_result(trade_intent_ref="strategy.trade_intent:intent-a"),
        ),
    )
    assert receipt.intent_produced is True
    assert receipt.intent_ref == "strategy.trade_intent:intent-a"
    assert forbidden_fields(TradeProposalReceipt) == ()


def test_a_rejected_proposal_cannot_report_an_intent() -> None:
    receipt = _submit(port=StubIntake(receiver_result()))
    with pytest.raises(ValidationError, match="produced no intent"):
        build_trade_proposal_receipt(
            {
                **receipt.model_dump(),
                "status": "rejected",
                "signals_evaluated": 0,
                "intent_produced": True,
                "intent_ref": "strategy.trade_intent:intent-a",
            },
        )


def test_a_receipt_claiming_an_intent_needs_its_identity() -> None:
    receipt = _submit()
    with pytest.raises(ValidationError, match="must carry that intent's identity"):
        build_trade_proposal_receipt(
            {**receipt.model_dump(), "intent_produced": True, "intent_ref": None},
        )


def test_a_receipt_carrying_an_identity_must_report_the_intent() -> None:
    receipt = _submit()
    with pytest.raises(ValidationError, match="must report the intent"):
        build_trade_proposal_receipt(
            {
                **receipt.model_dump(),
                "intent_produced": False,
                "intent_ref": "strategy.trade_intent:intent-a",
            },
        )


@pytest.mark.parametrize("status", ["rejected", "expired"])
def test_an_unevaluated_proposal_cannot_report_signals(status) -> None:
    receipt = _submit()
    with pytest.raises(ValidationError, match="report evaluated signals"):
        build_trade_proposal_receipt(
            {
                **receipt.model_dump(),
                "status": status,
                "intent_produced": False,
                "intent_ref": None,
                "signals_evaluated": 3,
            },
        )


def test_the_receipt_binds_to_the_proposal_it_answers() -> None:
    proposal = _proposal()
    receipt = _submit(proposal=proposal)
    assert receipt.proposal_id == proposal.proposal_id
    assert receipt.proposal_content_hash == proposal.content_hash


def test_a_result_for_another_proposal_is_refused() -> None:
    proposal = _proposal()
    other = receiver_result(
        source_proposal_id="proposal-other",
        source_content_hash=proposal.content_hash,
    )
    with pytest.raises(ValueError, match="answers proposal"):
        _submit(proposal=proposal, port=StubIntake(other))


def test_a_result_for_different_content_is_refused() -> None:
    proposal = _proposal()
    other = receiver_result(
        source_proposal_id=proposal.proposal_id,
        source_content_hash="b" * 64,
    )
    with pytest.raises(ValueError, match="different proposal content"):
        _submit(proposal=proposal, port=StubIntake(other))


def test_an_incomplete_result_is_refused() -> None:
    incomplete = {"status": "rejected"}
    with pytest.raises(ValueError, match="omits"):
        _submit(port=StubIntake(incomplete))


def test_verify_result_names_every_missing_field() -> None:
    failure = verify_result({"status": "rejected"})
    assert failure is not None
    for field in ("evaluation_request_id", "source_content_hash", "source_proposal_id"):
        assert field in failure


def test_verify_binding_accepts_a_matching_result() -> None:
    proposal = _proposal()
    bound = {
        "source_proposal_id": proposal.proposal_id,
        "source_content_hash": proposal.content_hash,
    }
    assert verify_binding(proposal, bound) is None


def test_a_receipt_cannot_report_a_negative_signal_count() -> None:
    receipt = _submit()
    with pytest.raises(ValidationError, match="negative signal count"):
        build_trade_proposal_receipt(
            {**receipt.model_dump(), "signals_evaluated": -1},
        )
