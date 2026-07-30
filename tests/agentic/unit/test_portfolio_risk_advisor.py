"""Unit tests for FEAT-AGT-19 Portfolio and Risk Advisory.

Covers FR-AGENTIC-055 (current evidence, non-binding proposals with expiry),
FR-AGENTIC-056 (eight risk kinds, no approval), and FR-AGENTIC-057 (advice a
receiver would reject is refused before it is emitted, and this domain never
bypasses the receiver).
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from app.agentic import (
    build_agent_policy,
    build_agent_task,
    build_in_memory_memory_store,
    build_model_profile,
    build_tool_policy,
    get_role_registry,
    retrieve_memory,
)
from app.agentic.agents.portfolio_risk_advisory.portfolio_risk_advisor import (
    advise_portfolio,
    build_allocation_proposal,
    build_risk_advisory,
    critique_risk,
)
from app.agentic.agents.portfolio_risk_advisory.portfolio_risk_advisor.agent import (
    PROMPT_PATH,
)
from app.agentic.agents.portfolio_risk_advisory.portfolio_risk_advisor.schemas import (
    FORBIDDEN_EXECUTABLE_FIELDS,
    REQUIRED_RISK_KINDS,
    AllocationProposal,
    RiskAdvisory,
    missing_risk_kinds,
    unknown_risk_kinds,
)
from app.agentic.agents.portfolio_risk_advisory.portfolio_risk_advisor.tools import (
    ACCOUNT_STATE_TOOL,
    ALLOCATION_EVIDENCE_TOOL,
    COMMON_MODE_TOOL,
    CORRELATION_TOOL,
    FIRM_MANDATE_TOOL,
    get_registered_tool_names,
    verify_mandate,
)
from app.agentic.governance.registry import verify_prompt_artifact
from app.agentic.runtime import ModelOutcome
from app.utils import derive_stable_id, generate_id
from pydantic import ValidationError

from tests.agentic.fixtures import (
    ADVISORY_PORTFOLIO_ID,
    NOW,
    advisor_critique_output,
    advisor_model_output,
    advisory_evidence,
    build_advisor_mandate,
    build_advisor_role_manifest,
)

TASK_ID = derive_stable_id("id", "task-advisory")
SCOPE = {"environment": "sandbox", "asset_class": "fx"}
MAX_AGE = 900
FRESH = (NOW - timedelta(seconds=60)).isoformat()


class StubPort:
    """Deterministic portfolio, risk, and account evidence port."""

    def __init__(self, readings=None) -> None:
        self.readings = advisory_evidence(FRESH) if readings is None else readings
        self.calls: list[str] = []

    def get_allocation_evidence(self, portfolio_id):
        self.calls.append(f"allocation:{portfolio_id}")
        return self.readings[ALLOCATION_EVIDENCE_TOOL]

    def get_common_mode_exposure(self, portfolio_id):
        self.calls.append(f"common_mode:{portfolio_id}")
        return self.readings[COMMON_MODE_TOOL]

    def get_cross_account_correlation(self, portfolio_id):
        self.calls.append(f"correlation:{portfolio_id}")
        return self.readings[CORRELATION_TOOL]

    def get_account_state(self, portfolio_id):
        self.calls.append(f"account:{portfolio_id}")
        return self.readings[ACCOUNT_STATE_TOOL]

    def get_firm_mandate(self, portfolio_id):
        self.calls.append(f"mandate:{portfolio_id}")
        return self.readings[FIRM_MANDATE_TOOL]


class StubRuntime:
    """Deterministic runtime returning declared structured output per node."""

    def __init__(self, outputs=None, status="ok", reasons=()) -> None:
        self.outputs = {} if status != "ok" else (outputs or {})
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
                "output": self.outputs.get(node_id) if self.status == "ok" else None,
                "reasons": self.reasons,
                "provider": profile.provider,
                "model_identifier": profile.model_identifier,
                "tokens_used": 900,
                "latency_ms": 110,
                "cost": Decimal("0.05"),
            },
        )


def _runtime(**overrides: object):
    outputs = {
        "advise_portfolio": advisor_model_output(),
        "critique_risk": advisor_critique_output(),
    }
    outputs.update(overrides)
    return StubRuntime(outputs=outputs)


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
            "workflow_name": "advise_portfolio",
            "workflow_version": "1.0.0",
            "objective": "Describe where exposure sits across the fx book.",
            "input_refs": ("portfolio.common_mode_exposure:2026-07-29",),
            "principal_id": "operator-owner",
            "scope": dict(SCOPE),
            "deadline_at": NOW + timedelta(minutes=45),
            "idempotency_key": "idem-advisory",
            "budgets": {"cost": Decimal("2.00")},
        },
    )


def _tool(name: str, **overrides: object):
    fields: dict[str, object] = {
        "tool_name": name,
        "version": "1.0.0",
        "owning_feature": "FEAT-AGT-19",
        "receiver_domain": name.split(".", maxsplit=1)[0],
        "public_operation": name.split(".", 1)[1],
        "request_schema_id": f"{name}.request.v1",
        "result_schema_id": f"{name}.result.v1",
        "permission_class": "read_evidence",
        "side_effect_class": "read_only",
        "eligible_roles": ("portfolio_risk_advisor",),
        "scope": dict(SCOPE),
        "idempotent": True,
        "requires_approval": False,
        "max_input_bytes": 8_192,
        "max_output_bytes": 1_048_576,
        "timeout_seconds": 30,
        "max_calls_per_task": 8,
        "enabled": True,
    }
    fields.update(overrides)
    return build_tool_policy(fields)


def _tool_policies(**overrides: object):
    return {name: _tool(name, **overrides) for name in get_registered_tool_names()}


def _policy(**overrides: object):
    fields: dict[str, object] = {
        "role_id": "portfolio_risk_advisor",
        "role_version": "1.0.0",
        "permission_classes": ("read_evidence",),
        "allowed_tools": get_registered_tool_names(),
        "environment": "sandbox",
        "max_tool_calls": 8,
        "max_cost": Decimal("2.50"),
        "enabled": True,
    }
    fields.update(overrides)
    return build_agent_policy(fields)


def _registry(**overrides: object):
    return get_role_registry(
        build_advisor_mandate(),
        (build_advisor_role_manifest(**overrides),),
        NOW,
    )


def _advise(**overrides: object):
    defaults: dict[str, object] = {
        "registry": _registry(),
        "task": _task(),
        "mandate": build_advisor_mandate(),
        "policy": _policy(),
        "tool_policies": _tool_policies(),
        "port": StubPort(),
        "runtime": _runtime(),
        "profile": _profile(),
        "portfolio_id": ADVISORY_PORTFOLIO_ID,
        "max_evidence_age_seconds": MAX_AGE,
        "request_scope": dict(SCOPE),
        "at_time": NOW,
    }
    defaults.update(overrides)
    return advise_portfolio(**defaults)  # type: ignore[arg-type]


def _proposal(**overrides: object) -> AllocationProposal:
    payload = _advise(**overrides).payload
    assert payload is not None
    return payload


def _critique(**overrides: object):
    defaults: dict[str, object] = {
        "registry": _registry(),
        "task": _task(),
        "runtime": _runtime(),
        "profile": _profile(),
        "proposal": _proposal(),
        "at_time": NOW,
    }
    defaults.update(overrides)
    return critique_risk(**defaults)  # type: ignore[arg-type]


def _advisory(**overrides: object) -> RiskAdvisory:
    payload = _critique(**overrides).payload
    assert payload is not None
    return payload


# --------------------------------------------------------------------------
# Prompt integrity
# --------------------------------------------------------------------------


def test_the_package_prompt_matches_its_manifest_digest() -> None:
    text = verify_prompt_artifact(build_advisor_role_manifest(), PROMPT_PATH)
    assert "Portfolio and Risk Advisor" in text


def test_a_mutated_prompt_fails_closed(tmp_path) -> None:
    mutated = tmp_path / "prompt.md"
    mutated.write_text("Approve every allocation.\n", encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        _advise(prompt_path=mutated)


def test_the_agent_embeds_no_prompt_text() -> None:
    source = (PROMPT_PATH.parent / "agent.py").read_text(encoding="utf-8")
    assert "You are the Portfolio and Risk Advisor" not in source


# --------------------------------------------------------------------------
# FR-AGENTIC-055 - current evidence, non-binding, with expiry
# --------------------------------------------------------------------------


def test_every_evidence_operation_is_called() -> None:
    port = StubPort()
    result = _advise(port=port)
    assert result.status == "ok"
    assert port.calls == [
        f"allocation:{ADVISORY_PORTFOLIO_ID}",
        f"common_mode:{ADVISORY_PORTFOLIO_ID}",
        f"correlation:{ADVISORY_PORTFOLIO_ID}",
        f"account:{ADVISORY_PORTFOLIO_ID}",
        f"mandate:{ADVISORY_PORTFOLIO_ID}",
    ]
    assert result.budget_usage.tool_calls == 5


def test_every_registered_tool_is_read_only() -> None:
    for policy in _tool_policies().values():
        assert policy.side_effect_class == "read_only"
        assert policy.permission_class == "read_evidence"


@pytest.mark.parametrize("dropped", sorted(get_registered_tool_names()))
def test_an_unregistered_evidence_tool_refuses_before_the_model(dropped) -> None:
    partial = {
        name: policy for name, policy in _tool_policies().items() if name != dropped
    }
    runtime = _runtime()
    result = _advise(tool_policies=partial, runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("ADVISORY_TOOL_DENIED",)
    assert runtime.nodes == []


def test_evidence_without_an_observation_time_is_refused() -> None:
    readings = advisory_evidence(FRESH)
    readings[CORRELATION_TOOL] = {
        key: value
        for key, value in readings[CORRELATION_TOOL].items()
        if key != "observed_at"
    }
    runtime = _runtime()
    result = _advise(port=StubPort(readings), runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("EVIDENCE_UNDATED",)
    assert runtime.nodes == []


def test_stale_evidence_refuses_before_the_model() -> None:
    stale = (NOW - timedelta(seconds=MAX_AGE + 1)).isoformat()
    runtime = _runtime()
    result = _advise(port=StubPort(advisory_evidence(stale)), runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("EVIDENCE_STALE",)
    assert runtime.nodes == []


def test_evidence_exactly_at_the_freshness_bound_is_accepted() -> None:
    edge = (NOW - timedelta(seconds=MAX_AGE)).isoformat()
    result = _advise(port=StubPort(advisory_evidence(edge)))
    assert result.status == "ok"


def test_one_stale_reading_is_enough_to_refuse() -> None:
    readings = advisory_evidence(FRESH)
    readings[ACCOUNT_STATE_TOOL] = {
        **readings[ACCOUNT_STATE_TOOL],
        "observed_at": (NOW - timedelta(hours=6)).isoformat(),
    }
    result = _advise(port=StubPort(readings))
    assert result.status == "refused"
    assert result.reasons == ("EVIDENCE_STALE",)
    assert ACCOUNT_STATE_TOOL in (result.detail or "")


def test_evidence_whose_age_cannot_be_established_counts_as_stale() -> None:
    readings = advisory_evidence(FRESH)
    readings[CORRELATION_TOOL] = {
        **readings[CORRELATION_TOOL],
        "observed_at": "recently",
    }
    result = _advise(port=StubPort(readings))
    assert result.status == "refused"
    assert result.reasons == ("EVIDENCE_STALE",)


def test_a_naive_observation_time_counts_as_stale() -> None:
    readings = advisory_evidence(FRESH)
    readings[COMMON_MODE_TOOL] = {
        **readings[COMMON_MODE_TOOL],
        "observed_at": "2026-07-29T11:59:00",
    }
    result = _advise(port=StubPort(readings))
    assert result.status == "refused"
    assert result.reasons == ("EVIDENCE_STALE",)


def test_a_proposal_expires_after_its_declared_validity() -> None:
    proposal = _proposal(validity_seconds=1_800)
    assert proposal.issued_at == NOW.isoformat()
    assert proposal.expires_at == (NOW + timedelta(seconds=1_800)).isoformat()
    assert proposal.is_expired(NOW + timedelta(seconds=1_800))
    assert not proposal.is_expired(NOW + timedelta(seconds=1_799))


def test_a_proposal_with_no_validity_window_is_refused() -> None:
    runtime = _runtime()
    result = _advise(validity_seconds=0, runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("ADVICE_VALIDITY_INVALID",)
    assert runtime.nodes == []


def test_an_already_expired_proposal_is_unrepresentable() -> None:
    proposal = _proposal()
    with pytest.raises(ValidationError, match="strictly after"):
        build_allocation_proposal(
            {
                **proposal.model_dump(),
                "expires_at": proposal.issued_at,
            },
        )


def test_the_proposal_carries_no_executable_field() -> None:
    fields = set(AllocationProposal.model_fields)
    assert fields.isdisjoint(FORBIDDEN_EXECUTABLE_FIELDS)


def test_the_advisory_carries_no_executable_or_approval_field() -> None:
    fields = set(RiskAdvisory.model_fields)
    assert fields.isdisjoint(FORBIDDEN_EXECUTABLE_FIELDS)


@pytest.mark.parametrize(
    "phrase",
    [
        # Shared with FEAT-AGT-07: what reads as an authorization.
        "approved",
        "authorization granted",
        "position size",
        "lot size",
        "order size",
        "execute this trade",
        # Advisor-specific: what reads as something executable.
        "entry price",
        "stop loss",
        "take profit",
        "deploy to live",
        "buy at",
    ],
)
def test_approval_and_sizing_language_is_refused(phrase) -> None:
    runtime = _runtime(
        advise_portfolio=advisor_model_output(
            rationale=f"The allocation is {phrase} for the coming session.",
        ),
    )
    result = _advise(runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("PROPOSAL_NOT_ADVISORY",)


def test_mandate_scope_comes_from_risk_not_from_the_model() -> None:
    runtime = _runtime(
        advise_portfolio=advisor_model_output(
            **{"weight:momentum_fx": "greater emphasis"},
        ),
    )
    proposal = _proposal(runtime=runtime)
    # The model wrote no scope at all; Risk supplied every field.
    assert proposal.asset_class == "fx"
    assert proposal.base_currency == "USD"
    assert proposal.mandate_id == "mandate-sandbox"
    assert proposal.mandate_version == "1.0.0"


def test_an_incomplete_mandate_refuses_before_the_model() -> None:
    readings = advisory_evidence(FRESH)
    readings[FIRM_MANDATE_TOOL] = {
        key: value
        for key, value in readings[FIRM_MANDATE_TOOL].items()
        if key != "asset_class"
    }
    runtime = _runtime()
    result = _advise(port=StubPort(readings), runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("MANDATE_SCOPE_UNAVAILABLE",)
    assert runtime.nodes == []


def test_verify_mandate_names_every_missing_field() -> None:
    failure = verify_mandate({"mandate_id": "m"})
    assert failure is not None
    for field in ("asset_class", "base_currency", "mandate_version"):
        assert field in failure


def test_a_proposal_with_no_candidate_is_unrepresentable() -> None:
    runtime = _runtime(advise_portfolio={"rationale": "Nothing stands out."})
    result = _advise(runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("PROPOSAL_NOT_ADVISORY",)


def test_the_proposal_records_when_each_evidence_was_observed() -> None:
    proposal = _proposal()
    assert set(proposal.evidence_observed_at) == set(get_registered_tool_names())
    assert set(proposal.evidence_refs) == set(get_registered_tool_names())


def test_the_proposal_digest_covers_the_whole_proposal() -> None:
    proposal = _proposal()
    altered = {**proposal.model_dump(), "rationale": "A different reading entirely."}
    rebuilt = build_allocation_proposal(altered)
    assert rebuilt.proposal_hash != proposal.proposal_hash


def test_a_model_refusal_is_propagated() -> None:
    runtime = StubRuntime(status="refused", reasons=("MODEL_REFUSED",))
    result = _advise(runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("MODEL_REFUSED",)


def test_every_evidence_read_is_audited() -> None:
    store = build_in_memory_memory_store()
    _advise(audit_store=store)
    records = retrieve_memory(store, "audit", TASK_ID, NOW)
    assert len(records) == 5


# --------------------------------------------------------------------------
# FR-AGENTIC-056 - eight risk kinds, no approval
# --------------------------------------------------------------------------


def test_the_required_risk_kinds_are_exactly_eight() -> None:
    assert {
        "barrier",
        "concentration",
        "correlation",
        "liquidity",
        "mandate",
        "model",
        "operational",
        "tail",
    } == REQUIRED_RISK_KINDS


def test_a_complete_critique_assesses_every_kind() -> None:
    advisory = _advisory()
    assert set(advisory.assessments) == REQUIRED_RISK_KINDS


@pytest.mark.parametrize("dropped", sorted(REQUIRED_RISK_KINDS))
def test_a_critique_missing_any_risk_kind_is_refused(dropped) -> None:
    output = advisor_critique_output()
    del output[f"risk:{dropped}"]
    result = _critique(runtime=_runtime(critique_risk=output))
    assert result.status == "refused"
    assert result.reasons == ("RISK_COVERAGE_INCOMPLETE",)


def test_an_unrecognized_risk_kind_is_refused() -> None:
    output = advisor_critique_output()
    output["risk:vibes"] = "The vibes were assessed and found to be acceptable."
    result = _critique(runtime=_runtime(critique_risk=output))
    assert result.status == "refused"
    assert result.reasons == ("RISK_COVERAGE_INCOMPLETE",)


@pytest.mark.parametrize(
    "statement",
    ["no concerns", "looks good", "lgtm", "not applicable", "risk-free"],
)
def test_a_reassuring_assessment_is_refused(statement) -> None:
    output = advisor_critique_output(**{"risk:tail": statement})
    result = _critique(runtime=_runtime(critique_risk=output))
    assert result.status == "refused"
    assert result.reasons == ("RISK_COVERAGE_INCOMPLETE",)


def test_a_stub_assessment_is_refused() -> None:
    output = advisor_critique_output(**{"risk:liquidity": "fine"})
    result = _critique(runtime=_runtime(critique_risk=output))
    assert result.status == "refused"
    assert result.reasons == ("RISK_COVERAGE_INCOMPLETE",)


def test_missing_and_unknown_kinds_are_reported_separately() -> None:
    assert missing_risk_kinds({"tail": "x"})
    assert "tail" not in missing_risk_kinds({"tail": "x"})
    assert unknown_risk_kinds({"vibes": "x"}) == ("vibes",)
    assert unknown_risk_kinds(dict.fromkeys(REQUIRED_RISK_KINDS, "x")) == ()


def test_the_advisory_binds_to_the_proposal_it_critiqued() -> None:
    proposal = _proposal()
    advisory = _advisory(proposal=proposal)
    assert advisory.proposal_id == proposal.proposal_id
    assert advisory.proposal_hash == proposal.proposal_hash


def test_critiquing_an_expired_proposal_is_refused() -> None:
    proposal = _proposal(validity_seconds=60)
    runtime = _runtime()
    result = _critique(
        proposal=proposal,
        runtime=runtime,
        at_time=NOW + timedelta(seconds=61),
    )
    assert result.status == "refused"
    assert result.reasons == ("PROPOSAL_EXPIRED",)
    assert runtime.nodes == []


def test_unresolved_risks_are_preserved() -> None:
    advisory = _advisory()
    assert advisory.unresolved_risks == (
        "The tail estimate rests on too few joint moves to be relied upon.",
    )


def test_approval_language_in_an_assessment_is_refused() -> None:
    output = advisor_critique_output(
        **{"risk:mandate": "The allocation is approved under the current mandate."},
    )
    result = _critique(runtime=_runtime(critique_risk=output))
    assert result.status == "refused"
    assert result.reasons == ("RISK_COVERAGE_INCOMPLETE",)


def test_an_advisory_needs_supporting_evidence() -> None:
    advisory = _advisory()
    with pytest.raises(ValidationError, match="is required"):
        build_risk_advisory({**advisory.model_dump(), "evidence_refs": ()})


def test_the_critique_reads_the_proposal_as_untrusted_evidence() -> None:
    runtime = _runtime()
    _critique(runtime=runtime)
    invocation = runtime.invocations[-1]
    assert "rationale" in invocation.untrusted_evidence
    assert "rationale" not in invocation.trusted_context
    assert invocation.trusted_context["proposal_hash"]


# --------------------------------------------------------------------------
# FR-AGENTIC-057 - the receiver decides, and this domain never bypasses it
# --------------------------------------------------------------------------


def test_the_package_never_calls_a_receiver() -> None:

    sources = "".join(
        path.read_text(encoding="utf-8") for path in PROMPT_PATH.parent.glob("*.py")
    )
    for forbidden in (
        "review_allocation_proposal",
        "AllocationReviewRequest",
        "coordinate_review",
        "app.services.portfolio",
        "app.services.risk",
        "app.services.analytics",
        "app.services.data",
    ):
        assert forbidden not in sources


def test_the_package_imports_no_receiver_domain() -> None:
    from pathlib import Path

    importers = {
        path.name
        for path in Path(PROMPT_PATH.parent).glob("*.py")
        if "app.services" in path.read_text(encoding="utf-8")
    }
    assert importers == set()


def test_advice_carries_what_a_receiver_checks() -> None:
    proposal = _proposal()
    # Identity, scope, evidence, and freshness are the four things a receiver
    # rejects on. Each is present and derived, not asserted by the model.
    assert proposal.proposal_id
    assert proposal.proposal_hash
    assert proposal.mandate_id
    assert proposal.mandate_version
    assert proposal.asset_class
    assert proposal.base_currency
    assert proposal.evidence_refs
    assert proposal.evidence_observed_at
    assert proposal.expires_at > proposal.issued_at


def test_a_scope_change_produces_a_different_proposal_digest() -> None:
    readings = advisory_evidence(FRESH)
    readings[FIRM_MANDATE_TOOL] = {
        **readings[FIRM_MANDATE_TOOL],
        "asset_class": "equity",
    }
    widened = _proposal(port=StubPort(readings))
    assert widened.asset_class == "equity"
    assert widened.proposal_hash != _proposal().proposal_hash
