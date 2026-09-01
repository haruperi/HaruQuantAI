"""Executable FEAT-AGT-19 Portfolio and Risk Advisor usage example.

Demonstrates the two registered public operations through the documented API.
The portfolio, risk, and account evidence arrives as an injected port bound to
deterministic doubles: no exposure is computed, no limit is read from a live
account, no network call occurs, and Agentic holds no credential.

The point of the demonstration is that the advice is non-binding by
construction. There is no field on a proposal that an execution path could
consume, approval and price vocabulary is refused outright, every proposal
expires, and Portfolio and Risk keep the decision — the last section shows the
receiver's own contract rejecting a projection this domain never builds.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

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
    critique_risk,
)
from app.agentic.agents.portfolio_risk_advisory.portfolio_risk_advisor.schemas import (
    FORBIDDEN_EXECUTABLE_FIELDS,
    REQUIRED_RISK_KINDS,
    AllocationProposal,
    RiskAdvisory,
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
from app.kernel.identity import derive_stable_id, generate_id
from app.services.risk import create_allocation_review_request

from tests.agentic.usage._runner import run_feature_usage

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tests.agentic.fixtures import (
    ADVISOR_ROLE_ID,
    ADVISORY_PORTFOLIO_ID,
    advisor_critique_output,
    advisor_model_output,
    advisory_evidence,
    build_advisor_mandate,
    build_advisor_role_manifest,
)

NOW = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
TASK_ID = derive_stable_id("id", "task-advisory-usage")
SCOPE = {"environment": "sandbox", "asset_class": "fx"}
MAX_AGE = 900
FRESH = (NOW - timedelta(seconds=120)).isoformat()

BANNER = "=" * 88


def heading(requirement: str, statement: str) -> None:
    """Print one requirement heading.

    Args:
        requirement: Functional requirement identifier.
        statement: What the requirement obliges.
    """
    print(f"\n{BANNER}\n{requirement}: {statement}\n{BANNER}")


class DeterministicPort:
    """Deterministic portfolio, risk, and account evidence port."""

    def __init__(self, readings=None) -> None:
        """Store the readings this port will return.

        Args:
            readings: Optional tool identity to receiver evidence.
        """
        self.readings = advisory_evidence(FRESH) if readings is None else readings
        self.calls: list[str] = []

    def get_allocation_evidence(self, portfolio_id):
        """Return the Analytics allocation evidence."""
        self.calls.append(f"{ALLOCATION_EVIDENCE_TOOL}:{portfolio_id}")
        return self.readings[ALLOCATION_EVIDENCE_TOOL]

    def get_common_mode_exposure(self, portfolio_id):
        """Return the Portfolio common-mode exposure report."""
        self.calls.append(f"{COMMON_MODE_TOOL}:{portfolio_id}")
        return self.readings[COMMON_MODE_TOOL]

    def get_cross_account_correlation(self, portfolio_id):
        """Return the Portfolio cross-account correlation report."""
        self.calls.append(f"{CORRELATION_TOOL}:{portfolio_id}")
        return self.readings[CORRELATION_TOOL]

    def get_account_state(self, portfolio_id):
        """Return the Data account-state snapshot."""
        self.calls.append(f"{ACCOUNT_STATE_TOOL}:{portfolio_id}")
        return self.readings[ACCOUNT_STATE_TOOL]

    def get_firm_mandate(self, portfolio_id):
        """Return the Risk-owned firm mandate scope."""
        self.calls.append(f"{FIRM_MANDATE_TOOL}:{portfolio_id}")
        return self.readings[FIRM_MANDATE_TOOL]


class DeterministicRuntime:
    """Deterministic runtime returning declared structured output per node."""

    def __init__(self, outputs=None) -> None:
        """Store the outputs this runtime will return.

        Args:
            outputs: Optional node identity to structured output.
        """
        self.outputs = outputs or {
            "advise_portfolio": advisor_model_output(),
            "critique_risk": advisor_critique_output(),
        }
        self.nodes: list[str] = []

    def execute_node(self, node_id, profile, invocation):
        """Return the declared output for one node.

        Args:
            node_id: Node identity being executed.
            profile: Pinned evaluated model profile.
            invocation: Governed model invocation.

        Returns:
            The deterministic model outcome.
        """
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


def make_runtime(**overrides: object) -> DeterministicRuntime:
    """Build a runtime with optional per-node output overrides.

    Args:
        **overrides: Node identity to structured output.

    Returns:
        A deterministic runtime.
    """
    outputs = {
        "advise_portfolio": advisor_model_output(),
        "critique_risk": advisor_critique_output(),
    }
    outputs.update(overrides)
    return DeterministicRuntime(outputs)


def profile():
    """Build the pinned evaluated model profile.

    Returns:
        A validated immutable model profile.
    """
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


def task():
    """Build the bounded governed task.

    Returns:
        A validated immutable agent task.
    """
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
            "idempotency_key": "idem-advisory-usage",
            "budgets": {"cost": Decimal("2.00")},
        },
    )


def tool_policies():
    """Build the registered read-only tool policies.

    Returns:
        Tool identity to validated policy.
    """
    return {
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


def policy():
    """Build the requesting agent policy.

    Returns:
        A validated immutable agent policy.
    """
    return build_agent_policy(
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
    )


def advise(**overrides: object):
    """Run one advisory with optional overrides.

    Args:
        **overrides: Optional argument overrides.

    Returns:
        The typed advisory result.
    """
    data: dict[str, object] = {
        "registry": get_role_registry(
            build_advisor_mandate(),
            (build_advisor_role_manifest(),),
            NOW,
        ),
        "task": task(),
        "mandate": build_advisor_mandate(),
        "policy": policy(),
        "tool_policies": tool_policies(),
        "port": DeterministicPort(),
        "runtime": make_runtime(),
        "profile": profile(),
        "portfolio_id": ADVISORY_PORTFOLIO_ID,
        "max_evidence_age_seconds": MAX_AGE,
        "request_scope": dict(SCOPE),
        "at_time": NOW,
    }
    data.update(overrides)
    return advise_portfolio(**data)


def fr_agentic_055() -> None:
    """Demonstrate current evidence, non-binding advice, and expiry."""
    heading(
        "FR-AGENTIC-055",
        "Portfolio advice uses current Analytics, Portfolio, Risk, and "
        "account-scope evidence and returns non-binding proposals with expiry.",
    )

    port = DeterministicPort()
    store = build_in_memory_memory_store()
    result = advise(port=port, audit_store=store)
    proposal = result.payload

    print(f"  evidence reads:      {len(port.calls)}")
    for name in port.calls:
        print(f"    - {name}")
    print(f"  audited tool calls:  {result.budget_usage.tool_calls}")
    print(
        f"  audit records:       {len(retrieve_memory(store, 'audit', TASK_ID, NOW))}"
    )
    print(f"  issued at:           {proposal.issued_at}")
    print(f"  expires at:          {proposal.expires_at}")
    print(f"  mandate scope:       {proposal.asset_class} / {proposal.base_currency}")
    print(f"  proposal digest:     {proposal.proposal_hash}")

    print("\n  Emphasis is relative, never executable:")
    for candidate, weight in sorted(proposal.relative_weights.items()):
        print(f"    {candidate:<14} {weight}")
    overlap = set(AllocationProposal.model_fields) & set(FORBIDDEN_EXECUTABLE_FIELDS)
    print(f"    executable fields on the model: {sorted(overlap) or 'none'}")

    print("\n  Stale evidence is refused before the model is invoked:")
    for label, age in (
        ("2 minutes old", 120),
        ("15 minutes old", 900),
        ("4 hours old", 14_400),
    ):
        observed = (NOW - timedelta(seconds=age)).isoformat()
        runtime = make_runtime()
        outcome = advise(
            port=DeterministicPort(advisory_evidence(observed)), runtime=runtime
        )
        verdict = "accepted" if outcome.status == "ok" else outcome.reasons[0]
        print(f"    {label:<16} -> {verdict:<16} model calls: {len(runtime.nodes)}")

    print("\n  Approval and price vocabulary is refused:")
    for phrase in (
        "approved",
        "position size",
        "entry price",
        "stop loss",
        "deploy to live",
    ):
        runtime = make_runtime(
            advise_portfolio=advisor_model_output(
                rationale=f"The allocation is {phrase} for the coming session.",
            ),
        )
        outcome = advise(runtime=runtime)
        print(f"    {phrase:<16} -> {outcome.reasons[0]}")

    print("\n  A proposal cannot be built already expired:")
    try:
        build_allocation_proposal(
            {**proposal.model_dump(), "expires_at": proposal.issued_at},
        )
        note = "ERROR: an expired proposal was accepted"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        note = "unbuildable"
    print(f"    {note}")


def fr_agentic_056() -> None:
    """Demonstrate the eight risk kinds and the absence of any approval."""
    heading(
        "FR-AGENTIC-056",
        "Risk critics identify mandate, barrier, tail, concentration, "
        "liquidity, correlation, operational, and model risks but emit no "
        "approval.",
    )

    proposal = advise().payload
    runtime = make_runtime()
    advisory = critique_risk(
        registry=get_role_registry(
            build_advisor_mandate(),
            (build_advisor_role_manifest(),),
            NOW,
        ),
        task=task(),
        runtime=runtime,
        profile=profile(),
        proposal=proposal,
        at_time=NOW,
    ).payload

    print(f"  required risk kinds: {sorted(REQUIRED_RISK_KINDS)}")
    for kind, statement in sorted(advisory.assessments.items()):
        print(f"    [{kind}] {statement[:56]}...")
    print(f"  unresolved risks:    {advisory.unresolved_risks}")
    print(f"  bound to proposal:   {advisory.proposal_hash == proposal.proposal_hash}")

    print("\n  The advisory has no field that could carry consent:")
    overlap = set(RiskAdvisory.model_fields) & set(FORBIDDEN_EXECUTABLE_FIELDS)
    print(f"    fields: {sorted(RiskAdvisory.model_fields)}")
    print(f"    approval-shaped fields: {sorted(overlap) or 'none'}")

    print("\n  A critique that omits or reassures is refused:")
    cases = (
        ("a missing kind", {"drop": "liquidity"}),
        ("an unknown kind", {"add": "vibes"}),
        ("a reassurance", {"reassure": "tail"}),
        ("a stub answer", {"stub": "barrier"}),
        ("approval language", {"approve": "mandate"}),
    )
    for label, spec in cases:
        output = advisor_critique_output()
        if "drop" in spec:
            del output[f"risk:{spec['drop']}"]
        if "add" in spec:
            output[f"risk:{spec['add']}"] = (
                "The vibes were examined and are acceptable."
            )
        if "reassure" in spec:
            output[f"risk:{spec['reassure']}"] = "no concerns"
        if "stub" in spec:
            output[f"risk:{spec['stub']}"] = "fine"
        if "approve" in spec:
            output[f"risk:{spec['approve']}"] = (
                "The allocation is approved under the current mandate."
            )
        outcome = critique_risk(
            registry=get_role_registry(
                build_advisor_mandate(),
                (build_advisor_role_manifest(),),
                NOW,
            ),
            task=task(),
            runtime=make_runtime(critique_risk=output),
            profile=profile(),
            proposal=proposal,
            at_time=NOW,
        )
        print(f"    {label:<20} -> {outcome.reasons[0]}")

    print("\n  An expired proposal is not critiqued at all:")
    short = advise(validity_seconds=60).payload
    stale_runtime = make_runtime()
    outcome = critique_risk(
        registry=get_role_registry(
            build_advisor_mandate(),
            (build_advisor_role_manifest(),),
            NOW,
        ),
        task=task(),
        runtime=stale_runtime,
        profile=profile(),
        proposal=short,
        at_time=NOW + timedelta(seconds=61),
    )
    print(f"    {outcome.reasons[0]}, model calls: {len(stale_runtime.nodes)}")


def fr_agentic_057() -> None:
    """Demonstrate that the receiver decides, using its own contract."""
    heading(
        "FR-AGENTIC-057",
        "Portfolio or risk advice is rejected by the receiver when evidence, "
        "identity, scope, authorization, or freshness is invalid.",
    )

    proposal = advise().payload
    print("  The advice carries what a receiver checks:")
    print(f"    identity:   {proposal.proposal_id}")
    print(f"    digest:     {proposal.proposal_hash[:32]}...")
    print(f"    scope:      {proposal.mandate_id}@{proposal.mandate_version}")
    print(f"    evidence:   {len(proposal.evidence_refs)} references")
    print(f"    freshness:  {len(proposal.evidence_observed_at)} observation times")

    print("\n  Risk's own contract is what accepts or rejects a projection:")
    base = {
        "projection_kind": "rebalance",
        "portfolio_id": proposal.portfolio_id,
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
    projections = (
        ("a self-contained projection", {}),
        ("without evidence hashes", {"evidence_hashes": {}}),
        ("without components", {"ordered_components": ()}),
        ("an incompatible route", {"execution_route": "live"}),
        ("a rebalance with no plan", {"plan_id": None}),
    )
    for label, override in projections:
        try:
            create_allocation_review_request(**{**base, **override})
            verdict = "accepted by Risk"
        except Exception as error:  # noqa: BLE001 - usage demonstrates rejection.
            detail = next(
                (
                    line.split("Value error, ", 1)[1].split(" [type=", 1)[0].strip()
                    for line in str(error).splitlines()
                    if "Value error, " in line
                ),
                "rejected",
            )
            verdict = f"rejected by Risk: {detail}"
        print(f"    {label:<28} -> {verdict}")

    print(
        "\n  Note: Agentic never builds that request. The projection above was "
        "assembled\n  by this usage program to show the receiver's authority; "
        "nothing in\n  agents/portfolio_risk_advisory imports Portfolio, Risk, "
        "Analytics, or Data,\n  and submitting a receiver-owned request belongs "
        "to FEAT-AGT-22."
    )


def main() -> None:
    """Run every functional-requirement demonstration for the advisor."""
    fr_agentic_055()
    fr_agentic_056()
    fr_agentic_057()


if __name__ == "__main__":
    run_feature_usage("FEAT-AGT-19", main)
