"""Executable FEAT-AGT-07 deliberation usage example.

Demonstrates every public operation registered for FEAT-AGT-07 through the
documented function-only `app.agentic` package-root API.

The agent-graph runtime is the deterministic in-repo double and no agent
package exists yet, so what runs here is the *bounded discussion mechanism*,
not real specialist reasoning. Those arrive with FEAT-AGT-08 onwards.
"""

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.agentic import (
    assemble_context,
    build_agent_task,
    build_evidence_claim,
    build_firm_mandate,
    build_in_memory_memory_store,
    build_model_profile,
    build_role_manifest,
    derive_content_hash,
    get_role_registry,
    reject_authorization_language,
    retrieve_memory,
    run_deliberation,
)
from app.agentic.runtime import ModelOutcome
from app.kernel.identity import derive_stable_id, generate_id
from app.kernel.serialization import canonical_digest

from tests.agentic.usage._runner import run_feature_usage

NOW = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
TASK_ID = derive_stable_id("id", "task-eurusd-council")
TECHNICAL = "technical_analyst"
QUANT = "quantitative_analyst"

UNIVERSAL_PROHIBITIONS = (
    "broker_credential_access",
    "broker_native_mutation",
    "mandate_modification",
    "kill_switch_clearing",
    "self_approval",
    "approval_delegation",
    "production_code_mutation",
    "hot_loading",
    "unbounded_discussion",
    "unbounded_spend",
    "unverified_evidence_use",
    "receipt_as_fill",
)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


class DeterministicRuntime:
    """Reproducible runtime satisfying the AdkRuntime port."""

    def __init__(self, refuse=()):
        self.refuse = refuse
        self.invocations = []

    def execute_node(self, node_id, profile, invocation):
        del node_id
        """Return a reproducible outcome for one node execution."""
        self.invocations.append(invocation)
        if invocation.role_id in self.refuse:
            status, output, reasons = "refused", None, ("INSUFFICIENT_EVIDENCE",)
        else:
            status = "ok"
            output = {"observation": f"{invocation.role_id} observed higher lows."}
            reasons = ()
        return ModelOutcome.model_validate(
            {
                "invocation_id": invocation.invocation_id,
                "status": status,
                "output": output,
                "reasons": reasons,
                "provider": profile.provider,
                "model_identifier": profile.model_identifier,
                "tokens_used": 120,
                "latency_ms": 30,
                "cost": Decimal("0.01"),
            },
        )


def make_mandate():
    """Build the sandbox mandate enabling both analyst roles."""
    return build_firm_mandate(
        {
            "mandate_id": "mandate-sandbox",
            "version": "1.0.0",
            "environment": "sandbox",
            "effective_at": datetime(2026, 7, 1, tzinfo=UTC),
            "expires_at": datetime(2026, 12, 31, tzinfo=UTC),
            "owner_principal": "operator-owner",
            "objectives": ("market_research",),
            "asset_scopes": {"asset_class": "fx"},
            "enabled_features": ("FEAT-AGT-11", "FEAT-AGT-12"),
            "enabled_roles": (TECHNICAL, QUANT),
            "model_profiles": ("profile-market-analysis-a",),
            "tool_scopes": {"data.get_market_data": "read_evidence"},
            "limits_profile_id": "agentic-limits-sandbox-v1",
            "budgets": {"cost": Decimal("50.00")},
            "approval_policy": ("artifact_promotion",),
            "retention_policy": {"evidence": "365d"},
            "prohibited_actions": UNIVERSAL_PROHIBITIONS,
            "fallback_policy": "refuse",
        },
        "owner-signature-sandbox",
    )


