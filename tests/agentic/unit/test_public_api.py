"""Unit tests for FEAT-AGT-22 Public Agentic API and Operator Control.

Covers FR-AGENTIC-064 (auth, explicit dependencies, request and correlation
IDs, bounded inputs, stable mapped failures), FR-AGENTIC-065 (seven operator
operations exposing no prompt, credential, or provider internal), and
FR-AGENTIC-066 (disablement rejects new work, settles active work by policy,
preserves audit evidence, and leaves deterministic safety untouched).
"""

from __future__ import annotations

import inspect
from dataclasses import MISSING, FrozenInstanceError, fields
from decimal import Decimal

import app.agentic as agentic_root
import pytest
from app.agentic import (
    build_agent_policy,
    build_in_memory_memory_store,
    build_in_memory_workflow_store,
    build_tool_policy,
    build_workflow_definition,
    get_role_registry,
    retrieve_memory,
    store_memory,
)
from app.agentic._settings import get_agentic_settings
from app.agentic.lifecycle import (
    build_in_memory_lifecycle_store,
    transition_artifact,
)
from app.agentic.operations import (
    REQUIRED_SPAN_KINDS,
    build_in_memory_operations_store,
    build_replay_request,
)
from app.agentic.operations.service import SPAN_KEY
from app.agentic.public_api import (
    FORBIDDEN_PAYLOAD_KEYS,
    OPERATOR_PERMISSIONS,
    READ_OPERATIONS,
    AgenticDependencies,
    OperatorOutcome,
    approve_agentic_handoff,
    build_agentic_dependencies,
    cancel_firm_run,
    disable_agentic,
    get_firm_audit,
    get_firm_run,
    get_operator_operations,
    quarantine_firm_agent,
    replay_firm_run,
    submit_firm_request,
)
from app.utils import derive_stable_id, generate_id
from pydantic import ValidationError

from tests.agentic.fixtures import NOW, build_technical_mandate

WORKFLOW_NAME = "firm_research_council"
WORKFLOW_VERSION = "1.0.0"
TASK_ID = derive_stable_id("id", "task-public-api")
ROLE_ID = "technical_analyst"
ARTIFACT_HASH = "sha256:artifact-public-api"

ALL_PERMISSIONS = tuple(sorted(set(OPERATOR_PERMISSIONS.values())))


class Operator:
    """An authenticated operator principal."""

    def __init__(
        self,
        principal_id: str = "operator-owner",
        principal_type: str = "USER",
        permissions: tuple[str, ...] = ALL_PERMISSIONS,
        tenant_or_environment: str = "sandbox",
    ) -> None:
        self.principal_id = principal_id
        self.principal_type = principal_type
        self.permissions = permissions
        self.tenant_or_environment = tenant_or_environment
        self.request_id = generate_id("req")
        self.workflow_id = generate_id("wf")
        self.correlation_id = generate_id("cor")


def _definition():
    return build_workflow_definition(
        {
            "workflow_name": WORKFLOW_NAME,
            "version": WORKFLOW_VERSION,
            "nodes": ("collect_briefs", "challenge", "synthesize"),
            "entry_node": "collect_briefs",
            "limits_profile_id": "agentic-limits-sandbox-v1",
            "max_fan_out": 4,
            "max_rounds": 1,
            "max_retries": 2,
            "deadline_seconds": 1_800,
            "permits_human_wait": True,
        },
    )


def _tool_policy(name: str = "data.get_market_data"):
    return build_tool_policy(
        {
            "tool_name": name,
            "version": "1.0.0",
            "owning_feature": "FEAT-AGT-22",
            "receiver_domain": name.split(".", maxsplit=1)[0],
            "public_operation": name.split(".", 1)[1],
            "request_schema_id": f"{name}.request.v1",
            "result_schema_id": f"{name}.result.v1",
            "permission_class": "read_evidence",
            "side_effect_class": "read_only",
            "eligible_roles": (ROLE_ID,),
            "scope": {"environment": "sandbox"},
            "idempotent": True,
            "requires_approval": False,
            "max_input_bytes": 8_192,
            "max_output_bytes": 1_048_576,
            "timeout_seconds": 30,
            "max_calls_per_task": 8,
            "enabled": True,
        },
    )


