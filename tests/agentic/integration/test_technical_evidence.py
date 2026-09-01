"""Integration evidence for FEAT-AGT-11 across the governed control plane.

Exercises the full path a role-bearing feature must traverse: mandate and
roster validation, policy-registry validation, deny-by-default tool
authorization, governed evidence gathering, prompt-integrity verification, and
a bound typed result.

The receiver operations arrive as an injected port bound to deterministic
doubles, so no broker, provider, or network call occurs. What is exercised is
the governance path, which is real.
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
from app.agentic.agents.market_analysis.technical_analyst import (
    analyze_technical_context,
)
from app.agentic.agents.market_analysis.technical_analyst.tools import (
    get_registered_tool_names,
)
from app.agentic.runtime import ModelOutcome
from app.kernel.identity import derive_stable_id, generate_id

from tests.agentic.fixtures import (
    NOW,
    TECHNICAL_ROLE_ID,
    build_technical_mandate,
    build_technical_role_manifest,
)

TASK_ID = derive_stable_id("id", "task-technical-integration")
SCOPE = {"environment": "sandbox", "asset_class": "fx"}

MODEL_OUTPUT = {
    "claim:trend": "Price printed three consecutive higher lows on H1.",
    "confirmation:trend": "A close above the prior swing high confirms it.",
    "invalidation:trend": "A close below the 200-period EMA invalidates it.",
    "leakage:trend": "Evaluate using only bars closed before the decision time.",
    "uncertainty": "One session under passing data quality.",
}


class _Port:
    """Deterministic receiver-domain evidence port."""

    def __init__(self, quality_status: str = "passed") -> None:
        self.quality_status = quality_status
        self.calls: list[str] = []

    def fetch_market_evidence(self, instrument, timeframe):
        self.calls.append("market")
        return {
            "dataset_ref": f"data.market_dataset:{instrument}-{timeframe}",
            "venue": "mt5-demo",
            "window_start": "2026-07-29T08:00:00Z",
            "window_end": "2026-07-29T12:00:00Z",
        }

    def fetch_quality_evidence(self, instrument):
        self.calls.append("quality")
        return {
            "report_ref": f"data.quality_report:{instrument}",
            "status": self.quality_status,
        }

    def fetch_session_evidence(self, instrument):
        del instrument
        self.calls.append("session")
        return {"session": "london", "tradable": "true"}

    def fetch_indicator_versions(self, indicators):
        self.calls.append("indicators")
        return dict.fromkeys(indicators, "1.0.0")


class _Runtime:
    """Deterministic runtime satisfying the AdkRuntime port."""

    def __init__(self) -> None:
        self.invocations: list[object] = []

    def execute_node(self, node_id, profile, invocation):
        del node_id
        self.invocations.append(invocation)
        return ModelOutcome.model_validate(
            {
                "invocation_id": invocation.invocation_id,
                "status": "ok",
                "output": dict(MODEL_OUTPUT),
                "reasons": (),
                "provider": profile.provider,
                "model_identifier": profile.model_identifier,
                "tokens_used": 500,
                "latency_ms": 40,
                "cost": Decimal("0.02"),
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
            "workflow_name": "analyze_technical_context",
            "workflow_version": "1.0.0",
            "objective": "Describe EURUSD H1 structure.",
            "input_refs": ("data.market_dataset:EURUSD-H1",),
            "principal_id": "operator-owner",
            "scope": dict(SCOPE),
            "deadline_at": NOW + timedelta(minutes=15),
            "idempotency_key": "idem-technical-integration",
            "budgets": {"cost": Decimal("1.00")},
        },
    )


def _tool(name: str):
    return build_tool_policy(
        {
            "tool_name": name,
            "version": "1.0.0",
            "owning_feature": "FEAT-AGT-11",
            "receiver_domain": name.split(".", maxsplit=1)[0],
            "public_operation": name.split(".", 1)[1],
            "request_schema_id": f"{name}.request.v1",
            "result_schema_id": f"{name}.result.v1",
            "permission_class": "read_evidence",
            "side_effect_class": "read_only",
            "eligible_roles": (TECHNICAL_ROLE_ID,),
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


def _policy():
    return build_agent_policy(
        {
            "role_id": TECHNICAL_ROLE_ID,
            "role_version": "1.0.0",
            "permission_classes": ("read_evidence",),
            "allowed_tools": get_registered_tool_names(),
            "environment": "sandbox",
            "max_tool_calls": 8,
            "max_cost": Decimal("2.50"),
            "enabled": True,
        },
    )


def test_technical_analyst_traverses_the_full_governed_path() -> None:
    # 1. Mandate and roster validate, and the prompt hash chain holds.
    mandate = build_technical_mandate()
    assert validate_firm_mandate(mandate, NOW) is mandate
    registry = get_role_registry(mandate, (build_technical_role_manifest(),), NOW)
    manifest = resolve_role_manifest(registry, TECHNICAL_ROLE_ID)
    assert set(manifest.tools) == set(get_registered_tool_names())

    # 2. Every registered tool is covered by a validated policy.
    tools, policies = validate_policy_registry(
        mandate,
        tuple(_tool(name) for name in get_registered_tool_names()),
        (_policy(),),
    )
    assert set(tools) == set(get_registered_tool_names())

    # 3. The run gathers evidence through authorized tool calls and binds it.
    port, runtime = _Port(), _Runtime()
    audit = build_in_memory_memory_store()
    result = analyze_technical_context(
        registry,
        _task(),
        mandate,
        policies[TECHNICAL_ROLE_ID],
        tools,
        port,
        runtime,
        _profile(),
        "EURUSD",
        "H1",
        ("ema", "atr"),
        request_scope=dict(SCOPE),
        audit_store=audit,
        at_time=NOW,
    )

    assert result.status == "ok"
    payload = result.payload
    assert payload is not None
    assert payload.instrument == "EURUSD"
    assert dict(payload.indicator_versions) == {"ema": "1.0.0", "atr": "1.0.0"}
    assert set(payload.confirmations) == set(payload.claims)
    assert set(payload.invalidations) == set(payload.claims)
    assert set(payload.leakage_notes) == set(payload.claims)

    # 4. Every tool call is audited, and provenance ties back to the prompt.
    assert port.calls == ["market", "quality", "session", "indicators"]
    assert len(retrieve_memory(audit, "audit", TASK_ID, at_time=NOW)) == 4
    assert result.provenance.base_prompt_hash == manifest.base_prompt_hash


def test_technical_analyst_has_no_broker_or_provider_reach() -> None:
    # The mandate validator rejects any broker tool outright, so this role
    # cannot be given one even by a mistaken mandate.
    mandate = build_technical_mandate(
        tool_scopes={"brokers.place_order": "read_evidence"},
    )
    with pytest.raises(ValueError, match="Brokers"):
        validate_firm_mandate(mandate, NOW)


def test_technical_analyst_refuses_on_failed_quality_evidence() -> None:
    mandate = build_technical_mandate()
    registry = get_role_registry(mandate, (build_technical_role_manifest(),), NOW)
    tools, policies = validate_policy_registry(
        mandate,
        tuple(_tool(name) for name in get_registered_tool_names()),
        (_policy(),),
    )
    runtime = _Runtime()
    result = analyze_technical_context(
        registry,
        _task(),
        mandate,
        policies[TECHNICAL_ROLE_ID],
        tools,
        _Port(quality_status="failed"),
        runtime,
        _profile(),
        "EURUSD",
        "H1",
        ("ema",),
        request_scope=dict(SCOPE),
        at_time=NOW,
    )
    assert result.status == "refused"
    assert result.reasons == ("DATA_QUALITY_FAILED",)
    # The model was never reached: quality gates before interpretation.
    assert runtime.invocations == []