def make_manifest(role_id, feature, package, prompt):
    """Build one enabled role manifest."""
    return build_role_manifest(
        {
            "role_id": role_id,
            "version": "1.0.0",
            "owning_feature": feature,
            "department": "market_analysis",
            "agent_package": package,
            "description": "Interprets canonical deterministic evidence.",
            "objective": "Describe observable structure with invalidation.",
            "expertise_boundary": "Does not size positions or approve actions.",
            "supported_assets": ("fx",),
            "refusal_conditions": ("missing_evidence",),
            "input_schema_id": f"agentic.{role_id}_request.v1",
            "output_schema_id": f"agentic.{role_id}_pack.v1",
            "base_prompt_hash": canonical_digest(prompt),
            "role_instruction": None,
            "model_profile_id": "profile-market-analysis-a",
            "permitted_fallback": None,
            "tools": ("data.get_market_data",),
            "permission_classes": ("read_evidence",),
            "data_requirements": ("canonical_market_data",),
            "freshness_seconds": 900,
            "budgets": {"cost": Decimal("2.50")},
            "evaluation_set_id": f"eval-{role_id}-v1",
            "baseline_id": "baseline-deterministic",
            "enabled": True,
        },
    )


def make_profile():
    """Build the evaluated model profile."""
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


def make_task():
    """Build the bounded governed research task."""
    return build_agent_task(
        {
            "created_at": NOW,
            "request_id": generate_id("req"),
            "workflow_id": generate_id("wf"),
            "correlation_id": generate_id("cor"),
            "causation_id": None,
            "task_id": TASK_ID,
            "workflow_name": "firm_research_council",
            "workflow_version": "1.0.0",
            "objective": "Assess EURUSD H1 trend evidence for the London session.",
            "input_refs": ("evidence-market-eurusd-h1",),
            "principal_id": "operator-owner",
            "scope": {"environment": "sandbox", "asset_class": "fx"},
            "deadline_at": NOW + timedelta(minutes=30),
            "idempotency_key": "idem-council-0001",
            "budgets": {"cost": Decimal("5.00")},
        },
    )


def make_context(task):
    """Assemble bounded eligible context for the task."""
    claim = build_evidence_claim(
        {
            "claim_id": "claim-0001",
            "task_id": task.task_id,
            "statement": "EURUSD H1 printed three consecutive higher lows.",
            "source_ref": "data.market_dataset:eurusd-h1",
            "source_trust": "authoritative",
            "licence_ref": "internal-market-data",
            "available_at": NOW - timedelta(minutes=5),
            "observed_at": NOW,
            "content_hash": derive_content_hash({"claim": "higher-lows"}),
            "confidence_basis": "Three confirmed swing lows.",
            "falsifier": "A close below the 200-period EMA.",
            "injection_status": "clean",
        },
    )
    return assemble_context(
        task.task_id,
        (claim,),
        NOW,
        trusted_context={"instrument": "EURUSD", "timeframe": "H1"},
    )


def _registry():
    """Build the validated two-role registry."""
    return get_role_registry(
        make_mandate(),
        (
            make_manifest(
                TECHNICAL,
                "FEAT-AGT-11",
                "agents/market_analysis/technical_analyst",
                "technical-prompt",
            ),
            make_manifest(
                QUANT,
                "FEAT-AGT-12",
                "agents/market_analysis/quantitative_analyst",
                "quantitative-prompt",
            ),
        ),
        NOW,
    )


def fr_agentic_019() -> None:
    """FR-AGENTIC-019: Independent briefs first, with a complete record."""
    _header(
        "FR-AGENTIC-019: Deliberation begins with independent briefs and records "
        "participants, topology, rounds, deadlines, budgets, claims, "
        "counterclaims, tool evidence, and stop reason."
    )

    task = make_task()
    runtime = DeterministicRuntime()
    store = build_in_memory_memory_store()
    record = run_deliberation(
        _registry(),
        task,
        make_context(task),
        runtime,
        make_profile(),
        (TECHNICAL, QUANT),
        memory_store=store,
        at_time=NOW,
    )

    print(f"  participants:   {', '.join(record.plan.participants)}")
    print(f"  topology:       {record.plan.topology}")
    print(f"  stances:        {dict(record.plan.stances)}")
    print(f"  briefs:         {len(record.messages)}")
    print(f"  counterclaims:  {len(record.counterclaims)}")
    print(f"  rounds used:    {record.rounds_used} of {record.plan.max_rounds}")
    print(f"  terminal reason:{record.terminal_reason}")
    print(
        f"  persisted:      {record.persisted} "
        f"({len(retrieve_memory(store, 'audit', TASK_ID, NOW))} audit record)"
    )
    print(f"  content hash:   {record.content_hash[:16]}...")

    peer_statements = {m.content["observation"] for m in record.messages}
    leaked = [
        inv.invocation_id
        for inv in runtime.invocations
        if any(s in " ".join(inv.untrusted_evidence.values()) for s in peer_statements)
    ]
    print(f"  brief invocations exposing a peer conclusion: {len(leaked)}")
    print("  Independence is structural: a brief invocation is built from the")
    print("  assembled context alone, so no peer output can reach it.")