def _agent_policy():
    return build_agent_policy(
        {
            "role_id": ROLE_ID,
            "role_version": "1.0.0",
            "permission_classes": ("read_evidence",),
            "allowed_tools": ("data.get_market_data",),
            "environment": "sandbox",
            "max_tool_calls": 8,
            "max_cost": Decimal("2.50"),
            "enabled": True,
        },
    )


def _dependencies(*, enabled: bool = True, **overrides: object) -> AgenticDependencies:
    from tests.agentic.fixtures import build_technical_role_manifest

    mandate = build_technical_mandate()
    data: dict[str, object] = {
        "settings": get_agentic_settings(
            {
                "agentic_enabled": True,
                "agentic_mandate_path": "app/configs/agentic-mandate.json",
                "agentic_model_profiles": ("profile-market-analysis-a",),
                "agentic_limits_profile": "agentic-limits-sandbox-v1",
            }
            if enabled
            else {"agentic_enabled": False},
        ),
        "mandate": mandate,
        "registry": get_role_registry(
            mandate,
            (build_technical_role_manifest(),),
            NOW,
        ),
        "workflow_store": build_in_memory_workflow_store(),
        "memory_store": build_in_memory_memory_store(),
        "operations_store": build_in_memory_operations_store(),
        "lifecycle_store": build_in_memory_lifecycle_store(),
        "definitions": {WORKFLOW_NAME: _definition()},
        "agent_policies": {ROLE_ID: _agent_policy()},
        "tool_policies": {"data.get_market_data": _tool_policy()},
    }
    data.update(overrides)
    return build_agentic_dependencies(**data)  # type: ignore[arg-type]


def _submit(dependencies=None, auth=None, **overrides: object) -> OperatorOutcome:
    data: dict[str, object] = {
        "workflow_name": WORKFLOW_NAME,
        "objective": "Assess EURUSD H1 trend evidence.",
        "input_refs": ("evidence-market-1",),
        "idempotency_key": "idem-public-api",
        "at_time": NOW,
    }
    data.update(overrides)
    return submit_firm_request(
        dependencies or _dependencies(),
        auth or Operator(),
        **data,  # type: ignore[arg-type]
    )


def _emit(memory, task_id: str):
    for kind in sorted(REQUIRED_SPAN_KINDS):
        content = {SPAN_KEY: kind, "detail": f"the {kind} span was emitted"}
        if kind == "cost":
            content["cost"] = "0.40"
        store_memory(
            memory,
            "audit",
            task_id,
            ROLE_ID,
            content,
            {"environment": "sandbox"},
            "audit-730d",
            at_time=NOW,
        )
    return memory


# --------------------------------------------------------------------------
# FR-AGENTIC-064 - auth, explicit dependencies, IDs, bounds, mapped failures
# --------------------------------------------------------------------------


def test_the_dependency_record_requires_every_port() -> None:
    required = {field.name for field in fields(AgenticDependencies)}
    assert required == {
        "settings",
        "mandate",
        "registry",
        "workflow_store",
        "memory_store",
        "operations_store",
        "lifecycle_store",
        "definitions",
        "agent_policies",
        "tool_policies",
    }
    # No field carries a default, so a partially wired firm cannot be built.
    for field in fields(AgenticDependencies):
        assert field.default is MISSING, field.name
        assert field.default_factory is MISSING, field.name
    with pytest.raises(TypeError):
        AgenticDependencies()  # type: ignore[call-arg]


def test_the_dependency_record_is_frozen() -> None:
    dependencies = _dependencies()
    with pytest.raises(FrozenInstanceError):
        dependencies.settings = None  # type: ignore[misc]


def test_every_operation_takes_dependencies_and_auth_first() -> None:
    for name in get_operator_operations():
        operation = getattr(agentic_root, _root_name(name), None)
        if operation is None:
            continue
        parameters = list(inspect.signature(operation).parameters)
        assert parameters[:2] == ["dependencies", "auth"], name


