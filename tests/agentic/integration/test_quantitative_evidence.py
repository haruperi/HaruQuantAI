"""Integration evidence for FEAT-AGT-12 across the governed control plane.

Exercises the full path a role-bearing feature must traverse: mandate and
roster validation, policy-registry validation, deny-by-default tool
authorization, deterministic catalog grounding, prompt-integrity verification,
and a bound typed result.

The Analytics catalog arrives as an injected port bound to deterministic
doubles, so no network call occurs. What is exercised is the governance path,
which is real.
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
from app.agentic.agents.market_analysis.quantitative_analyst import (
    analyze_quantitative_evidence,
)
from app.agentic.agents.market_analysis.quantitative_analyst.tools import (
    get_registered_tool_names,
)
from app.agentic.runtime import ModelOutcome
from app.utils import derive_stable_id, generate_id

from tests.agentic.fixtures import (
    NOW,
    QUANT_ROLE_ID,
    build_quantitative_mandate,
    build_quantitative_role_manifest,
)

TASK_ID = derive_stable_id("id", "task-quantitative-integration")
SCOPE = {"environment": "sandbox", "asset_class": "fx"}

DATASET_HASH = "sha256:dataset-a"
CONFIG_HASH = "sha256:config-a"

EVIDENCE = {
    "research.edge_lab_profile:v1": {
        "dataset_hash": DATASET_HASH,
        "configuration_hash": CONFIG_HASH,
        "split": "holdout",
    },
    "analytics.performance_report:v1": {
        "dataset_hash": DATASET_HASH,
        "configuration_hash": CONFIG_HASH,
        "split": "holdout",
    },
}

CATALOG = {
    "sharpe_ratio": {
        "formula": "mean(excess_returns) / stdev(excess_returns)",
        "unit": "ratio",
        "minimum_sample": "30",
    },
}

MODEL_OUTPUT = {
    "finding:risk_adjusted_return": (
        "Risk-adjusted return is positive but small on the holdout split."
    ),
    "estimator:risk_adjusted_return": "sharpe_ratio",
    "uncertainty:risk_adjusted_return": (
        "The bootstrap interval spans zero at the 95 percent level."
    ),
    "assumptions": "Returns are treated as independent across bars.",
    "limitations": "This evidence cannot establish out-of-sample profitability.",
}


class _Port:
    """Deterministic Analytics catalog port."""

    def __init__(self, minimum_statistical: str = "30") -> None:
        self.minimum_statistical = minimum_statistical
        self.calls: list[str] = []

    def fetch_metric_definition(self, metric):
        self.calls.append(f"definition:{metric}")
        return CATALOG.get(metric, {})

    def fetch_minimum_samples(self):
        self.calls.append("floors")
        return {"variance": "2", "tail": "30", "statistical": self.minimum_statistical}

    def validate_evidence_contract(self, contract, version):
        self.calls.append(f"contract:{contract}")
        return {"contract": contract, "version": version, "status": "compatible"}


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
                "tokens_used": 550,
                "latency_ms": 45,
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
            "workflow_name": "analyze_quantitative_evidence",
            "workflow_version": "1.0.0",
            "objective": "State what the holdout statistics support.",
            "input_refs": tuple(sorted(EVIDENCE)),
            "principal_id": "operator-owner",
            "scope": dict(SCOPE),
            "deadline_at": NOW + timedelta(minutes=15),
            "idempotency_key": "idem-quantitative-integration",
            "budgets": {"cost": Decimal("1.00")},
        },
    )


def _tool(name: str):
    return build_tool_policy(
        {
            "tool_name": name,
            "version": "1.0.0",
            "owning_feature": "FEAT-AGT-12",
            "receiver_domain": name.split(".", maxsplit=1)[0],
            "public_operation": name.split(".", 1)[1],
            "request_schema_id": f"{name}.request.v1",
            "result_schema_id": f"{name}.result.v1",
            "permission_class": "read_evidence",
            "side_effect_class": "read_only",
            "eligible_roles": (QUANT_ROLE_ID,),
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
            "role_id": QUANT_ROLE_ID,
            "role_version": "1.0.0",
            "permission_classes": ("read_evidence",),
            "allowed_tools": get_registered_tool_names(),
            "environment": "sandbox",
            "max_tool_calls": 8,
            "max_cost": Decimal("2.50"),
            "enabled": True,
        },
    )


def _control_plane():
    """Validate the mandate, roster, and policy registry for this role."""
    mandate = build_quantitative_mandate()
    registry = get_role_registry(mandate, (build_quantitative_role_manifest(),), NOW)
    tools, policies = validate_policy_registry(
        mandate,
        tuple(_tool(name) for name in get_registered_tool_names()),
        (_policy(),),
    )
    return mandate, registry, tools, policies


def test_quantitative_analyst_traverses_the_full_governed_path() -> None:
    # 1. Mandate and roster validate, and the prompt hash chain holds.
    mandate, registry, tools, policies = _control_plane()
    assert validate_firm_mandate(mandate, NOW) is mandate
    manifest = resolve_role_manifest(registry, QUANT_ROLE_ID)
    assert set(manifest.tools) == set(get_registered_tool_names())
    assert set(tools) == set(get_registered_tool_names())

    # 2. The run grounds every estimator through authorized tool calls.
    port, runtime = _Port(), _Runtime()
    audit = build_in_memory_memory_store()
    result = analyze_quantitative_evidence(
        registry,
        _task(),
        mandate,
        policies[QUANT_ROLE_ID],
        tools,
        port,
        runtime,
        _profile(),
        {ref: dict(body) for ref, body in EVIDENCE.items()},
        ("sharpe_ratio",),
        {"sharpe_ratio": 0.42},
        512,
        40,
        request_scope=dict(SCOPE),
        audit_store=audit,
        at_time=NOW,
    )

    assert result.status == "ok"
    payload = result.payload
    assert payload is not None
    assert payload.sample_size == "512"
    assert payload.multiple_testing_exposure == "40"
    assert payload.dataset_hash == DATASET_HASH
    assert set(payload.uncertainty) == set(payload.findings)
    assert set(payload.estimators) == set(payload.findings)
    assert (
        payload.estimators["risk_adjusted_return"] == CATALOG["sharpe_ratio"]["formula"]
    )

    # 3. Every tool call is audited, and provenance ties back to the prompt.
    assert port.calls == ["definition:sharpe_ratio", "floors"]
    assert len(retrieve_memory(audit, "audit", TASK_ID, at_time=NOW)) == 2
    assert result.provenance.base_prompt_hash == manifest.base_prompt_hash


def test_quantitative_analyst_has_no_broker_or_provider_reach() -> None:
    # The mandate validator rejects any broker tool outright, so this role
    # cannot be given one even by a mistaken mandate.
    mandate = build_quantitative_mandate(
        tool_scopes={"brokers.place_order": "read_evidence"},
    )
    with pytest.raises(ValueError, match="Brokers"):
        validate_firm_mandate(mandate, NOW)


def test_the_sample_floor_gates_before_the_model_across_the_control_plane() -> None:
    mandate, registry, tools, policies = _control_plane()
    runtime = _Runtime()
    result = analyze_quantitative_evidence(
        registry,
        _task(),
        mandate,
        policies[QUANT_ROLE_ID],
        tools,
        _Port(minimum_statistical="5000"),
        runtime,
        _profile(),
        {ref: dict(body) for ref, body in EVIDENCE.items()},
        ("sharpe_ratio",),
        {"sharpe_ratio": 0.42},
        512,
        40,
        request_scope=dict(SCOPE),
        at_time=NOW,
    )
    assert result.status == "refused"
    assert result.reasons == ("INSUFFICIENT_SAMPLE",)
    # The model was never reached: the catalog floor gates interpretation.
    assert runtime.invocations == []