def fr_agentic_020() -> None:
    """FR-AGENTIC-020: Dissent survives and consensus is not authorization."""
    _header(
        "FR-AGENTIC-020: Discussion preserves minority dissent and allows "
        "insufficient_evidence; voting or consensus produces no authorization "
        "and no position size."
    )

    task = make_task()
    record = run_deliberation(
        _registry(),
        task,
        make_context(task),
        DeterministicRuntime(),
        make_profile(),
        (TECHNICAL, QUANT),
        at_time=NOW,
    )
    print(f"  dissent preserved: {len(record.dissent)}")
    for item in record.dissent:
        print(
            f"    {item.dissenting_role_id}: basis={item.basis} "
            f"unresolved={item.unresolved}"
        )
    print(f"  consensus_reached: {record.consensus_reached} (never an authorization)")
    print(f"  synthesis: {record.synthesis}")

    refused = run_deliberation(
        _registry(),
        task,
        make_context(task),
        DeterministicRuntime(refuse=(TECHNICAL, QUANT)),
        make_profile(),
        (TECHNICAL, QUANT),
        at_time=NOW,
    )
    print(
        f"  all roles refused -> {refused.terminal_reason}, "
        f"synthesis={refused.synthesis}"
    )

    for text in (
        "The council approved the trade.",
        "Use a position size of two lots.",
        "Place the order at market.",
    ):
        try:
            reject_authorization_language(text, "synthesis")
            outcome = "ERROR: authorization language was accepted"
        except Exception:  # noqa: BLE001 - usage demonstrates rejection.
            outcome = f"rejected: {text!r}"
        print(f"  {outcome}")


def fr_agentic_021() -> None:
    """FR-AGENTIC-021: Selection and caps are deterministic."""
    _header(
        "FR-AGENTIC-021: Dynamic participant selection is limited to enabled "
        "roles and deterministic caps; maximum rounds and fan-out are never "
        "model-overridable."
    )

    task = make_task()
    inflated = run_deliberation(
        _registry(),
        task,
        make_context(task),
        DeterministicRuntime(),
        make_profile(),
        (TECHNICAL, QUANT, "ghost_role", "sentiment_analyst", "coder"),
        at_time=NOW,
    )
    print(f"  requested 5 roles, selected: {', '.join(inflated.plan.participants)}")
    print(f"  caps from limits profile {inflated.plan.limits_profile_id}:")
    print(
        f"    max_participants={inflated.plan.max_participants} "
        f"max_rounds={inflated.plan.max_rounds} "
        f"max_fan_out={inflated.plan.max_fan_out}"
    )
    print(f"  rounds actually used: {inflated.rounds_used}")

    none_eligible = run_deliberation(
        _registry(),
        task,
        make_context(task),
        DeterministicRuntime(),
        make_profile(),
        ("ghost_role",),
        at_time=NOW,
    )
    print(f"  no eligible participants -> {none_eligible.terminal_reason}")

    try:
        run_deliberation(
            _registry(),
            task,
            make_context(task),
            DeterministicRuntime(),
            make_profile(),
            (TECHNICAL,),
            limits_profile_id="agentic-limits-unbounded",
            at_time=NOW,
        )
        outcome = "ERROR: an unregistered limits profile was accepted"
    except Exception:  # noqa: BLE001 - usage demonstrates rejection.
        outcome = "Unregistered limits profile correctly fails closed"
    print(f"  {outcome}")


def main() -> None:
    """Run every functional-requirement demonstration for deliberation."""
    fr_agentic_019()
    fr_agentic_020()
    fr_agentic_021()


if __name__ == "__main__":
    run_feature_usage("FEAT-AGT-07", main)
