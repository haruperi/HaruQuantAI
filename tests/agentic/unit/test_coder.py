"""Unit tests for FEAT-AGT-16 Governed Code Generation and Sandbox.

Covers FR-AGENTIC-046 (an authenticated specification and a fully attested
ephemeral, resource-bounded, credential-free, network-denied environment),
FR-AGENTIC-047 (artefacts record files, dependencies, tests, hashes,
model/prompt/tool provenance, and complete search history), and
FR-AGENTIC-048 (the coder writes only to staging and nothing it writes is ever
imported, executed, registered, or deployed).
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from pathlib import Path

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
from app.agentic.agents.engineering.coder import (
    author_code_artifact,
    build_code_artifact,
    build_code_specification,
)
from app.agentic.agents.engineering.coder.agent import (
    AUTHORING_PERMISSION,
    PROMPT_PATH,
)
from app.agentic.agents.engineering.coder.artifact_store import (
    read_staged_file,
    stage_files,
    validate_relative_path,
    verify_staged_artifact,
)
from app.agentic.agents.engineering.coder.sandbox import (
    build_deterministic_sandbox,
    lease_refusal,
)
from app.agentic.agents.engineering.coder.schemas import (
    build_generated_file,
    build_sandbox_lease,
    derive_artifact_hash,
    forbidden_source_markers,
)
from app.agentic.agents.engineering.coder.tools import (
    INDICATOR_REGISTRY_TOOL,
    get_registered_tool_names,
)
from app.agentic.governance.registry import verify_prompt_artifact
from app.agentic.runtime import ModelOutcome
from app.utils import derive_stable_id, generate_id
from pydantic import ValidationError

from tests.agentic.fixtures import (
    NOW,
    build_coder_mandate,
    build_coder_role_manifest,
)

TASK_ID = derive_stable_id("id", "task-coder")
SCOPE = {"environment": "sandbox", "asset_class": "fx"}
SPEC_ID = derive_stable_id("id", "spec-coder")
PRINCIPAL = "operator-owner"

REGISTERED = {"ema": "1.0.0", "atr": "1.0.0", "rsi": "1.0.0"}

STRATEGY_SOURCE = '''"""Generated session-overlap momentum evaluator."""


class OverlapMomentumEvaluator:
    """Consumes precomputed indicators and emits signals."""

    strategy_id = "overlap-momentum"
    strategy_version = "0.1.0"
    module_path = "staging.overlap_momentum"

    def evaluate_signals(self, evidence, indicators, config, context):
        """Emit signals from precomputed indicators only."""
        del evidence, config, context
        return indicators
'''

TEST_SOURCE = '''"""Generated tests for the overlap momentum evaluator."""


def test_evaluator_declares_the_contract_fields():
    from staging.overlap_momentum import OverlapMomentumEvaluator

    assert OverlapMomentumEvaluator.strategy_id
'''

MODEL_OUTPUT = {
    "file:overlap_momentum.py": STRATEGY_SOURCE,
    "file:tests/test_overlap_momentum.py": TEST_SOURCE,
    "dependency:numpy": "2.4.6",
    "search_history": (
        "attempt 1: drafted the evaluator against SignalEvaluator\n"
        "attempt 2: added the warmup boundary test"
    ),
}


class StubAuth:
    """Structural stand-in for an authenticated principal."""

    def __init__(
        self,
        principal_id: str = PRINCIPAL,
        principal_type: str = "USER",
        permissions: tuple[str, ...] = (AUTHORING_PERMISSION,),
        tenant_or_environment: str = "sandbox",
    ) -> None:
        self.principal_id = principal_id
        self.principal_type = principal_type
        self.permissions = permissions
        self.tenant_or_environment = tenant_or_environment


class StubRegistryPort:
    """Deterministic Indicators registry port."""

    def __init__(self, registered: dict[str, str] | None = None) -> None:
        self.registered = REGISTERED if registered is None else registered
        self.calls: list[str] = []

    def list_registered_indicators(self):
        self.calls.append("list")
        return dict(self.registered)


class StubRuntime:
    """Deterministic runtime returning declared structured output."""

    def __init__(self, output=None, status="ok", reasons=()) -> None:
        # A refused outcome carries no output; the contract enforces that.
        if status != "ok":
            self.output = None
        else:
            self.output = MODEL_OUTPUT if output is None else output
        self.status = status
        self.reasons = reasons
        self.invocations: list[object] = []

    def execute_node(self, node_id, profile, invocation):
        del node_id
        self.invocations.append(invocation)
        return ModelOutcome.model_validate(
            {
                "invocation_id": invocation.invocation_id,
                "status": self.status,
                "output": self.output,
                "reasons": self.reasons,
                "provider": profile.provider,
                "model_identifier": profile.model_identifier,
                "tokens_used": 2_400,
                "latency_ms": 900,
                "cost": Decimal("0.12"),
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
            "objective": "Author a staged evaluator for the overlap thesis.",
            "input_refs": ("agentic.strategy_thesis:overlap",),
            "principal_id": PRINCIPAL,
            "scope": dict(SCOPE),
            "deadline_at": NOW + timedelta(minutes=45),
            "idempotency_key": "idem-coder",
            "budgets": {"cost": Decimal("3.00")},
        },
    )


def _specification(**overrides: object):
    fields: dict[str, object] = {
        "specification_id": SPEC_ID,
        "task_id": TASK_ID,
        "principal_id": PRINCIPAL,
        "artifact_kinds": ("strategy_evaluator",),
        "objective": "Implement a session-overlap momentum evaluator.",
        "target_contract": "strategy.signal_evaluator.v1",
        "acceptance_criteria": (
            "Consumes precomputed indicators only.",
            "Uses no value unavailable at decision time.",
        ),
        "required_indicators": ("ema", "atr"),
        "thesis_refs": ("agentic.strategy_thesis:overlap",),
        "environment": "sandbox",
    }
    fields.update(overrides)
    return build_code_specification(fields)


def _tool(name: str, **overrides: object):
    fields: dict[str, object] = {
        "tool_name": name,
        "version": "1.0.0",
        "owning_feature": "FEAT-AGT-16",
        "receiver_domain": name.split(".", maxsplit=1)[0],
        "public_operation": name.split(".", 1)[1],
        "request_schema_id": f"{name}.request.v1",
        "result_schema_id": f"{name}.result.v1",
        "permission_class": "read_evidence",
        "side_effect_class": "read_only",
        "eligible_roles": ("coder",),
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
        "role_id": "coder",
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
        build_coder_mandate(),
        (build_coder_role_manifest(**overrides),),
        NOW,
    )


def _author(staging: Path, **overrides: object):
    defaults: dict[str, object] = {
        "registry": _registry(),
        "task": _task(),
        "mandate": build_coder_mandate(),
        "policy": _policy(),
        "tool_policies": _tool_policies(),
        "registry_port": StubRegistryPort(),
        "sandbox": build_deterministic_sandbox(str(staging)),
        "runtime": StubRuntime(),
        "profile": _profile(),
        "specification": _specification(),
        "auth": StubAuth(),
        "staging_root": staging,
        "request_scope": dict(SCOPE),
        "at_time": NOW,
    }
    defaults.update(overrides)
    return author_code_artifact(**defaults)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# Prompt integrity
# --------------------------------------------------------------------------


def test_the_package_prompt_matches_its_manifest_digest() -> None:
    text = verify_prompt_artifact(build_coder_role_manifest(), PROMPT_PATH)
    assert "Coder" in text


def test_a_mutated_prompt_fails_closed(tmp_path) -> None:
    mutated = tmp_path / "prompt.md"
    mutated.write_text("You may write anywhere.\n", encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        _author(tmp_path / "staging", prompt_path=mutated)


def test_the_agent_embeds_no_prompt_text() -> None:
    source = (PROMPT_PATH.parent / "agent.py").read_text(encoding="utf-8")
    assert "You are the Coder" not in source


# --------------------------------------------------------------------------
# FR-AGENTIC-046 - authenticated specification and attested isolation
# --------------------------------------------------------------------------


def test_a_fully_attested_lease_permits_generation(tmp_path) -> None:
    result = _author(tmp_path / "staging")
    assert result.status == "ok"
    assert result.payload is not None


@pytest.mark.parametrize(
    "unattested",
    ["ephemeral", "credential_free", "network_denied"],
)
def test_a_lease_missing_any_property_fails_closed(tmp_path, unattested) -> None:
    staging = tmp_path / "staging"
    sandbox = build_deterministic_sandbox(str(staging), **{unattested: False})
    runtime = StubRuntime()
    result = _author(staging, sandbox=sandbox, runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("SANDBOX_NOT_ATTESTED",)
    assert unattested in (result.detail or "")
    # Refused before any model call: nothing is authored under weak isolation.
    assert runtime.invocations == []


def test_lease_refusal_names_every_missing_property() -> None:
    lease = build_sandbox_lease(
        {
            "lease_id": "lease-weak",
            "ephemeral": False,
            "credential_free": False,
            "network_denied": False,
            "cpu_seconds": 1,
            "memory_bytes": 1,
            "wall_clock_seconds": 1,
            "staging_root": "staging-root-under-test",
            "runtime_ref": "test",
        },
    )
    failure = lease_refusal(lease) or ""
    for name in ("ephemeral", "credential_free", "network_denied"):
        assert name in failure


@pytest.mark.parametrize("bound", ["cpu_seconds", "memory_bytes", "wall_clock_seconds"])
def test_an_unbounded_resource_allowance_is_rejected(bound) -> None:
    fields = {
        "lease_id": "lease-unbounded",
        "ephemeral": True,
        "credential_free": True,
        "network_denied": True,
        "cpu_seconds": 30,
        "memory_bytes": 1024,
        "wall_clock_seconds": 60,
        "staging_root": "staging-root-under-test",
        "runtime_ref": "test",
    }
    with pytest.raises(ValidationError, match="must be positive"):
        build_sandbox_lease({**fields, bound: 0})


def test_the_lease_is_closed_after_generation(tmp_path) -> None:
    staging = tmp_path / "staging"
    sandbox = build_deterministic_sandbox(str(staging))
    _author(staging, sandbox=sandbox)
    assert sandbox.opened == sandbox.closed  # type: ignore[attr-defined]
    assert len(sandbox.closed) == 1  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("auth_override", "fragment"),
    [
        ({"principal_type": "SERVICE_ACCOUNT"}, "human principal"),
        ({"permissions": ()}, AUTHORING_PERMISSION),
        ({"principal_id": "someone-else"}, "different principal"),
        ({"tenant_or_environment": "production"}, "environment"),
    ],
)
def test_an_unauthenticated_specification_is_refused(
    tmp_path,
    auth_override,
    fragment,
) -> None:
    runtime = StubRuntime()
    result = _author(
        tmp_path / "staging",
        auth=StubAuth(**auth_override),
        runtime=runtime,
    )
    assert result.status == "refused"
    assert result.reasons == ("SPECIFICATION_NOT_AUTHENTICATED",)
    assert fragment in (result.detail or "")
    assert runtime.invocations == []


def test_an_unauthorised_artefact_kind_is_refused(tmp_path) -> None:
    runtime = StubRuntime()
    result = _author(
        tmp_path / "staging",
        kind="indicator_candidate",
        runtime=runtime,
    )
    assert result.status == "refused"
    assert result.reasons == ("ARTIFACT_KIND_NOT_AUTHORISED",)
    assert runtime.invocations == []


# --------------------------------------------------------------------------
# FR-AGENTIC-047 - the manifest is complete or the artefact does not exist
# --------------------------------------------------------------------------


def test_the_artefact_records_its_full_provenance(tmp_path) -> None:
    artifact = _author(tmp_path / "staging").payload
    assert len(artifact.files) == 2
    assert dict(artifact.dependencies) == {"numpy": "2.4.6"}
    assert artifact.tests == ("tests/test_overlap_momentum.py",)
    assert artifact.tool_refs == (INDICATOR_REGISTRY_TOOL,)
    assert len(artifact.search_history) == 2
    assert artifact.model_profile_id == "profile-market-analysis-a"
    assert artifact.base_prompt_hash
    assert artifact.composite_instruction_hash
    assert artifact.artifact_hash


def test_every_file_carries_a_digest_of_its_own_content(tmp_path) -> None:
    artifact = _author(tmp_path / "staging").payload
    for generated in artifact.files:
        assert generated.content_hash
        assert generated.byte_count == len(generated.content.encode("utf-8"))


def test_a_file_whose_digest_does_not_describe_it_is_rejected() -> None:
    generated = build_generated_file("a.py", "x = 1\n")
    with pytest.raises(ValidationError, match="content_hash does not describe"):
        generated.model_copy(update={"content": "x = 2\n"}).model_validate(
            {
                **generated.model_dump(),
                "content": "x = 2\n",
            },
        )


@pytest.mark.parametrize("field", ["tests", "search_history"])
def test_an_incomplete_manifest_is_unrepresentable(tmp_path, field) -> None:
    artifact = _author(tmp_path / "staging").payload
    with pytest.raises(ValidationError, match="is required"):
        build_code_artifact({**artifact.model_dump(), field: ()})


def test_an_artefact_with_no_files_is_unrepresentable(tmp_path) -> None:
    artifact = _author(tmp_path / "staging").payload
    with pytest.raises(ValidationError, match="at least one generated file"):
        build_code_artifact({**artifact.model_dump(), "files": ()})


def test_the_manifest_digest_covers_the_whole_manifest(tmp_path) -> None:
    artifact = _author(tmp_path / "staging").payload
    altered = {**artifact.model_dump(), "search_history": ("attempt 1: nothing",)}
    assert derive_artifact_hash(altered) != artifact.artifact_hash


def test_generating_no_files_is_refused(tmp_path) -> None:
    empty = {"dependency:numpy": "2.4.6", "search_history": "attempt 1: gave up"}
    result = _author(tmp_path / "staging", runtime=StubRuntime(output=empty))
    assert result.status == "refused"
    assert result.reasons == ("NO_FILES_GENERATED",)


def test_a_model_refusal_is_propagated(tmp_path) -> None:
    runtime = StubRuntime(status="refused", reasons=("SPECIFICATION_AMBIGUOUS",))
    result = _author(tmp_path / "staging", runtime=runtime)
    assert result.status == "refused"
    assert result.reasons == ("SPECIFICATION_AMBIGUOUS",)
    assert result.payload is None


def test_storage_usage_reflects_what_was_staged(tmp_path) -> None:
    result = _author(tmp_path / "staging")
    expected = sum(item.byte_count for item in result.payload.files)
    assert result.budget_usage.storage_bytes == expected


# --------------------------------------------------------------------------
# FR-AGENTIC-048 - staging containment
# --------------------------------------------------------------------------

HOSTILE_PATHS = [
    "/etc/passwd",
    "//server/share/x.py",
    "C:/Windows/System32/evil.py",
    "C:evil.py",
    "~/.ssh/authorized_keys",
    "../escape.py",
    "a/../../escape.py",
    "./a.py",
    "a/./b.py",
    "a\\b.py",
    "evil.py:stream",
    "CON.py",
    "nul.py",
    "com1.py",
    "LPT9.py",
    "aux",
    "trailing.py.",
    "trailing.py ",
    "a/b/c/d/e/f/g/h/i.py",
    "no_suffix",
    "config.yaml",
    "shell.sh",
    "run.exe",
    "",
    "   ",
    "line\nbreak.py",
    "null\0byte.py",
]


@pytest.mark.parametrize("candidate", HOSTILE_PATHS)
def test_a_hostile_staging_path_is_rejected(candidate) -> None:
    assert validate_relative_path(candidate) is not None, candidate


@pytest.mark.parametrize(
    "candidate",
    ["a.py", "pkg/a.py", "tests/test_a.py", "README.md", "pyproject.toml"],
)
def test_an_ordinary_staging_path_is_accepted(candidate) -> None:
    assert validate_relative_path(candidate) is None, candidate


@pytest.mark.parametrize("candidate", HOSTILE_PATHS)
def test_staging_refuses_to_write_a_hostile_path(tmp_path, candidate) -> None:
    staging = tmp_path / "staging"
    # A hostile path is rejected before the file is even constructed in most
    # cases; where it is representable, staging must still refuse it.
    try:
        generated = build_generated_file(candidate, "x = 1\n")
    except ValidationError:
        return
    with pytest.raises(ValueError, match="refusing staging path"):
        stage_files(staging, "artifact-a", (generated,))
    assert not any(tmp_path.rglob("passwd"))
    assert not any(tmp_path.rglob("escape.py"))


def test_files_are_written_under_the_artefact_directory(tmp_path) -> None:
    staging = tmp_path / "staging"
    artifact = _author(staging).payload
    written = sorted(
        path.relative_to(staging).as_posix()
        for path in staging.rglob("*")
        if path.is_file()
    )
    assert written == [
        f"{artifact.artifact_id}/overlap_momentum.py",
        f"{artifact.artifact_id}/tests/test_overlap_momentum.py",
    ]


def test_nothing_is_written_outside_the_staging_root(tmp_path) -> None:
    staging = tmp_path / "staging"
    sentinel = tmp_path / "outside"
    sentinel.mkdir()
    _author(staging)
    assert list(sentinel.iterdir()) == []


def test_staged_content_matches_the_recorded_digests(tmp_path) -> None:
    staging = tmp_path / "staging"
    artifact = _author(staging).payload
    assert verify_staged_artifact(staging, artifact) == ()


def test_drifted_staged_content_is_detected(tmp_path) -> None:
    staging = tmp_path / "staging"
    artifact = _author(staging).payload
    target = staging / artifact.artifact_id / "overlap_momentum.py"
    target.write_text("x = 'tampered'\n", encoding="utf-8")
    assert verify_staged_artifact(staging, artifact) == ("overlap_momentum.py",)


def test_a_symlinked_staging_target_is_refused(tmp_path) -> None:
    staging = tmp_path / "staging"
    outside = tmp_path / "outside"
    outside.mkdir()
    (staging / "artifact-a").mkdir(parents=True)
    try:
        (staging / "artifact-a" / "pkg").symlink_to(outside, target_is_directory=True)
    except OSError, NotImplementedError:
        pytest.skip("symlink creation is not permitted in this environment")
    generated = build_generated_file("pkg/a.py", "x = 1\n")
    with pytest.raises(ValueError, match="refusing staging path"):
        stage_files(staging, "artifact-a", (generated,))
    assert list(outside.iterdir()) == []


def test_an_unsafe_artefact_identity_is_refused(tmp_path) -> None:
    generated = build_generated_file("a.py", "x = 1\n")
    with pytest.raises(ValueError, match="not a safe directory name"):
        stage_files(tmp_path / "staging", "../escape", (generated,))


def test_reading_a_hostile_staged_path_returns_nothing(tmp_path) -> None:
    assert read_staged_file(tmp_path, "artifact-a", "../../etc/passwd") is None


def test_the_package_never_imports_executes_or_registers() -> None:
    package = PROMPT_PATH.parent
    forbidden = (
        "importlib",
        "__import__",
        "exec(",
        "eval(",
        "compile(",
        "subprocess",
        "sys.path",
        "register_strategy_version",
    )
    for module in package.glob("*.py"):
        source = module.read_text(encoding="utf-8")
        # The marker list in `schemas.py` names these deliberately; it is data
        # describing what to look for, never a call.
        if module.name == "schemas.py":
            continue
        for marker in forbidden:
            assert marker not in source, f"{module.name} names {marker}"


def test_forbidden_source_markers_are_reported_for_review() -> None:
    assert forbidden_source_markers(STRATEGY_SOURCE) == ()
    flagged = forbidden_source_markers("import os\nos.system('rm -rf /')\n")
    assert "os.system" in flagged


# --------------------------------------------------------------------------
# Indicator gap detection and promotion readiness
# --------------------------------------------------------------------------


def test_registered_indicators_come_from_the_receiver(tmp_path) -> None:
    port = StubRegistryPort()
    result = _author(tmp_path / "staging", registry_port=port)
    assert result.status == "ok"
    assert port.calls == ["list"]
    assert result.payload.unregistered_indicators == ()
    assert result.payload.promotion_status == "ready"


def test_a_missing_indicator_is_refused_when_candidates_are_unauthorised(
    tmp_path,
) -> None:
    runtime = StubRuntime()
    result = _author(
        tmp_path / "staging",
        specification=_specification(required_indicators=("ema", "kalman_slope")),
        runtime=runtime,
    )
    assert result.status == "refused"
    assert result.reasons == ("INDICATOR_NOT_REGISTERED",)
    assert "kalman_slope" in (result.detail or "")
    assert runtime.invocations == []


def test_a_missing_indicator_proceeds_when_candidates_are_authorised(
    tmp_path,
) -> None:
    result = _author(
        tmp_path / "staging",
        specification=_specification(
            artifact_kinds=("indicator_candidate", "strategy_evaluator"),
            required_indicators=("ema", "kalman_slope"),
        ),
    )
    assert result.status == "ok"
    assert result.payload.unregistered_indicators == ("kalman_slope",)
    assert result.payload.promotion_status == "blocked_on_indicator_merge"


def test_an_artefact_blocked_on_an_indicator_cannot_claim_readiness(
    tmp_path,
) -> None:
    artifact = _author(
        tmp_path / "staging",
        specification=_specification(
            artifact_kinds=("indicator_candidate", "strategy_evaluator"),
            required_indicators=("ema", "kalman_slope"),
        ),
    ).payload
    with pytest.raises(ValidationError, match="cannot be ready"):
        build_code_artifact({**artifact.model_dump(), "promotion_status": "ready"})


def test_unregistered_indicators_must_be_required_indicators(tmp_path) -> None:
    artifact = _author(tmp_path / "staging").payload
    with pytest.raises(ValidationError, match="does not require"):
        build_code_artifact(
            {**artifact.model_dump(), "unregistered_indicators": ("ghost",)},
        )


def test_a_failing_sandbox_run_blocks_readiness(tmp_path) -> None:
    staging = tmp_path / "staging"
    sandbox = build_deterministic_sandbox(
        str(staging),
        failing_paths=("overlap_momentum.py",),
    )
    artifact = _author(staging, sandbox=sandbox).payload
    assert artifact.sandbox_result.compiled is False
    assert artifact.promotion_status == "blocked_on_tests"
    with pytest.raises(ValidationError, match="tests are not clean"):
        build_code_artifact({**artifact.model_dump(), "promotion_status": "ready"})


def test_a_denied_registry_tool_stops_the_run_before_the_model(tmp_path) -> None:
    port = StubRegistryPort()
    runtime = StubRuntime()
    result = _author(
        tmp_path / "staging",
        registry_port=port,
        runtime=runtime,
        tool_policies=_tool_policies(enabled=False),
    )
    assert result.status == "refused"
    assert result.reasons == ("REGISTRY_TOOL_DENIED",)
    assert port.calls == []
    assert runtime.invocations == []


def test_an_unregistered_registry_tool_is_refused(tmp_path) -> None:
    result = _author(tmp_path / "staging", tool_policies={})
    assert result.status == "refused"
    assert result.reasons == ("REGISTRY_TOOL_DENIED",)


def test_tool_calls_are_audited_when_a_store_is_injected(tmp_path) -> None:
    store = build_in_memory_memory_store()
    _author(tmp_path / "staging", audit_store=store)
    assert len(retrieve_memory(store, "audit", TASK_ID, at_time=NOW)) == 1


def test_registered_tool_names_are_stable() -> None:
    assert get_registered_tool_names() == (INDICATOR_REGISTRY_TOOL,)


def test_the_specification_and_registry_are_trusted_context(tmp_path) -> None:
    runtime = StubRuntime()
    _author(tmp_path / "staging", runtime=runtime)
    invocation = runtime.invocations[0]
    assert invocation.trusted_context["artifact_kind"] == "strategy_evaluator"
    assert "ema" in invocation.trusted_context["registered_indicators"]
    assert any(key.startswith("thesis:") for key in invocation.untrusted_evidence)


def test_a_specification_authorising_nothing_is_rejected() -> None:
    with pytest.raises(ValidationError, match="at least one artefact kind"):
        _specification(artifact_kinds=())