def _root_name(operation: str) -> str:
    """Return the root export name for one operator operation."""
    return operation


def test_the_outcome_carries_the_callers_trace_identifiers() -> None:
    auth = Operator()
    outcome = _submit(auth=auth)
    assert outcome.request_id == auth.request_id
    assert outcome.correlation_id == auth.correlation_id
    assert outcome.principal_id == auth.principal_id


def test_a_missing_permission_is_refused() -> None:
    outcome = _submit(auth=Operator(permissions=("agentic:read_run",)))
    assert outcome.status == "refused"
    assert outcome.reasons == ("PERMISSION_DENIED",)


def test_a_context_for_another_environment_is_refused() -> None:
    outcome = _submit(auth=Operator(tenant_or_environment="production"))
    assert outcome.status == "refused"
    assert outcome.reasons == ("ENVIRONMENT_MISMATCH",)


def test_an_unregistered_workflow_is_refused() -> None:
    outcome = _submit(workflow_name="not_a_workflow")
    assert outcome.status == "refused"
    assert outcome.reasons == ("WORKFLOW_NOT_REGISTERED",)


def test_an_unexpected_failure_is_mapped_not_raised() -> None:
    # An empty objective is rejected by the task contract; the boundary maps
    # it rather than letting a validation error escape to the operator.
    outcome = _submit(objective="")
    assert outcome.status == "failed"
    assert outcome.reasons
    assert outcome.detail


def test_no_public_operation_lets_an_exception_escape() -> None:
    dependencies = _dependencies()
    auth = Operator()
    calls = (
        lambda: get_firm_run(dependencies, auth, "run-missing", at_time=NOW),
        lambda: cancel_firm_run(dependencies, auth, "run-missing", at_time=NOW),
        lambda: approve_agentic_handoff(
            dependencies,
            auth,
            ARTIFACT_HASH,
            "artifact-a",
            "approving",
            at_time=NOW,
        ),
        lambda: get_firm_audit(dependencies, auth, TASK_ID, "run-a", at_time=NOW),
    )
    for call in calls:
        outcome = call()
        assert outcome.status in {"refused", "failed"}


def test_a_successful_submission_reserves_a_run() -> None:
    outcome = _submit()
    assert outcome.status == "ok"
    assert outcome.payload["run_id"]
    assert outcome.payload["workflow_name"] == WORKFLOW_NAME


# --------------------------------------------------------------------------
# FR-AGENTIC-065 - seven operations, no prompts, credentials, or internals
# --------------------------------------------------------------------------


def test_seven_operator_operations_are_registered() -> None:
    operations = set(get_operator_operations())
    assert {
        "submit_firm_request",
        "get_firm_run",
        "cancel_firm_run",
        "approve_agentic_handoff",
        "replay_firm_run",
        "quarantine_firm_agent",
        "get_firm_audit",
    } <= operations


def test_every_operation_declares_a_permission() -> None:
    for operation in get_operator_operations():
        assert OPERATOR_PERMISSIONS[operation]


@pytest.mark.parametrize("forbidden", list(FORBIDDEN_PAYLOAD_KEYS))
def test_a_payload_naming_a_forbidden_field_is_unrepresentable(forbidden) -> None:
    with pytest.raises(ValidationError, match="must not expose"):
        OperatorOutcome.model_validate(
            {
                "outcome_id": "outcome-a",
                "operation": "get_firm_run",
                "status": "ok",
                "payload": {forbidden: "anything"},
                "reasons": (),
                "principal_id": "operator-owner",
                "request_id": generate_id("req"),
                "correlation_id": generate_id("cor"),
                "completed_at": NOW.isoformat(),
            },
        )


