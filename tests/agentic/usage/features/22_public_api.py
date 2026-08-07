"""Executable FEAT-AGT-22 public Agentic API usage example.

Demonstrates every registered operator operation through the documented API.
Every store is the deterministic in-memory double its owning feature ships, so
nothing is written to disk, no network call occurs, and Agentic holds no
credential.

The point of the demonstration is that the operator boundary is narrow. Seven
operations, each requiring an authenticated principal and an explicit
dependency record; every answer a mapping of bounded strings, so no prompt,
credential, or provider name has anywhere to travel; and disablement that stops
new work without hiding what already happened.
"""

import inspect
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import app.agentic as agentic_root
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
)
from app.agentic.operations.service import SPAN_KEY
from app.agentic.public_api import (
    FORBIDDEN_PAYLOAD_KEYS,
    OPERATOR_PERMISSIONS,
    READ_OPERATIONS,
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
from app.utils import generate_id

from tests.agentic.usage._runner import run_feature_usage

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tests.agentic.fixtures import (
    build_technical_mandate,
    build_technical_role_manifest,
)

NOW = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
WORKFLOW_NAME = "firm_research_council"
ROLE_ID = "technical_analyst"
ARTIFACT_HASH = "sha256:artifact-usage"

BANNER = "=" * 88


def heading(requirement: str, statement: str) -> None:
    """Print one requirement heading.

    Args:
        requirement: Functional requirement identifier.
        statement: What the requirement obliges.
    """
    print(f"\n{BANNER}\n{requirement}: {statement}\n{BANNER}")


class Operator:
    """An authenticated operator principal."""

    def __init__(self, **overrides: object) -> None:
        """Initialize the operator principal.

        Args:
            **overrides: Optional attribute overrides.
        """
        self.principal_id = "operator-owner"
        self.principal_type = "USER"
        self.permissions = tuple(sorted(set(OPERATOR_PERMISSIONS.values())))
        self.tenant_or_environment = "sandbox"
        self.request_id = generate_id("req")
        self.workflow_id = generate_id("wf")
        self.correlation_id = generate_id("cor")
        for key, value in overrides.items():
            setattr(self, key, value)


def dependencies(*, enabled: bool = True):
    """Build the explicit composition record.

    Args:
        enabled: Whether the package is enabled.

    Returns:
        The frozen dependency record.
    """
    mandate = build_technical_mandate()
    return build_agentic_dependencies(
        settings=get_agentic_settings(
            {
                "agentic_enabled": True,
                "agentic_mandate_path": "app/configs/agentic-mandate.json",
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


def emit(memory, task_id: str) -> None:
    """Write one audit record per required span, as the firm's emitters do.

    Args:
        memory: Injected governed memory store.
        task_id: Owning task identity.
    """
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


def submit(deps, auth):
    """Submit one governed request.

    Args:
        deps: Explicit composition dependencies.
        auth: Authenticated operator principal.

    Returns:
        The typed operator outcome.
    """
    return submit_firm_request(
        deps,
        auth,
        WORKFLOW_NAME,
        "Assess EURUSD H1 trend evidence.",
        ("evidence-market-1",),
        "idem-public-usage",
        at_time=NOW,
    )


def show(outcome: OperatorOutcome) -> None:
    """Print one operator outcome.

    Args:
        outcome: Typed operator outcome.
    """
    fields = ", ".join(f"{k}={v}" for k, v in sorted(outcome.payload.items()))
    reasons = ",".join(outcome.reasons) or "-"
    print(f"    {outcome.operation:<24} {outcome.status:<8} {reasons:<24} {fields}")


def fr_agentic_064() -> None:
    """Demonstrate auth, explicit dependencies, IDs, bounds, and mapping."""
    heading(
        "FR-AGENTIC-064",
        "Public operations require AuthContext, explicit dependencies, "
        "request/correlation IDs, bounded inputs, and stable mapped failures.",
    )

    deps = dependencies()
    auth = Operator()
    outcome = submit(deps, auth)
    print(f"  operator operations: {len(get_operator_operations())}")
    print("    (the seven FR-AGENTIC-065 operations plus FR-AGENTIC-066 disablement)")
    print(f"  request id carried:  {outcome.request_id == auth.request_id}")
    print(f"  correlation carried: {outcome.correlation_id == auth.correlation_id}")
    print(f"  principal carried:   {outcome.principal_id}")
    print(f"  run reserved:        {outcome.payload['run_id'][:32]}...")

    print("\n  Every operation takes the dependency record and the principal first:")
    for name in get_operator_operations():
        operation = getattr(agentic_root, name, None)
        if operation is None:
            continue
        first = list(inspect.signature(operation).parameters)[:2]
        print(f"    {name:<24} {first}")

    print("\n  A caller cannot invoke against a partially wired firm:")
    try:
        build_agentic_dependencies()  # type: ignore[call-arg]
        verdict = "ERROR: an incomplete dependency record was built"
    except TypeError as error:
        verdict = str(error).split("(")[0].strip() + " (missing required ports)"
    print(f"    {verdict}")

    print("\n  Failures are mapped, never raised:")
    cases = (
        ("an unregistered workflow", {"workflow_name": "not_a_workflow"}),
        ("an empty objective", {"objective": ""}),
        ("a missing permission", {"auth": Operator(permissions=("agentic:read_run",))}),
        ("another environment", {"auth": Operator(tenant_or_environment="production")}),
    )
    for label, override in cases:
        principal = override.pop("auth", auth)
        result = submit_firm_request(
            deps,
            principal,
            override.get("workflow_name", WORKFLOW_NAME),
            override.get("objective", "Assess EURUSD H1 trend evidence."),
            ("evidence-market-1",),
            "idem-public-usage-b",
            at_time=NOW,
        )
        print(f"    {label:<26} -> {result.status}: {','.join(result.reasons)}")


def fr_agentic_065() -> None:
    """Demonstrate the seven operator operations and what they never expose."""
    heading(
        "FR-AGENTIC-065",
        "Operator APIs expose submit, inspect, cancel, approve-handoff, "
        "replay, quarantine, and audit without exposing prompts, credentials, "
        "or provider internals.",
    )

    deps = dependencies()
    auth = Operator()
    submitted = submit(deps, auth)
    run_id = submitted.payload["run_id"]
    task_id = submitted.payload["task_id"]
    emit(deps.memory_store, task_id)
    records = retrieve_memory(deps.memory_store, "audit", task_id, NOW)
    for state in ("staged", "evaluated"):
        transition_artifact(
            deps.lifecycle_store,
            ARTIFACT_HASH,
            "artifact-a",
            state,
            "process-lifecycle",
            f"advancing to {state}",
            at_time=NOW,
        )

    print("  The whole operator surface, in order:")
    show(submitted)
    show(get_firm_run(deps, auth, run_id, at_time=NOW))
    show(get_firm_audit(deps, auth, task_id, run_id, at_time=NOW))
    show(
        replay_firm_run(
            deps,
            auth,
            build_replay_request(
                {
                    "replay_id": "replay-usage",
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
        ),
    )
    show(
        approve_agentic_handoff(
            deps,
            auth,
            ARTIFACT_HASH,
            "artifact-a",
            "the reviewer approved the complete packet",
            at_time=NOW,
        ),
    )
    show(
        quarantine_firm_agent(
            deps,
            auth,
            run_id,
            "injection",
            "A retrieved document asked the role to ignore its rules.",
            ROLE_ID,
            (records[0].record_id,),
            f"agentic.checkpoint:{run_id}:0",
            at_time=NOW,
        ),
    )
    # Containment already cancelled the run, so this is an ordinary refusal
    # rather than a failure: a stopped run needs no cancelling.
    show(cancel_firm_run(deps, auth, run_id, at_time=NOW))
    print(
        "    artefact state now: "
        f"{get_artifact_state(deps.lifecycle_store, ARTIFACT_HASH)}"
    )

    print(
        "\n  Every answer is a mapping of bounded strings, so nothing can ride along:"
    )
    audited = get_firm_audit(deps, auth, task_id, run_id, at_time=NOW)
    rendered = str(audited.model_dump()).lower()
    for forbidden in ("super-secret-value", "vault://", "gemini", "you are the"):
        print(f"    {forbidden:<22} present: {forbidden in rendered}")

    print("\n  Naming a forbidden field is refused outright:")
    for key in ("prompt", "credential_ref", "model_provider"):
        try:
            OperatorOutcome.model_validate(
                {
                    "outcome_id": "outcome-a",
                    "operation": "get_firm_run",
                    "status": "ok",
                    "payload": {key: "anything"},
                    "reasons": (),
                    "principal_id": auth.principal_id,
                    "request_id": auth.request_id,
                    "correlation_id": auth.correlation_id,
                    "completed_at": NOW.isoformat(),
                },
            )
            verdict = "ERROR: a forbidden field was accepted"
        except Exception:  # noqa: BLE001 - usage demonstrates rejection.
            verdict = "unbuildable"
        print(f"    {key:<22} -> {verdict}")
    print(f"    the prohibition list holds {len(FORBIDDEN_PAYLOAD_KEYS)} names")


def fr_agentic_066() -> None:
    """Demonstrate disablement and deterministic safety equivalence."""
    heading(
        "FR-AGENTIC-066",
        "Package disablement rejects new work, cancels or drains active work "
        "by policy, preserves audit evidence, and leaves deterministic safety "
        "controls available.",
    )

    deps = dependencies()
    auth = Operator()
    submitted = submit(deps, auth)
    task_id = submitted.payload["task_id"]
    emit(deps.memory_store, task_id)
    before = len(retrieve_memory(deps.memory_store, "audit", task_id, NOW))

    print("  A drain policy lets active work finish:")
    drained = disable_agentic(
        deps,
        auth,
        (submitted.payload["run_id"],),
        "drain",
        at_time=NOW,
    )
    show(drained)
    print(
        f"    run state: {deps.workflow_store.load_run(submitted.payload['run_id']).state}"
    )

    print("\n  A cancel policy stops it through the normal path:")
    cancelled = disable_agentic(
        deps,
        auth,
        (submitted.payload["run_id"],),
        "cancel",
        at_time=NOW,
    )
    show(cancelled)
    print(
        f"    run state: {deps.workflow_store.load_run(submitted.payload['run_id']).state}"
    )

    after = len(retrieve_memory(deps.memory_store, "audit", task_id, NOW))
    print(f"\n  Audit evidence before and after disablement: {before} -> {after}")

    print("\n  A disabled package refuses new work but still answers reads:")
    off = dependencies(enabled=False)
    show(submit(off, auth))
    show(get_firm_run(off, auth, "run-missing", at_time=NOW))
    print(f"    read operations available while disabled: {sorted(READ_OPERATIONS)}")

    print("\n  Deterministic safety is unaffected, because Agentic never held it:")
    sources = "".join(
        path.read_text(encoding="utf-8")
        for path in Path("app/agentic").rglob("*.py")
        if "__pycache__" not in str(path)
    )
    for capability in (
        "apply_kill_switch_command",
        "check_risk_kill_switch",
        "dispatch_order_intent",
        "evaluate_live_gate",
        "review_allocation_proposal",
        "MetaTrader5",
    ):
        print(f"    {capability:<28} present in app/agentic: {capability in sources}")

    print("\n  The package root is a function-only surface:")
    non_functions = [
        name
        for name in agentic_root.__all__
        if not inspect.isfunction(getattr(agentic_root, name))
    ]
    print(f"    exports: {len(agentic_root.__all__)}")
    print(f"    non-function exports: {non_functions or 'none'}")

    print("\n  Nothing unimplemented is exported:")
    for absent in (
        "analyze_fundamentals",
        "analyze_sentiment",
        "open_sandbox",
        "stage_code_artifact",
    ):
        print(f"    {absent:<24} exported: {absent in agentic_root.__all__}")

    print(
        "\n  Note: FEAT-AGT-09 and -10 are not implemented, and WF-AGT-005's "
        "planned\n  open_sandbox and stage_code_artifact have no isolation "
        "runtime to open. A\n  function that could not do what its name "
        "promises would be worse than the\n  gap, so none is exported."
    )


def main() -> None:
    """Run every functional-requirement demonstration for the public API."""
    fr_agentic_064()
    fr_agentic_065()
    fr_agentic_066()


if __name__ == "__main__":
    run_feature_usage("FEAT-AGT-22", main)
