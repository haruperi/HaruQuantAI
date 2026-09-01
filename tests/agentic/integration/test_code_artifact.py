"""Integration evidence for FEAT-AGT-16 across the governed control plane.

Exercises the full path a code-authoring feature must traverse: mandate and
roster validation, policy-registry validation, human authentication, sandbox
lease attestation, deny-by-default tool authorization, deterministic registry
gap detection, and a content-addressed staged artefact.

This covers `WF-AGT-005` steps 1 through 5. The workflow itself stays
`Missing` until `open_sandbox` and `stage_code_artifact` are exposed on the
Agentic public root, which the registry assigns to `FEAT-AGT-22`.

The sandbox is the in-process double and the registry arrives as an injected
port, so nothing is executed and no receiver is reached. What is exercised is
the governance path and the staging containment, both of which are real.
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
from app.agentic.agents.engineering.coder import (
    author_code_artifact,
    build_code_specification,
)
from app.agentic.agents.engineering.coder.agent import AUTHORING_PERMISSION
from app.agentic.agents.engineering.coder.artifact_store import verify_staged_artifact
from app.agentic.agents.engineering.coder.sandbox import build_deterministic_sandbox
from app.agentic.agents.engineering.coder.tools import get_registered_tool_names
from app.agentic.runtime import ModelOutcome
from app.kernel.identity import derive_stable_id, generate_id

from tests.agentic.fixtures import (
    CODER_ROLE_ID,
    NOW,
    build_coder_mandate,
    build_coder_role_manifest,
)

TASK_ID = derive_stable_id("id", "task-coder-integration")
SCOPE = {"environment": "sandbox", "asset_class": "fx"}
PRINCIPAL = "operator-owner"

REGISTERED = {"ema": "1.0.0", "atr": "1.0.0"}

SOURCE = '''"""Generated evaluator."""


class Evaluator:
    """Consumes precomputed indicators."""

    strategy_id = "integration-evaluator"

    def evaluate_signals(self, evidence, indicators, config, context):
        """Emit signals from precomputed indicators only."""
        del evidence, config, context
        return indicators
'''

TEST_SOURCE = '''"""Generated tests."""


def test_declares_identity():
    assert True
'''

OUTPUT = {
    "file:evaluator.py": SOURCE,
    "file:tests/test_evaluator.py": TEST_SOURCE,
    "dependency:numpy": "2.4.6",
    "search_history": "attempt 1: drafted against SignalEvaluator",
}


class _Auth:
    """Structural stand-in for an authenticated human principal."""

    principal_id = PRINCIPAL
    principal_type = "USER"
    permissions = (AUTHORING_PERMISSION,)
    tenant_or_environment = "sandbox"


class _RegistryPort:
    """Deterministic Indicators registry port."""

    def __init__(self, registered: dict[str, str] | None = None) -> None:
        self.registered = REGISTERED if registered is None else registered
        self.calls: list[str] = []

    def list_registered_indicators(self):
        self.calls.append("list")
        return dict(self.registered)


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
                "output": dict(OUTPUT),
                "reasons": (),
                "provider": profile.provider,
                "model_identifier": profile.model_identifier,
                "tokens_used": 1_800,
                "latency_ms": 700,
                "cost": Decimal("0.09"),
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
            "workflow_name": "author_code_artifact",
            "workflow_version": "1.0.0",
            "objective": "Author a staged evaluator.",
            "input_refs": ("agentic.strategy_thesis:overlap",),
            "principal_id": PRINCIPAL,
            "scope": dict(SCOPE),
            "deadline_at": NOW + timedelta(minutes=45),
            "idempotency_key": "idem-coder-integration",
            "budgets": {"cost": Decimal("3.00")},
        },
    )


def _specification(**overrides: object):
    fields: dict[str, object] = {
        "specification_id": derive_stable_id("id", "spec-integration"),
        "task_id": TASK_ID,
        "principal_id": PRINCIPAL,
        "artifact_kinds": ("strategy_evaluator",),
        "objective": "Implement an evaluator for the overlap thesis.",
        "target_contract": "strategy.signal_evaluator.v1",
        "acceptance_criteria": ("Consumes precomputed indicators only.",),
        "required_indicators": ("ema", "atr"),
        "environment": "sandbox",
    }
    fields.update(overrides)
    return build_code_specification(fields)


def _tool(name: str):
    return build_tool_policy(
        {
            "tool_name": name,
            "version": "1.0.0",
            "owning_feature": "FEAT-AGT-16",
            "receiver_domain": name.split(".", maxsplit=1)[0],
            "public_operation": name.split(".", 1)[1],
            "request_schema_id": f"{name}.request.v1",
            "result_schema_id": f"{name}.result.v1",
            "permission_class": "read_evidence",
            "side_effect_class": "read_only",
            "eligible_roles": (CODER_ROLE_ID,),
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
            "role_id": CODER_ROLE_ID,
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
    mandate = build_coder_mandate()
    registry = get_role_registry(mandate, (build_coder_role_manifest(),), NOW)
    tools, policies = validate_policy_registry(
        mandate,
        tuple(_tool(name) for name in get_registered_tool_names()),
        (_policy(),),
    )
    return mandate, registry, tools, policies


def _author(staging, **overrides):
    """Author one artefact through the full governed path."""
    mandate, registry, tools, policies = _control_plane()
    defaults = {
        "registry": registry,
        "task": _task(),
        "mandate": mandate,
        "policy": policies[CODER_ROLE_ID],
        "tool_policies": tools,
        "registry_port": _RegistryPort(),
        "sandbox": build_deterministic_sandbox(str(staging)),
        "runtime": _Runtime(),
        "profile": _profile(),
        "specification": _specification(),
        "auth": _Auth(),
        "staging_root": staging,
        "request_scope": dict(SCOPE),
        "at_time": NOW,
    }
    defaults.update(overrides)
    return author_code_artifact(**defaults)


def test_coder_traverses_the_full_governed_path(tmp_path) -> None:
    # 1. Mandate and roster validate, and the prompt hash chain holds.
    mandate, registry, tools, _ = _control_plane()
    assert validate_firm_mandate(mandate, NOW) is mandate
    manifest = resolve_role_manifest(registry, CODER_ROLE_ID)
    assert set(manifest.tools) == set(get_registered_tool_names())
    assert set(tools) == set(get_registered_tool_names())

    # 2. Authoring proceeds under an authenticated human and an attested lease.
    staging = tmp_path / "staging"
    port = _RegistryPort()
    audit = build_in_memory_memory_store()
    result = _author(staging, registry_port=port, audit_store=audit)

    assert result.status == "ok"
    artifact = result.payload
    assert artifact is not None
    assert artifact.promotion_status == "ready"
    assert artifact.unregistered_indicators == ()

    # 3. Files exist on disk under the artefact directory and match digests.
    assert verify_staged_artifact(staging, artifact) == ()
    written = sorted(
        path.relative_to(staging).as_posix()
        for path in staging.rglob("*")
        if path.is_file()
    )
    assert written == [
        f"{artifact.artifact_id}/evaluator.py",
        f"{artifact.artifact_id}/tests/test_evaluator.py",
    ]

    # 4. The registry answer and the tool call are both recorded.
    assert port.calls == ["list"]
    assert len(retrieve_memory(audit, "audit", TASK_ID, at_time=NOW)) == 1
    assert result.provenance.base_prompt_hash == manifest.base_prompt_hash


def test_coder_has_no_broker_or_provider_reach() -> None:
    # The mandate validator rejects any broker tool outright, so this role
    # cannot be given one even by a mistaken mandate.
    mandate = build_coder_mandate(
        tool_scopes={"brokers.place_order": "read_evidence"},
    )
    with pytest.raises(ValueError, match="Brokers"):
        validate_firm_mandate(mandate, NOW)


def test_an_unattested_sandbox_stops_the_run_before_the_model(tmp_path) -> None:
    staging = tmp_path / "staging"
    runtime = _Runtime()
    result = _author(
        staging,
        sandbox=build_deterministic_sandbox(str(staging), network_denied=False),
        runtime=runtime,
    )
    assert result.status == "refused"
    assert result.reasons == ("SANDBOX_NOT_ATTESTED",)
    assert runtime.invocations == []
    assert not staging.exists() or not any(staging.rglob("*"))


def test_a_service_account_cannot_authorise_code_generation(tmp_path) -> None:
    class _ServiceAuth:
        principal_id = PRINCIPAL
        principal_type = "SERVICE_ACCOUNT"
        permissions = (AUTHORING_PERMISSION,)
        tenant_or_environment = "sandbox"

    staging = tmp_path / "staging"
    runtime = _Runtime()
    result = _author(staging, auth=_ServiceAuth(), runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("SPECIFICATION_NOT_AUTHENTICATED",)
    assert runtime.invocations == []


def test_an_unregistered_indicator_blocks_promotion_across_the_plane(
    tmp_path,
) -> None:
    staging = tmp_path / "staging"
    result = _author(
        staging,
        specification=_specification(
            artifact_kinds=("indicator_candidate", "strategy_evaluator"),
            required_indicators=("ema", "kalman_slope"),
        ),
    )
    assert result.status == "ok"
    artifact = result.payload
    assert artifact is not None
    assert artifact.unregistered_indicators == ("kalman_slope",)
    assert artifact.promotion_status == "blocked_on_indicator_merge"


def test_nothing_is_staged_outside_the_supplied_root(tmp_path) -> None:
    staging = tmp_path / "staging"
    neighbour = tmp_path / "neighbour"
    neighbour.mkdir()
    _author(staging)
    assert list(neighbour.iterdir()) == []
    assert staging.exists()