def test_no_operation_returns_a_provider_or_prompt() -> None:
    dependencies = _dependencies()
    auth = Operator()
    submitted = _submit(dependencies=dependencies, auth=auth)
    run_id = submitted.payload["run_id"]
    _emit(dependencies.memory_store, submitted.payload["task_id"])
    outcomes = (
        submitted,
        get_firm_run(dependencies, auth, run_id, at_time=NOW),
        get_firm_audit(
            dependencies,
            auth,
            submitted.payload["task_id"],
            run_id,
            at_time=NOW,
        ),
    )
    for outcome in outcomes:
        rendered = str(outcome.model_dump()).lower()
        for forbidden in ("gemini", "vault://", "you are the", "credential_ref"):
            assert forbidden not in rendered


def test_the_run_view_exposes_state_not_internals() -> None:
    dependencies = _dependencies()
    auth = Operator()
    run_id = _submit(dependencies=dependencies, auth=auth).payload["run_id"]
    outcome = get_firm_run(dependencies, auth, run_id, at_time=NOW)
    assert outcome.status == "ok"
    assert set(outcome.payload) == {
        "run_id",
        "task_id",
        "state",
        "current_node",
        "sequence",
        "terminal",
        "terminal_reason",
    }


def test_an_unknown_run_is_refused_not_failed() -> None:
    outcome = get_firm_run(_dependencies(), Operator(), "run-missing", at_time=NOW)
    assert outcome.status == "refused"
    assert outcome.reasons == ("RUN_NOT_FOUND",)


def test_a_run_can_be_cancelled_through_the_boundary() -> None:
    dependencies = _dependencies()
    auth = Operator()
    run_id = _submit(dependencies=dependencies, auth=auth).payload["run_id"]
    outcome = cancel_firm_run(dependencies, auth, run_id, at_time=NOW)
    assert outcome.status == "ok"
    assert outcome.payload["state"] == "cancelled"


def test_approving_a_handoff_records_a_lifecycle_transition() -> None:
    dependencies = _dependencies()
    auth = Operator()
    for state in ("staged", "evaluated"):
        transition_artifact(
            dependencies.lifecycle_store,
            ARTIFACT_HASH,
            "artifact-a",
            state,  # type: ignore[arg-type]
            "process-lifecycle",
            f"advancing to {state}",
            at_time=NOW,
        )
    outcome = approve_agentic_handoff(
        dependencies,
        auth,
        ARTIFACT_HASH,
        "artifact-a",
        "the reviewer approved the packet",
        at_time=NOW,
    )
    assert outcome.status == "ok"
    assert outcome.payload["state"] == "approved"
    assert outcome.payload["previous_state"] == "evaluated"


def test_a_service_account_cannot_approve_a_handoff() -> None:
    outcome = approve_agentic_handoff(
        _dependencies(),
        Operator(principal_type="SERVICE_ACCOUNT"),
        ARTIFACT_HASH,
        "artifact-a",
        "approving",
        at_time=NOW,
    )
    assert outcome.status == "refused"
    assert outcome.reasons == ("APPROVAL_NOT_HUMAN",)


def test_approving_an_artefact_that_skipped_evaluation_is_refused() -> None:
    dependencies = _dependencies()
    transition_artifact(
        dependencies.lifecycle_store,
        ARTIFACT_HASH,
        "artifact-a",
        "staged",
        "process-lifecycle",
        "staged",
        at_time=NOW,
    )
    outcome = approve_agentic_handoff(
        dependencies,
        Operator(),
        ARTIFACT_HASH,
        "artifact-a",
        "approving from staged",
        at_time=NOW,
    )
    assert outcome.status == "refused"
    assert outcome.reasons == ("TRANSITION_REFUSED",)


def test_quarantine_reaches_the_operations_feature() -> None:
    dependencies = _dependencies()
    auth = Operator()
    submitted = _submit(dependencies=dependencies, auth=auth)
    run_id = submitted.payload["run_id"]
    outcome = quarantine_firm_agent(
        dependencies,
        auth,
        run_id,
        "injection",
        "A retrieved document asked the role to ignore its rules.",
        ROLE_ID,
        ("agentic.memory:record-a",),
        f"agentic.checkpoint:{run_id}:0",
        at_time=NOW,
    )
    assert outcome.status == "ok"
    assert outcome.payload["containment_action"] == "quarantine_and_cancel"
    assert outcome.payload["quarantined_role_id"] == ROLE_ID


