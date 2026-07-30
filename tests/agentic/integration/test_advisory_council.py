"""Integration evidence for `WF-AGT-TER` — portfolio and risk council.

Exercises the full path advice must traverse: mandate and roster validation,
policy-registry validation, deny-by-default tool authorization across all five
read-only receiver operations, freshness established from what the receivers
reported, a non-binding proposal bounded by Risk-supplied scope, and an
independent critique covering every required risk kind.

The last section is the part worth reading. `FR-AGENTIC-057` says the receiver
rejects invalid advice, so the test builds a Risk-owned `AllocationReviewRequest`
from an advisory and shows **Risk's own contract** rejecting an incomplete or
incompatible projection. Production code in this package never constructs one —
a separate test asserts that — but the receiver's authority is demonstrated
here with the receiver's real contract rather than a stand-in.
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
    resolve_role_manifest,
    retrieve_memory,
    validate_firm_mandate,
    validate_policy_registry,
)
from app.agentic.agents.portfolio_risk_advisory.portfolio_risk_advisor import (
    advise_portfolio,
    critique_risk,
)
from app.agentic.agents.portfolio_risk_advisory.portfolio_risk_advisor.schemas import (
    REQUIRED_RISK_KINDS,
)
from app.agentic.agents.portfolio_risk_advisory.portfolio_risk_advisor.tools import (
    ACCOUNT_STATE_TOOL,
    ALLOCATION_EVIDENCE_TOOL,
    COMMON_MODE_TOOL,
    CORRELATION_TOOL,
    FIRM_MANDATE_TOOL,
    get_registered_tool_names,
)
from app.agentic.runtime import ModelOutcome
from app.services.risk import AllocationReviewRequest
from app.utils import derive_stable_id, generate_id
from pydantic import ValidationError

from tests.agentic.fixtures import (
    ADVISOR_ROLE_ID,
    ADVISORY_PORTFOLIO_ID,
    NOW,
    advisor_critique_output,
    advisor_model_output,
    advisory_evidence,
    build_advisor_mandate,
    build_advisor_role_manifest,
)

TASK_ID = derive_stable_id("id", "task-advisory-council")
SCOPE = {"environment": "sandbox", "asset_class": "fx"}
MAX_AGE = 900
FRESH = (NOW - timedelta(seconds=120)).isoformat()


class _Port:
    """Deterministic advisory-evidence port recording its reads."""

    def __init__(self, readings=None) -> None:
        self.readings = advisory_evidence(FRESH) if readings is None else readings
        self.calls: list[str] = []

    def get_allocation_evidence(self, portfolio_id):
        self.calls.append(f"{ALLOCATION_EVIDENCE_TOOL}:{portfolio_id}")
        return self.readings[ALLOCATION_EVIDENCE_TOOL]

    def get_common_mode_exposure(self, portfolio_id):
        self.calls.append(f"{COMMON_MODE_TOOL}:{portfolio_id}")
        return self.readings[COMMON_MODE_TOOL]

    def get_cross_account_correlation(self, portfolio_id):
        self.calls.append(f"{CORRELATION_TOOL}:{portfolio_id}")
        return self.readings[CORRELATION_TOOL]

    def get_account_state(self, portfolio_id):
        self.calls.append(f"{ACCOUNT_STATE_TOOL}:{portfolio_id}")
        return self.readings[ACCOUNT_STATE_TOOL]

    def get_firm_mandate(self, portfolio_id):
        self.calls.append(f"{FIRM_MANDATE_TOOL}:{portfolio_id}")
        return self.readings[FIRM_MANDATE_TOOL]


class _Runtime:
    """Deterministic runtime returning declared structured output per node."""

    def __init__(self, outputs=None) -> None:
        self.outputs = outputs or {
            "advise_portfolio": advisor_model_output(),
            "critique_risk": advisor_critique_output(),
        }
        self.nodes: list[str] = []

    def execute_node(self, node_id, profile, invocation):
        self.nodes.append(node_id)
        return ModelOutcome.model_validate(
            {
                "invocation_id": invocation.invocation_id,
                "status": "ok",
                "output": self.outputs.get(node_id),
                "reasons": (),
                "provider": profile.provider,
                "model_identifier": profile.model_identifier,
                "tokens_used": 950,
                "latency_ms": 130,
                "cost": Decimal("0.06"),
            },
        )


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
            "idempotency_key": "idem-advisory-council",
            "budgets": {"cost": Decimal("2.00")},
        },
    )


def _control_plane():
    mandate = build_advisor_mandate()
    manifest = build_advisor_role_manifest()
    registry = get_role_registry(mandate, (manifest,), NOW)
    tools = {
        name: build_tool_policy(
            {
                "tool_name": name,
                "version": "1.0.0",
                "owning_feature": "FEAT-AGT-19",
                "receiver_domain": name.split(".", maxsplit=1)[0],
                "public_operation": name.split(".", 1)[1],
                "request_schema_id": f"{name}.request.v1",
                "result_schema_id": f"{name}.result.v1",
                "permission_class": "read_evidence",
                "side_effect_class": "read_only",
                "eligible_roles": (ADVISOR_ROLE_ID,),
                "scope": dict(SCOPE),
                "idempotent": True,
                "requires_approval": False,
                "max_input_bytes": 8_192,
                "max_output_bytes": 1_048_576,
                "timeout_seconds": 30,
                "max_calls_per_task": 8,
                "enabled": True,
            },
        )
        for name in get_registered_tool_names()
    }
    policies = {
        ADVISOR_ROLE_ID: build_agent_policy(
            {
                "role_id": ADVISOR_ROLE_ID,
                "role_version": "1.0.0",
                "permission_classes": ("read_evidence",),
                "allowed_tools": get_registered_tool_names(),
                "environment": "sandbox",
                "max_tool_calls": 8,
                "max_cost": Decimal("2.50"),
                "enabled": True,
            },
        ),
    }
    return (mandate, registry, tools, policies)


def _advise(**overrides: object):
    mandate, registry, tools, policies = _control_plane()
    data: dict[str, object] = {
        "registry": registry,
        "task": _task(),
        "mandate": mandate,
        "policy": policies[ADVISOR_ROLE_ID],
        "tool_policies": tools,
        "port": _Port(),
        "runtime": _Runtime(),
        "profile": _profile(),
        "portfolio_id": ADVISORY_PORTFOLIO_ID,
        "max_evidence_age_seconds": MAX_AGE,
        "request_scope": dict(SCOPE),
        "at_time": NOW,
    }
    data.update(overrides)
    return advise_portfolio(**data)


def test_advisory_traverses_the_full_governed_path() -> None:
    # 1. Mandate and roster validate, and the prompt hash chain holds.
    mandate, registry, tools, policies = _control_plane()
    assert validate_firm_mandate(mandate, NOW) is mandate
    manifest = resolve_role_manifest(registry, ADVISOR_ROLE_ID)
    assert set(manifest.tools) == set(get_registered_tool_names())

    # 2. The policy registry accepts a read-only advisory surface.
    registered_tools, registered_policies = validate_policy_registry(
        mandate,
        tuple(tools.values()),
        tuple(policies.values()),
    )
    assert set(registered_tools) == set(get_registered_tool_names())
    assert set(registered_policies) == {ADVISOR_ROLE_ID}

    # 3. Every receiver read traverses the permission enforcement point.
    port = _Port()
    store = build_in_memory_memory_store()
    runtime = _Runtime()
    result = advise_portfolio(
        registry=registry,
        task=_task(),
        mandate=mandate,
        policy=policies[ADVISOR_ROLE_ID],
        tool_policies=tools,
        port=port,
        runtime=runtime,
        profile=_profile(),
        portfolio_id=ADVISORY_PORTFOLIO_ID,
        max_evidence_age_seconds=MAX_AGE,
        request_scope=dict(SCOPE),
        audit_store=store,
        at_time=NOW,
    )
    assert result.status == "ok"
    # Read in evidence order, not alphabetically: the mandate is read last so
    # scope is applied to evidence already in hand.
    assert port.calls == [
        f"{name}:{ADVISORY_PORTFOLIO_ID}"
        for name in (
            ALLOCATION_EVIDENCE_TOOL,
            COMMON_MODE_TOOL,
            CORRELATION_TOOL,
            ACCOUNT_STATE_TOOL,
            FIRM_MANDATE_TOOL,
        )
    ]
    assert {call.rsplit(":", 1)[0] for call in port.calls} == set(
        get_registered_tool_names(),
    )
    assert len(retrieve_memory(store, "audit", TASK_ID, NOW)) == 5

    # 4. The proposal is non-binding, scoped by Risk, and expires.
    proposal = result.payload
    assert proposal is not None
    assert proposal.asset_class == "fx"
    assert proposal.base_currency == "USD"
    assert proposal.expires_at > proposal.issued_at

    # 5. The critique covers every required risk kind and authorizes nothing.
    critique = critique_risk(
        registry=registry,
        task=_task(),
        runtime=runtime,
        profile=_profile(),
        proposal=proposal,
        at_time=NOW,
    )
    assert critique.status == "ok"
    advisory = critique.payload
    assert advisory is not None
    assert set(advisory.assessments) == REQUIRED_RISK_KINDS
    assert advisory.proposal_hash == proposal.proposal_hash
    assert runtime.nodes == ["advise_portfolio", "critique_risk"]


def test_stale_evidence_stops_the_council_before_the_model() -> None:
    stale = (NOW - timedelta(hours=4)).isoformat()
    runtime = _Runtime()
    result = _advise(port=_Port(advisory_evidence(stale)), runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("EVIDENCE_STALE",)
    assert runtime.nodes == []


def test_a_denied_tool_stops_the_council_before_the_model() -> None:
    _, _, tools, _ = _control_plane()
    without_mandate = {
        name: policy for name, policy in tools.items() if name != FIRM_MANDATE_TOOL
    }
    runtime = _Runtime()
    result = _advise(tool_policies=without_mandate, runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("ADVISORY_TOOL_DENIED",)
    assert runtime.nodes == []


# --------------------------------------------------------------------------
# FR-AGENTIC-057 - the receiver decides, using its own contract
# --------------------------------------------------------------------------


def _projection(**overrides: object) -> dict[str, object]:
    """Build the Risk-owned projection fields an advisory would inform.

    This lives in the test, never in production: Agentic does not author a
    receiver request. What it demonstrates is that the receiver's own contract
    is what rejects an invalid one.
    """
    data: dict[str, object] = {
        "projection_kind": "rebalance",
        "portfolio_id": ADVISORY_PORTFOLIO_ID,
        "portfolio_version": "1.0.0",
        "result_id": None,
        "plan_id": "plan-a",
        "ordered_components": ({"candidate": "momentum_fx"},),
        "eligibility_decision_refs": ("risk.eligibility:momentum_fx",),
        "account_evidence_ref": "data.account_state_snapshot:2026-07-29T11:58Z",
        "market_evidence_ref": "data.market_context:2026-07-29T11:58Z",
        "fx_evidence_refs": ("data.fx_conversion:USD",),
        "evidence_hashes": {"account": "sha256:account-a"},
        "runtime_profile": "simulation",
        "execution_route": "sim",
        "approval_refs": (),
        "requested_at": NOW,
        "request_id": generate_id("req"),
        "workflow_id": generate_id("wf"),
        "correlation_id": generate_id("cor"),
    }
    data.update(overrides)
    return data


def test_the_receiver_accepts_a_self_contained_projection() -> None:
    request = AllocationReviewRequest.model_validate(_projection())
    assert request.portfolio_id == ADVISORY_PORTFOLIO_ID


def test_the_receiver_rejects_a_projection_without_evidence() -> None:
    with pytest.raises(ValidationError, match="not self-contained"):
        AllocationReviewRequest.model_validate(_projection(evidence_hashes={}))


def test_the_receiver_rejects_a_projection_with_no_components() -> None:
    with pytest.raises(ValidationError, match="not self-contained"):
        AllocationReviewRequest.model_validate(_projection(ordered_components=()))


def test_the_receiver_rejects_an_incompatible_route() -> None:
    with pytest.raises(ValidationError, match="profile and route are incompatible"):
        AllocationReviewRequest.model_validate(
            _projection(runtime_profile="simulation", execution_route="live"),
        )


def test_the_receiver_rejects_a_rebalance_without_its_plan() -> None:
    with pytest.raises(ValidationError, match="rebalance requires plan_id"):
        AllocationReviewRequest.model_validate(_projection(plan_id=None))


def test_agentic_never_constructs_a_receiver_request() -> None:
    from pathlib import Path

    package = Path("app/agentic/agents/portfolio_risk_advisory")
    sources = "".join(
        path.read_text(encoding="utf-8") for path in package.rglob("*.py")
    )
    for forbidden in (
        "AllocationReviewRequest",
        "review_allocation_proposal",
        "app.services.risk",
        "app.services.portfolio",
    ):
        assert forbidden not in sources
