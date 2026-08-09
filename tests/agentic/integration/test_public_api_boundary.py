"""Integration evidence for the `FEAT-AGT-22` operator boundary.

Exercises what an operator actually does across the whole firm: submit a
request, inspect the run, audit it, contain an incident on it, validate a
replay, approve a staged artefact, and disable the package — each through the
public API, each against the real stores the owning features ship.

The last two tests are the ones worth reading. One asserts that no operator
response anywhere on the surface carries a prompt, a credential, or a provider
name. The other asserts the domain-wide invariant every feature has held: the
package holds no kill switch, no risk approval, and no execution route, so
disabling it cannot weaken deterministic safety because it never had any of it
to surrender.
"""

from __future__ import annotations

import inspect
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
    get_artifact_state,
    transition_artifact,
)
from app.agentic.operations import (
    REQUIRED_SPAN_KINDS,
    build_in_memory_operations_store,
    build_replay_request,
    get_quarantined_roles,
)
from app.agentic.operations.service import SPAN_KEY
from app.agentic.public_api import (
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
from app.utils import generate_id

from tests.agentic.fixtures import (
    NOW,
    build_technical_mandate,
    build_technical_role_manifest,
)

WORKFLOW_NAME = "firm_research_council"
ROLE_ID = "technical_analyst"
ARTIFACT_HASH = "sha256:artifact-boundary"


class _Operator:
    """An authenticated operator principal holding every operator permission."""

    def __init__(self, **overrides: object) -> None:
        self.principal_id = "operator-owner"
        self.principal_type = "USER"
        self.permissions = (
            "agentic:approve_promotion",
            "agentic:cancel_run",
            "agentic:operate",
            "agentic:read_audit",
            "agentic:read_run",
            "agentic:replay",
            "agentic:submit",
        )
        self.tenant_or_environment = "sandbox"
        self.request_id = generate_id("req")
        self.workflow_id = generate_id("wf")
        self.correlation_id = generate_id("cor")
        for key, value in overrides.items():
            setattr(self, key, value)


def _dependencies(*, enabled: bool = True):
    mandate = build_technical_mandate()
    return build_agentic_dependencies(
        settings=get_agentic_settings(
            {
                "agentic_enabled": True,
                "agentic_mandate_path": "data/agentic/agentic-mandate.json",
                "agentic_model_profiles": ("profile-market-analysis-a",),
                "agentic_limits_profile": "agentic-limits-sandbox-v1",
            }
            if enabled
            else {"agentic_enabled": False},
        ),
        mandate=mandate,
        registry=get_role_registry(mandate, (build_technical_role_manifest(),), NOW),
        workflow_store=build_in_memory_workflow_store(),
        memory_store=build_in_memory_memory_store(),
        operations_store=build_in_memory_operations_store(),
        lifecycle_store=build_in_memory_lifecycle_store(),
        definitions={
            WORKFLOW_NAME: build_workflow_definition(
                {
                    "workflow_name": WORKFLOW_NAME,
                    "version": "1.0.0",
                    "nodes": ("collect_briefs", "challenge", "synthesize"),
                    "entry_node": "collect_briefs",
                    "limits_profile_id": "agentic-limits-sandbox-v1",
                    "max_fan_out": 4,
                    "max_rounds": 1,
                    "max_retries": 2,
                    "deadline_seconds": 1_800,
                    "permits_human_wait": True,
                },
            ),
        },
        agent_policies={
            ROLE_ID: build_agent_policy(
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
            ),
        },
        tool_policies={
            "data.get_market_data": build_tool_policy(
                {
                    "tool_name": "data.get_market_data",
                    "version": "1.0.0",
                    "owning_feature": "FEAT-AGT-22",
                    "receiver_domain": "data",
                    "public_operation": "get_market_data",
                    "request_schema_id": "data.get_market_data.request.v1",
                    "result_schema_id": "data.get_market_data.result.v1",
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
            ),
        },
    )


def _emit(memory, task_id: str) -> None:
    for kind in sorted(REQUIRED_SPAN_KINDS):
        content = {SPAN_KEY: kind, "detail": f"the {kind} span was emitted"}
        if kind == "cost":
            content["cost"] = "0.40"
        if kind == "tool":
            content["api_key"] = "super-secret-value"  # pragma: allowlist secret
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


def _submit(dependencies, auth):
    return submit_firm_request(
        dependencies,
        auth,
        WORKFLOW_NAME,
        "Assess EURUSD H1 trend evidence.",
        ("evidence-market-1",),
        "idem-boundary",
        at_time=NOW,
    )


def test_an_operator_drives_the_whole_firm_through_the_public_api() -> None:
    dependencies = _dependencies()
    auth = _Operator()

    # 1. Submit: a real run is reserved through the normal orchestration path.
    submitted = _submit(dependencies, auth)
    assert submitted.status == "ok"
    run_id = submitted.payload["run_id"]
    task_id = submitted.payload["task_id"]

    # 2. Inspect: the run's durable state, and nothing about how it runs.
    inspected = get_firm_run(dependencies, auth, run_id, at_time=NOW)
    assert inspected.status == "ok"
    assert inspected.payload["state"] == "submitted"
    assert inspected.payload["terminal"] == "False"

    # 3. Audit: a correlated trace, redacted at the memory boundary.
    _emit(dependencies.memory_store, task_id)
    audited = get_firm_audit(dependencies, auth, task_id, run_id, at_time=NOW)
    assert audited.status == "ok"
    assert audited.payload["spans_covered"] == str(len(REQUIRED_SPAN_KINDS))
    assert int(audited.payload["redacted_paths"]) >= 1

    # 4. Replay: validated against immutable references, executing nothing.
    records = retrieve_memory(dependencies.memory_store, "audit", task_id, NOW)
    replayed = replay_firm_run(
        dependencies,
        auth,
        build_replay_request(
            {
                "replay_id": "replay-boundary",
                "run_id": run_id,
                "task_id": task_id,
                "environment": "sandbox",
                "reference_hashes": {
                    records[0].record_id: records[0].content_hash,
                },
                "requested_by": auth.principal_id,
                "requested_at": NOW.isoformat(),
            },
        ),
        at_time=NOW,
    )
    assert replayed.status == "ok"
    assert replayed.payload["executed"] == "False"

    # 5. Quarantine: containment derived from the kind, applied to the run.
    contained = quarantine_firm_agent(
        dependencies,
        auth,
        run_id,
        "injection",
        "A retrieved document asked the role to ignore its rules.",
        ROLE_ID,
        (records[0].record_id,),
        f"agentic.checkpoint:{run_id}:0",
        at_time=NOW,
    )
    assert contained.status == "ok"
    assert contained.payload["containment_action"] == "quarantine_and_cancel"
    assert get_quarantined_roles(dependencies.operations_store) == (ROLE_ID,)
    assert dependencies.workflow_store.load_run(run_id).state == "cancelled"

    # 6. Approve: through the FEAT-AGT-18 ledger, with its rules intact.
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
    approved = approve_agentic_handoff(
        dependencies,
        auth,
        ARTIFACT_HASH,
        "artifact-a",
        "the reviewer approved the complete packet",
        at_time=NOW,
    )
    assert approved.status == "ok"
    assert get_artifact_state(dependencies.lifecycle_store, ARTIFACT_HASH) == "approved"


def test_disablement_stops_new_work_and_keeps_the_evidence() -> None:
    dependencies = _dependencies()
    auth = _Operator()
    submitted = _submit(dependencies, auth)
    task_id = submitted.payload["task_id"]
    _emit(dependencies.memory_store, task_id)
    before = len(retrieve_memory(dependencies.memory_store, "audit", task_id, NOW))

    settled = disable_agentic(
        dependencies,
        auth,
        (submitted.payload["run_id"],),
        "cancel",
        at_time=NOW,
    )
    assert settled.status == "ok"
    assert settled.payload["cancelled_runs"] == "1"

    # The audit evidence survives disablement untouched.
    after = retrieve_memory(dependencies.memory_store, "audit", task_id, NOW)
    assert len(after) == before

    # And a disabled package refuses new work while still answering reads.
    disabled = _dependencies(enabled=False)
    refused = _submit(disabled, auth)
    assert refused.reasons == ("AGENTIC_DISABLED",)
    readable = get_firm_run(disabled, auth, "run-missing", at_time=NOW)
    assert readable.reasons == ("RUN_NOT_FOUND",)


def test_no_operator_response_carries_a_prompt_credential_or_provider() -> None:
    dependencies = _dependencies()
    auth = _Operator()
    submitted = _submit(dependencies, auth)
    task_id = submitted.payload["task_id"]
    run_id = submitted.payload["run_id"]
    _emit(dependencies.memory_store, task_id)

    outcomes = [
        submitted,
        get_firm_run(dependencies, auth, run_id, at_time=NOW),
        get_firm_audit(dependencies, auth, task_id, run_id, at_time=NOW),
        cancel_firm_run(dependencies, auth, run_id, at_time=NOW),
        approve_agentic_handoff(
            dependencies,
            auth,
            ARTIFACT_HASH,
            "artifact-a",
            "approving",
            at_time=NOW,
        ),
    ]
    for outcome in outcomes:
        rendered = str(outcome.model_dump()).lower()
        for forbidden in (
            "super-secret-value",
            "vault://",
            "gemini",
            "you are the",
            "credential",
            "base_prompt",
        ):
            assert forbidden not in rendered, outcome.operation


def test_the_package_holds_no_deterministic_safety_authority() -> None:
    from pathlib import Path

    # The domain-wide invariant, checked over the whole package rather than one
    # feature: disabling Agentic cannot weaken deterministic safety because
    # Agentic never held any of it.
    sources = "".join(
        path.read_text(encoding="utf-8")
        for path in Path("app/agentic").rglob("*.py")
        if "__pycache__" not in str(path)
    )
    for forbidden in (
        "apply_kill_switch_command",
        "check_risk_kill_switch",
        "dispatch_order_intent",
        "evaluate_live_gate",
        "activate_allocation_budget",
        "review_allocation_proposal",
        "MetaTrader5",
        "ALLOW_LIVE_MUTATIONS",
    ):
        assert forbidden not in sources


def test_the_root_surface_stays_function_only() -> None:
    non_functions = [
        name
        for name in agentic_root.__all__
        if not inspect.isfunction(getattr(agentic_root, name))
    ]
    assert non_functions == []
    for operation in get_operator_operations():
        assert operation in agentic_root.__all__


@pytest.mark.parametrize(
    "planned",
    ["open_sandbox", "stage_code_artifact"],
)
def test_the_root_exposes_nothing_that_does_not_exist(planned) -> None:
    # WF-AGT-005 names two planned sandbox exports. Neither is implemented, so
    # neither is exported: a function that could not do what its name promises
    # is worse than the gap. FEAT-AGT-09 and -10 have since landed, and their
    # operations are exported because they genuinely work.
    assert planned not in agentic_root.__all__
    assert "analyze_fundamentals" in agentic_root.__all__
    assert "analyze_sentiment" in agentic_root.__all__