def test_replay_through_the_boundary_executes_nothing() -> None:
    dependencies = _dependencies()
    auth = Operator()
    submitted = _submit(dependencies=dependencies, auth=auth)
    task_id = submitted.payload["task_id"]
    _emit(dependencies.memory_store, task_id)
    records = retrieve_memory(dependencies.memory_store, "audit", task_id, NOW)
    request = build_replay_request(
        {
            "replay_id": "replay-public-a",
            "run_id": submitted.payload["run_id"],
            "task_id": task_id,
            "environment": "sandbox",
            "reference_hashes": {records[0].record_id: records[0].content_hash},
            "requested_by": auth.principal_id,
            "requested_at": NOW.isoformat(),
        },
    )
    outcome = replay_firm_run(dependencies, auth, request, at_time=NOW)
    assert outcome.status == "ok"
    assert outcome.payload["executed"] == "False"
    assert outcome.payload["side_effects_attempted"] == "0"


def test_the_audit_view_reports_the_trace_without_its_content() -> None:
    dependencies = _dependencies()
    auth = Operator()
    submitted = _submit(dependencies=dependencies, auth=auth)
    task_id = submitted.payload["task_id"]
    _emit(dependencies.memory_store, task_id)
    outcome = get_firm_audit(
        dependencies,
        auth,
        task_id,
        submitted.payload["run_id"],
        at_time=NOW,
    )
    assert outcome.status == "ok"
    assert outcome.payload["spans_covered"] == str(len(REQUIRED_SPAN_KINDS))
    assert "detail" not in outcome.payload


# --------------------------------------------------------------------------
# FR-AGENTIC-066 - disablement
# --------------------------------------------------------------------------


def test_a_disabled_package_rejects_new_work() -> None:
    outcome = _submit(dependencies=_dependencies(enabled=False))
    assert outcome.status == "refused"
    assert outcome.reasons == ("AGENTIC_DISABLED",)


@pytest.mark.parametrize(
    "operation",
    ["cancel_firm_run", "approve_agentic_handoff", "quarantine_firm_agent"],
)
def test_a_disabled_package_rejects_state_changes(operation) -> None:
    dependencies = _dependencies(enabled=False)
    auth = Operator()
    calls = {
        "cancel_firm_run": lambda: cancel_firm_run(
            dependencies,
            auth,
            "run-a",
            at_time=NOW,
        ),
        "approve_agentic_handoff": lambda: approve_agentic_handoff(
            dependencies,
            auth,
            ARTIFACT_HASH,
            "artifact-a",
            "approving",
            at_time=NOW,
        ),
        "quarantine_firm_agent": lambda: quarantine_firm_agent(
            dependencies,
            auth,
            "run-a",
            "injection",
            "trigger",
            ROLE_ID,
            ("agentic.memory:record-a",),
            "agentic.checkpoint:run-a:0",
            at_time=NOW,
        ),
    }
    outcome = calls[operation]()
    assert outcome.status == "refused"
    assert outcome.reasons == ("AGENTIC_DISABLED",)


def test_disablement_rejects_before_authentication() -> None:
    # A disabled package should not be doing identity lookups either: a
    # principal holding nothing at all still gets AGENTIC_DISABLED.
    outcome = _submit(
        dependencies=_dependencies(enabled=False),
        auth=Operator(permissions=()),
    )
    assert outcome.reasons == ("AGENTIC_DISABLED",)


@pytest.mark.parametrize("operation", sorted(READ_OPERATIONS))
def test_reads_stay_available_while_disabled(operation) -> None:
    dependencies = _dependencies(enabled=False)
    auth = Operator()
    outcome = (
        get_firm_run(dependencies, auth, "run-missing", at_time=NOW)
        if operation == "get_firm_run"
        else get_firm_audit(dependencies, auth, TASK_ID, "run-a", at_time=NOW)
    )
    # Refused for a real reason, never for being disabled.
    assert outcome.reasons != ("AGENTIC_DISABLED",)


