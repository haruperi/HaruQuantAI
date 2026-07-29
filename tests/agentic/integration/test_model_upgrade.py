"""Integration evidence for WF-AGT-009 - Model upgrade.

Exercises the documented workflow end to end across governance, runtime, and
orchestration: an Owner-requested profile change is compatibility-checked,
gated, and either activated or refused, and the surrounding governed run
continues to fail closed while an unevaluated profile is in play.

Requirement sequence: FR-AGENTIC-007 -> FR-AGENTIC-008 -> FR-AGENTIC-009.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from app.agentic import (
    build_agent_task,
    build_deterministic_adk_runtime,
    build_deterministic_model_gateway,
    build_in_memory_workflow_store,
    build_model_invocation,
    build_model_profile,
    build_workflow_definition,
    get_required_upgrade_gates,
    get_role_registry,
    invoke_model,
    resolve_role_manifest,
    submit_task,
    validate_model_upgrade,
)
from app.agentic.runtime import ModelOutcome
from app.utils import canonical_digest, derive_stable_id, generate_id

from tests.agentic.fixtures import (
    FALLBACK_PROFILE_ID,
    MODEL_PROFILE_ID,
    NOW,
    TECHNICAL_ROLE_ID,
    build_sandbox_mandate,
    build_technical_manifest,
)

INVOCATION_ID = "inv-upgrade-0001"


def _profile(profile_id: str, model_identifier: str, **overrides: object):
    fields: dict[str, object] = {
        "profile_id": profile_id,
        "version": "1.0.0",
        "provider": "gemini",
        "model_identifier": model_identifier,
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
    }
    fields.update(overrides)
    return build_model_profile(fields)


def _invocation(**overrides: object):
    fields: dict[str, object] = {
        "invocation_id": INVOCATION_ID,
        "task_id": "task-upgrade",
        "role_id": TECHNICAL_ROLE_ID,
        "composite_instruction_hash": canonical_digest("composite"),
        "trusted_context": {"instrument": "EURUSD"},
        "untrusted_evidence": {"headline": "Rates unchanged."},
        "max_output_tokens": 2_000,
        "seed": 1,
    }
    fields.update(overrides)
    return build_model_invocation(fields)


def _outcome(**overrides: object) -> ModelOutcome:
    fields: dict[str, object] = {
        "invocation_id": INVOCATION_ID,
        "status": "ok",
        "output": {"trend": "up"},
        "reasons": (),
        "provider": "gemini",
        "model_identifier": "gemini-3.0-pro-002",
        "tokens_used": 900,
        "latency_ms": 700,
        "cost": Decimal("0.01"),
    }
    fields.update(overrides)
    return ModelOutcome.model_validate(fields)


def test_wf_agt_009_model_upgrade_activates_only_after_every_gate_passes() -> None:
    # 1. The registry resolves the role and the model profile it pins.
    registry = get_role_registry(
        build_sandbox_mandate(enabled_roles=(TECHNICAL_ROLE_ID,)),
        (build_technical_manifest(),),
        NOW,
    )
    manifest = resolve_role_manifest(registry, TECHNICAL_ROLE_ID)
    assert manifest.model_profile_id == MODEL_PROFILE_ID

    current = _profile(MODEL_PROFILE_ID, "gemini-3.0-pro-002")

    # 2. The pinned profile serves a governed invocation through the port.
    runtime = build_deterministic_adk_runtime(
        build_deterministic_model_gateway({INVOCATION_ID: _outcome()}),
    )
    served = runtime.execute_node("collect_briefs", current, _invocation())
    assert served.status == "ok"

    # 3. An Owner-requested change is refused while evidence is missing.
    candidate = _profile(FALLBACK_PROFILE_ID, "gemini-3.1-pro-001")
    assert validate_model_upgrade(current, candidate, {}).approved is False

    # 4. It stays refused while any single gate fails.
    gates = dict.fromkeys(get_required_upgrade_gates(), True)
    gates["shadow_comparison"] = False
    refused = validate_model_upgrade(current, candidate, gates)
    assert refused.approved is False
    assert refused.failed_gates == ("shadow_comparison",)

    # 5. It activates only once every gate passes.
    approved = validate_model_upgrade(
        current,
        candidate,
        dict.fromkeys(get_required_upgrade_gates(), True),
    )
    assert approved.approved is True
    assert approved.candidate_profile_id == FALLBACK_PROFILE_ID


def test_wf_agt_009_unevaluated_profile_cannot_serve_a_governed_run() -> None:
    shadow = _profile(
        FALLBACK_PROFILE_ID,
        "gemini-3.1-pro-001",
        evaluation_state="shadow",
    )
    gateway = build_deterministic_model_gateway({INVOCATION_ID: _outcome()})
    with pytest.raises(ValueError, match="only an evaluated profile"):
        invoke_model(gateway, shadow, _invocation())


def test_wf_agt_009_substitution_is_refused_inside_a_governed_run() -> None:
    # A governed run is submitted, then the provider serves a different model.
    store = build_in_memory_workflow_store()
    definition = build_workflow_definition(
        {
            "workflow_name": "model_upgrade",
            "version": "1.0.0",
            "nodes": ("evaluate",),
            "entry_node": "evaluate",
            "limits_profile_id": "agentic-limits-sandbox-v1",
            "max_fan_out": 1,
            "max_rounds": 1,
            "max_retries": 0,
            "deadline_seconds": 600,
            "permits_human_wait": False,
        },
    )
    task = build_agent_task(
        {
            "created_at": NOW,
            "request_id": generate_id("req"),
            "workflow_id": generate_id("wf"),
            "correlation_id": generate_id("cor"),
            "causation_id": None,
            "task_id": derive_stable_id("id", "task-upgrade-run"),
            "workflow_name": "model_upgrade",
            "workflow_version": "1.0.0",
            "objective": "Evaluate a proposed model-profile change.",
            "input_refs": ("evidence-shadow-run",),
            "principal_id": "operator-owner",
            "scope": {"environment": "sandbox"},
            "deadline_at": NOW + timedelta(minutes=10),
            "idempotency_key": "idem-upgrade-0001",
            "budgets": {"cost": Decimal("1.00")},
        },
    )
    run = submit_task(store, definition, task, at_time=NOW)
    assert run.state == "submitted"
    assert len(store.list_checkpoints(task.task_id)) == 1

    current = _profile(MODEL_PROFILE_ID, "gemini-3.0-pro-002")
    substituting = build_deterministic_model_gateway(
        {INVOCATION_ID: _outcome(model_identifier="gemini-3.0-flash-001")},
    )
    with pytest.raises(ValueError, match="model substitution detected"):
        invoke_model(substituting, current, _invocation())