def test_a_drain_policy_leaves_active_work_running() -> None:
    dependencies = _dependencies()
    auth = Operator()
    run_id = _submit(dependencies=dependencies, auth=auth).payload["run_id"]
    outcome = disable_agentic(dependencies, auth, (run_id,), "drain", at_time=NOW)
    assert outcome.status == "ok"
    assert outcome.payload["drained_runs"] == "1"
    assert outcome.payload["cancelled_runs"] == "0"
    assert dependencies.workflow_store.load_run(run_id).state == "submitted"


def test_a_cancel_policy_stops_active_work() -> None:
    dependencies = _dependencies()
    auth = Operator()
    run_id = _submit(dependencies=dependencies, auth=auth).payload["run_id"]
    outcome = disable_agentic(dependencies, auth, (run_id,), "cancel", at_time=NOW)
    assert outcome.status == "ok"
    assert outcome.payload["cancelled_runs"] == "1"
    assert dependencies.workflow_store.load_run(run_id).state == "cancelled"


def test_disablement_preserves_audit_evidence() -> None:
    dependencies = _dependencies()
    auth = Operator()
    submitted = _submit(dependencies=dependencies, auth=auth)
    task_id = submitted.payload["task_id"]
    _emit(dependencies.memory_store, task_id)
    before = len(retrieve_memory(dependencies.memory_store, "audit", task_id, NOW))
    disable_agentic(
        dependencies,
        auth,
        (submitted.payload["run_id"],),
        "cancel",
        at_time=NOW,
    )
    after = len(retrieve_memory(dependencies.memory_store, "audit", task_id, NOW))
    assert after == before
    assert before == len(REQUIRED_SPAN_KINDS)


def test_disablement_reports_what_it_settled() -> None:
    dependencies = _dependencies()
    auth = Operator()
    run_id = _submit(dependencies=dependencies, auth=auth).payload["run_id"]
    outcome = disable_agentic(
        dependencies,
        auth,
        (run_id, "run-missing"),
        "drain",
        at_time=NOW,
    )
    assert outcome.payload["runs_examined"] == "1"
    assert outcome.payload["audit_preserved"] == "true"


def test_disablement_requires_the_operate_permission() -> None:
    outcome = disable_agentic(
        _dependencies(),
        Operator(permissions=("agentic:submit",)),
        (),
        "drain",
        at_time=NOW,
    )
    assert outcome.status == "refused"
    assert outcome.reasons == ("PERMISSION_DENIED",)


def test_the_package_holds_no_deterministic_safety_authority() -> None:
    from pathlib import Path

    sources = "".join(
        path.read_text(encoding="utf-8")
        for path in Path("app/agentic/public_api").glob("*.py")
    )
    for forbidden in (
        "kill_switch",
        "apply_kill_switch_command",
        "review_allocation_proposal",
        "dispatch_order_intent",
        "app.services.risk",
        "app.services.trading",
        "app.services.brokers",
    ):
        assert forbidden not in sources


# --------------------------------------------------------------------------
# The package root stays a function-only surface
# --------------------------------------------------------------------------


def test_every_root_export_is_a_standalone_function() -> None:
    non_functions = [
        name
        for name in agentic_root.__all__
        if not inspect.isfunction(getattr(agentic_root, name))
    ]
    assert non_functions == []


def test_every_root_export_resolves() -> None:
    missing = [name for name in agentic_root.__all__ if not hasattr(agentic_root, name)]
    assert missing == []


def test_the_root_exports_the_operator_surface() -> None:
    for operation in get_operator_operations():
        assert operation in agentic_root.__all__


def test_the_root_exposes_no_unimplemented_capability() -> None:
    # WF-AGT-005's planned sandbox exports have no isolation runtime to open,
    # so they stay absent. FEAT-AGT-09 and -10 have since landed and are
    # exported; the assertion below reflects that.
    for absent in ("open_sandbox", "stage_code_artifact"):
        assert absent not in agentic_root.__all__
    for present in ("analyze_fundamentals", "analyze_sentiment"):
        assert present in agentic_root.__all__
