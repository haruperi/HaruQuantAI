"""Authenticated typed Agentic application operations.

`FR-AGENTIC-065` names seven operator operations: submit, inspect, cancel,
approve-handoff, replay, quarantine, and audit. All seven are here. The §4.22
key-exports column names three of them; it is a subset of the requirement, not
a cap on it.

Every operation returns an `OperatorOutcome` whose payload is a mapping of
bounded **strings**. That is the enforcement point for "without exposing
prompts, credentials, or provider internals": there is no nested object an
operator response could carry a provider name or a prompt inside, and a
validator refuses the field names that would smuggle one in as text.

`FR-AGENTIC-066` disablement is checked before authentication in every
operation that creates or changes work, because a disabled package should not
be performing identity lookups either. Read operations stay available while
disabled — inspecting a trace is how an operator learns why the package was
disabled, and refusing that would make disablement a way to hide.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from app.agentic.contracts.models import build_agent_task
from app.agentic.lifecycle.service import can_transition, transition_artifact
from app.agentic.operations.service import (
    get_run_trace,
    quarantine_agent,
    replay_run,
)
from app.agentic.orchestration.models import is_terminal_state
from app.agentic.orchestration.service import cancel_task, submit_task
from app.utils import derive_stable_id, get_logger, map_exception, utc_now

if TYPE_CHECKING:
    from app.agentic.contracts.models import AgentTask
    from app.agentic.operations.models import IncidentKind, ReplayRequest
    from app.agentic.orchestration.models import WorkflowRun
    from app.agentic.public_api.dependencies import (
        AgenticDependencies,
        AuthenticatedPrincipal,
    )

logger = get_logger(__name__)

_MAX_TEXT = 2_000
_MAX_SHORT_TEXT = 200
_MAX_ITEMS = 64

type OperatorStatus = Literal["ok", "refused", "failed"]

type DrainPolicy = Literal["cancel", "drain"]

# The permission each operator operation requires. Deny by default: an
# operation whose permission a principal does not hold is refused before any
# store is touched.
OPERATOR_PERMISSIONS: Mapping[str, str] = {
    "approve_agentic_handoff": "agentic:approve_promotion",
    "cancel_firm_run": "agentic:cancel_run",
    "disable_agentic": "agentic:operate",
    "get_firm_audit": "agentic:read_audit",
    "get_firm_run": "agentic:read_run",
    "quarantine_firm_agent": "agentic:operate",
    "replay_firm_run": "agentic:replay",
    "submit_firm_request": "agentic:submit",
}

# Operations that read. These stay available while the package is disabled,
# because understanding a disabled firm requires reading it.
READ_OPERATIONS: frozenset[str] = frozenset(
    {"get_firm_audit", "get_firm_run"},
)

# Payload keys an operator response must never carry. The payload is a string
# mapping, so this closes the remaining route: naming the field.
FORBIDDEN_PAYLOAD_KEYS: tuple[str, ...] = (
    "api_key",
    "base_prompt",
    "credential",
    "credential_ref",
    "instruction",
    "model_identifier",
    "model_provider",
    "prompt",
    "prompt_text",
    "provider",
    "secret",
    "system_prompt",
    "token",
)


def _text(value: str, field: str, *, limit: int = _MAX_TEXT) -> str:
    """Validate bounded non-empty trimmed text.

    Args:
        value: Candidate text.
        field: Safe field label for validation.
        limit: Maximum permitted character count.

    Returns:
        Validated text.

    Raises:
        ValueError: If the text is empty, untrimmed, or oversized.
    """
    if not value or value != value.strip():
        message = f"{field} must be non-empty trimmed text"
        raise ValueError(message)
    if len(value) > limit:
        message = f"{field} must not exceed {limit} characters"
        raise ValueError(message)
    return value


class OperatorOutcome(BaseModel):
    """One typed answer from the public Agentic boundary.

    The payload is a mapping of bounded strings by design. An operator
    response has no nested object a prompt, a credential, or a provider name
    could travel inside, and the forbidden-key rule closes the text route.

    Attributes:
        outcome_id: Stable outcome identity.
        operation: Operator operation this answers.
        status: Whether the operation succeeded, refused, or failed.
        payload: Bounded string result fields.
        reasons: Ordered enumerated reason codes.
        detail: Bounded advisory detail.
        principal_id: Principal that invoked the operation.
        request_id: Trace identifier of the outer request.
        correlation_id: Trace identifier tracking the whole flow.
        completed_at: Completion time, as an ISO-8601 UTC string.
    """

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        frozen=True,
        strict=True,
    )

    outcome_id: str
    operation: str
    status: OperatorStatus
    payload: Mapping[str, str]
    reasons: tuple[str, ...]
    principal_id: str
    request_id: str
    correlation_id: str
    completed_at: str
    detail: str | None = None

    @field_validator(
        "outcome_id",
        "operation",
        "principal_id",
        "request_id",
        "correlation_id",
        "completed_at",
    )
    @classmethod
    def _validate_reference(cls, value: str) -> str:
        """Validate one required outcome reference.

        Args:
            value: Candidate reference.

        Returns:
            Validated reference.
        """
        return _text(value, "outcome reference", limit=_MAX_SHORT_TEXT)

    @field_validator("payload")
    @classmethod
    def _validate_payload(cls, value: Mapping[str, str]) -> Mapping[str, str]:
        """Validate that the payload exposes nothing it must not.

        Args:
            value: Candidate payload.

        Returns:
            Deterministically ordered payload.

        Raises:
            ValueError: If the payload is oversized or names a forbidden field.
        """
        if len(value) > _MAX_ITEMS:
            message = f"an operator payload must not exceed {_MAX_ITEMS} entries"
            raise ValueError(message)
        for key in sorted(value):
            lowered = key.lower()
            for forbidden in FORBIDDEN_PAYLOAD_KEYS:
                if forbidden in lowered:
                    message = (
                        f"an operator payload must not expose {key!r}; prompts, "
                        "credentials, and provider internals stay inside the "
                        "package"
                    )
                    raise ValueError(message)
        return {
            _text(key, "payload key", limit=_MAX_SHORT_TEXT): _text(
                item,
                "payload entry",
            )
            for key, item in sorted(value.items())
        }

    @field_validator("detail")
    @classmethod
    def _validate_detail(cls, value: str | None) -> str | None:
        """Validate the optional advisory detail.

        Args:
            value: Candidate detail.

        Returns:
            Validated detail, or None.
        """
        if value is None:
            return None
        return _text(value, "outcome detail")

    @field_validator("reasons")
    @classmethod
    def _validate_reasons(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Validate the enumerated reason codes.

        Args:
            value: Candidate codes.

        Returns:
            Validated codes.

        Raises:
            ValueError: If the tuple is oversized.
        """
        if len(value) > _MAX_ITEMS:
            message = f"operator reasons must not exceed {_MAX_ITEMS} entries"
            raise ValueError(message)
        return tuple(
            _text(item, "reason code", limit=_MAX_SHORT_TEXT) for item in value
        )

    @field_serializer("payload", mode="plain")
    def _serialize_payload(self, value: Mapping[str, str]) -> dict[str, str]:
        """Serialize the payload deterministically.

        Args:
            value: Payload mapping.

        Returns:
            Plain ordered mapping.
        """
        return dict(value)


def _outcome(
    operation: str,
    status: OperatorStatus,
    auth: AuthenticatedPrincipal,
    at_time: datetime,
    payload: Mapping[str, str] | None = None,
    reasons: tuple[str, ...] = (),
    detail: str | None = None,
) -> OperatorOutcome:
    """Build one typed operator outcome.

    Args:
        operation: Operator operation this answers.
        status: Whether the operation succeeded, refused, or failed.
        auth: Authenticated principal that invoked it.
        at_time: Completion time.
        payload: Optional bounded string result fields.
        reasons: Ordered enumerated reason codes.
        detail: Bounded advisory detail.

    Returns:
        A validated immutable outcome.
    """
    return OperatorOutcome.model_validate(
        {
            "outcome_id": derive_stable_id(
                "id",
                f"operator:{operation}:{auth.request_id}",
            ),
            "operation": operation,
            "status": status,
            "payload": dict(payload or {}),
            "reasons": reasons,
            "detail": detail,
            "principal_id": auth.principal_id,
            "request_id": auth.request_id,
            "correlation_id": auth.correlation_id,
            "completed_at": at_time.isoformat(),
        },
    )


def _admission(
    dependencies: AgenticDependencies,
    auth: AuthenticatedPrincipal,
    operation: str,
) -> tuple[str, str] | None:
    """Report why an operator call may not proceed.

    Enablement is checked before authentication for anything that creates or
    changes work: a disabled package should not be performing identity lookups
    either. Reads stay available so an operator can understand a disabled firm.

    Args:
        dependencies: Explicit composition dependencies.
        auth: Authenticated principal.
        operation: Operator operation requested.

    Returns:
        An enumerated reason and detail, or None when the call may proceed.
    """
    reads = operation in READ_OPERATIONS
    if not reads and not dependencies.settings.agentic_enabled:
        return (
            "AGENTIC_DISABLED",
            "Agentic is disabled and accepts no new or state-changing work.",
        )
    required = OPERATOR_PERMISSIONS.get(operation)
    if required is None:
        return ("OPERATION_NOT_REGISTERED", f"{operation!r} is not an operator API.")
    if required not in auth.permissions:
        return (
            "PERMISSION_DENIED",
            f"The principal does not hold {required}.",
        )
    if auth.tenant_or_environment != dependencies.mandate.environment:
        return (
            "ENVIRONMENT_MISMATCH",
            (
                f"The context was issued for {auth.tenant_or_environment!r}, not "
                f"for {dependencies.mandate.environment!r}."
            ),
        )
    return None


def _refused(
    operation: str,
    auth: AuthenticatedPrincipal,
    failure: tuple[str, str],
    at_time: datetime,
) -> OperatorOutcome:
    """Build one refused operator outcome.

    Args:
        operation: Operator operation refused.
        auth: Authenticated principal.
        failure: Enumerated reason and detail.
        at_time: Refusal time.

    Returns:
        A refused typed outcome.
    """
    reason, detail = failure
    logger.info("Operator %s refused for %s: %s", operation, auth.principal_id, reason)
    return _outcome(
        operation, "refused", auth, at_time, reasons=(reason,), detail=detail
    )


def _failed(
    operation: str,
    auth: AuthenticatedPrincipal,
    error: Exception,
    at_time: datetime,
) -> OperatorOutcome:
    """Map one unexpected failure onto a bounded typed outcome.

    Nothing raw escapes the boundary. `map_exception` returns a symbolic code
    and a bounded detail, so a provider or receiver exception never reaches an
    operator as a traceback.

    Args:
        operation: Operator operation that failed.
        auth: Authenticated principal.
        error: Caught exception; never returned or retained.
        at_time: Failure time.

    Returns:
        A failed typed outcome.
    """
    mapped = map_exception(error)
    logger.warning("Operator %s failed: %s", operation, mapped["code"])
    return _outcome(
        operation,
        "failed",
        auth,
        at_time,
        reasons=(mapped["code"],),
        detail=mapped["detail"],
    )


def submit_firm_request(
    dependencies: AgenticDependencies,
    auth: AuthenticatedPrincipal,
    workflow_name: str,
    objective: str,
    input_refs: tuple[str, ...],
    idempotency_key: str,
    deadline_seconds: int = 1_800,
    cost_budget: Decimal | None = None,
    at_time: datetime | None = None,
) -> OperatorOutcome:
    """Submit one bounded governed request to the firm.

    Args:
        dependencies: Explicit composition dependencies.
        auth: Authenticated principal.
        workflow_name: Registered workflow to run.
        objective: Bounded research objective.
        input_refs: Evidence references the request rests on.
        idempotency_key: Submission idempotency identity.
        deadline_seconds: Lifetime of the run.
        cost_budget: Optional cost ceiling for the run.
        at_time: Optional submission time; current UTC when omitted.

    Returns:
        A typed outcome carrying the reserved run identity, or a refusal.
    """
    now = at_time if at_time is not None else utc_now()
    operation = "submit_firm_request"
    failure = _admission(dependencies, auth, operation)
    if failure is not None:
        return _refused(operation, auth, failure, now)

    definition = dependencies.definitions.get(workflow_name)
    if definition is None:
        return _refused(
            operation,
            auth,
            ("WORKFLOW_NOT_REGISTERED", f"{workflow_name!r} is not registered."),
            now,
        )

    try:
        task = build_agent_task(
            {
                "created_at": now,
                "request_id": auth.request_id,
                "workflow_id": auth.workflow_id,
                "correlation_id": auth.correlation_id,
                "causation_id": None,
                "task_id": derive_stable_id("id", f"task:{idempotency_key}"),
                "workflow_name": workflow_name,
                "workflow_version": definition.version,
                "objective": objective,
                "input_refs": input_refs,
                "principal_id": auth.principal_id,
                "scope": {"environment": auth.tenant_or_environment},
                "deadline_at": now + timedelta(seconds=deadline_seconds),
                "idempotency_key": idempotency_key,
                "budgets": {"cost": cost_budget or Decimal("1.00")},
            },
        )
        run = submit_task(
            dependencies.workflow_store,
            definition,
            task,
            at_time=now,
        )
    except Exception as error:  # noqa: BLE001 - the boundary maps every failure.
        return _failed(operation, auth, error, now)

    logger.info("Operator submitted run %s for %s", run.run_id, auth.principal_id)
    return _outcome(
        operation,
        "ok",
        auth,
        now,
        payload={
            "run_id": run.run_id,
            "task_id": run.task_id,
            "state": run.state,
            "workflow_name": run.workflow_name,
            "workflow_version": run.workflow_version,
        },
    )


def get_firm_run(
    dependencies: AgenticDependencies,
    auth: AuthenticatedPrincipal,
    run_id: str,
    at_time: datetime | None = None,
) -> OperatorOutcome:
    """Inspect one run's durable state.

    Available while Agentic is disabled: understanding a stopped firm requires
    reading it.

    Args:
        dependencies: Explicit composition dependencies.
        auth: Authenticated principal.
        run_id: Run to inspect.
        at_time: Optional read time; current UTC when omitted.

    Returns:
        A typed outcome carrying the run's bounded state, or a refusal.
    """
    now = at_time if at_time is not None else utc_now()
    operation = "get_firm_run"
    failure = _admission(dependencies, auth, operation)
    if failure is not None:
        return _refused(operation, auth, failure, now)

    run = dependencies.workflow_store.load_run(run_id)
    if run is None:
        return _refused(
            operation,
            auth,
            ("RUN_NOT_FOUND", f"No Agentic run {run_id}."),
            now,
        )
    return _outcome(
        operation,
        "ok",
        auth,
        now,
        payload={
            "run_id": run.run_id,
            "task_id": run.task_id,
            "state": run.state,
            "current_node": run.current_node,
            "sequence": str(run.sequence),
            "terminal": str(is_terminal_state(run.state)),
            "terminal_reason": run.terminal_reason or "none",
        },
    )


def cancel_firm_run(
    dependencies: AgenticDependencies,
    auth: AuthenticatedPrincipal,
    run_id: str,
    reason: str = "OPERATOR_CANCELLED",
    at_time: datetime | None = None,
) -> OperatorOutcome:
    """Cancel one non-terminal run through the normal orchestration path.

    Args:
        dependencies: Explicit composition dependencies.
        auth: Authenticated principal.
        run_id: Run to cancel.
        reason: Enumerated cancellation reason.
        at_time: Optional cancellation time; current UTC when omitted.

    Returns:
        A typed outcome carrying the cancelled state, or a refusal.
    """
    now = at_time if at_time is not None else utc_now()
    operation = "cancel_firm_run"
    failure = _admission(dependencies, auth, operation)
    if failure is not None:
        return _refused(operation, auth, failure, now)

    run = dependencies.workflow_store.load_run(run_id)
    if run is None:
        return _refused(
            operation,
            auth,
            ("RUN_NOT_FOUND", f"No Agentic run {run_id}."),
            now,
        )
    if is_terminal_state(run.state):
        # A run that already stopped is not a failure to cancel; it is a run
        # that needs no cancelling, and reporting it as an internal error
        # would misdescribe an ordinary outcome.
        return _refused(
            operation,
            auth,
            (
                "RUN_ALREADY_TERMINAL",
                f"Run {run_id} is already {run.state} and needs no cancelling.",
            ),
            now,
        )
    task = _task_for(run, auth, now)
    try:
        cancelled = cancel_task(
            dependencies.workflow_store,
            run_id,
            task,
            reason=reason,
            at_time=now,
        )
    except Exception as error:  # noqa: BLE001 - the boundary maps every failure.
        return _failed(operation, auth, error, now)
    return _outcome(
        operation,
        "ok",
        auth,
        now,
        payload={"run_id": cancelled.run_id, "state": cancelled.state},
    )


def _task_for(
    run: WorkflowRun,
    auth: AuthenticatedPrincipal,
    at_time: datetime,
) -> AgentTask:
    """Rebuild the governed task envelope one run was submitted under.

    Args:
        run: Durable workflow run.
        auth: Authenticated principal.
        at_time: Operation time.

    Returns:
        A validated immutable agent task.
    """
    return build_agent_task(
        {
            "created_at": at_time,
            "request_id": auth.request_id,
            "workflow_id": auth.workflow_id,
            "correlation_id": auth.correlation_id,
            "causation_id": None,
            "task_id": run.task_id,
            "workflow_name": run.workflow_name,
            "workflow_version": run.workflow_version,
            "objective": "Operator-initiated control of an existing run.",
            "input_refs": (f"agentic.run:{run.run_id}",),
            "principal_id": auth.principal_id,
            "scope": {"environment": auth.tenant_or_environment},
            "deadline_at": at_time + timedelta(minutes=30),
            "idempotency_key": run.idempotency_key,
            "budgets": {"cost": Decimal("1.00")},
        },
    )


def approve_agentic_handoff(
    dependencies: AgenticDependencies,
    auth: AuthenticatedPrincipal,
    artifact_hash: str,
    artifact_id: str,
    rationale: str,
    at_time: datetime | None = None,
) -> OperatorOutcome:
    """Record an authenticated human approval of one staged artefact.

    The transition goes through the `FEAT-AGT-18` ledger, so the state machine,
    the append-only rule, and the non-inheritance rule all apply exactly as
    they would to any other transition.

    Args:
        dependencies: Explicit composition dependencies.
        auth: Authenticated principal.
        artifact_hash: Digest of the exact artefact.
        artifact_id: Artefact identity, for operator readability.
        rationale: Why the approval is being recorded.
        at_time: Optional approval time; current UTC when omitted.

    Returns:
        A typed outcome carrying the recorded transition, or a refusal.
    """
    now = at_time if at_time is not None else utc_now()
    operation = "approve_agentic_handoff"
    failure = _admission(dependencies, auth, operation)
    if failure is not None:
        return _refused(operation, auth, failure, now)
    if auth.principal_type != "USER":
        return _refused(
            operation,
            auth,
            (
                "APPROVAL_NOT_HUMAN",
                f"{auth.principal_type!r} cannot approve a handoff.",
            ),
            now,
        )

    blocked = can_transition(dependencies.lifecycle_store, artifact_hash, "approved")
    if blocked is not None:
        return _refused(operation, auth, ("TRANSITION_REFUSED", blocked), now)
    try:
        record = transition_artifact(
            dependencies.lifecycle_store,
            artifact_hash,
            artifact_id,
            "approved",
            auth.principal_id,
            rationale,
            at_time=now,
        )
    except Exception as error:  # noqa: BLE001 - the boundary maps every failure.
        return _failed(operation, auth, error, now)
    return _outcome(
        operation,
        "ok",
        auth,
        now,
        payload={
            "artifact_hash": record.artifact_hash,
            "state": record.state,
            "previous_state": record.previous_state or "none",
            "sequence": str(record.sequence),
        },
    )


def replay_firm_run(
    dependencies: AgenticDependencies,
    auth: AuthenticatedPrincipal,
    request: ReplayRequest,
    at_time: datetime | None = None,
) -> OperatorOutcome:
    """Validate one isolated replay and record it.

    This exposes `FEAT-AGT-21`'s validation to an operator. It executes
    nothing: the outcome reports `executed=False` because no path here can
    make it otherwise.

    Args:
        dependencies: Explicit composition dependencies.
        auth: Authenticated principal.
        request: Validated immutable replay request.
        at_time: Optional replay time; current UTC when omitted.

    Returns:
        A typed outcome carrying the replay verdict, or a refusal.
    """
    now = at_time if at_time is not None else utc_now()
    operation = "replay_firm_run"
    failure = _admission(dependencies, auth, operation)
    if failure is not None:
        return _refused(operation, auth, failure, now)

    try:
        outcome = replay_run(
            dependencies.operations_store,
            dependencies.memory_store,
            request,
            now,
        )
    except Exception as error:  # noqa: BLE001 - the boundary maps every failure.
        return _failed(operation, auth, error, now)
    return _outcome(
        operation,
        "ok",
        auth,
        now,
        payload={
            "replay_id": outcome.replay_id,
            "run_id": outcome.run_id,
            "environment": outcome.environment,
            "verified_references": str(len(outcome.verified_references)),
            "side_effects_attempted": str(outcome.side_effects_attempted),
            "executed": str(outcome.executed),
        },
    )


def quarantine_firm_agent(
    dependencies: AgenticDependencies,
    auth: AuthenticatedPrincipal,
    run_id: str,
    kind: IncidentKind,
    trigger: str,
    role_id: str,
    preserved_evidence_refs: tuple[str, ...],
    checkpoint_ref: str,
    at_time: datetime | None = None,
) -> OperatorOutcome:
    """Classify, contain, and record one incident from the operator boundary.

    Containment is derived from the incident kind by `FEAT-AGT-21`, so an
    operator reports what was observed and does not choose what happens.

    Args:
        dependencies: Explicit composition dependencies.
        auth: Authenticated principal.
        run_id: Run the incident occurred in.
        kind: Enumerated incident kind.
        trigger: Bounded description of what was observed.
        role_id: Role implicated by the incident.
        preserved_evidence_refs: Evidence kept for investigation.
        checkpoint_ref: Checkpoint preserved rather than dropped.
        at_time: Optional detection time; current UTC when omitted.

    Returns:
        A typed outcome carrying the containment, or a refusal.
    """
    now = at_time if at_time is not None else utc_now()
    operation = "quarantine_firm_agent"
    failure = _admission(dependencies, auth, operation)
    if failure is not None:
        return _refused(operation, auth, failure, now)

    run = dependencies.workflow_store.load_run(run_id)
    if run is None:
        return _refused(
            operation,
            auth,
            ("RUN_NOT_FOUND", f"No Agentic run {run_id}."),
            now,
        )
    try:
        incident = quarantine_agent(
            dependencies.operations_store,
            dependencies.workflow_store,
            run_id,
            _task_for(run, auth, now),
            kind,
            trigger,
            role_id,
            preserved_evidence_refs,
            checkpoint_ref,
            correlation_id=auth.correlation_id,
            at_time=now,
        )
    except Exception as error:  # noqa: BLE001 - the boundary maps every failure.
        return _failed(operation, auth, error, now)
    return _outcome(
        operation,
        "ok",
        auth,
        now,
        payload={
            "incident_id": incident.incident_id,
            "kind": incident.kind,
            "containment_action": incident.containment_action,
            "contained_state": incident.contained_state,
            "quarantined_role_id": incident.quarantined_role_id or "none",
            "preserved_evidence": str(len(incident.preserved_evidence_refs)),
        },
    )


def get_firm_audit(
    dependencies: AgenticDependencies,
    auth: AuthenticatedPrincipal,
    task_id: str,
    run_id: str,
    at_time: datetime | None = None,
) -> OperatorOutcome:
    """Return one run's correlated redacted trace.

    Available while Agentic is disabled, and preserved across disablement: the
    audit evidence `FR-AGENTIC-066` requires kept is the evidence this reads.

    Args:
        dependencies: Explicit composition dependencies.
        auth: Authenticated principal.
        task_id: Owning task identity.
        run_id: Run to audit.
        at_time: Optional read time; current UTC when omitted.

    Returns:
        A typed outcome carrying the bounded trace, or a refusal.
    """
    now = at_time if at_time is not None else utc_now()
    operation = "get_firm_audit"
    failure = _admission(dependencies, auth, operation)
    if failure is not None:
        return _refused(operation, auth, failure, now)

    try:
        trace = get_run_trace(
            dependencies.memory_store,
            task_id,
            run_id,
            auth.correlation_id,
            operations_store=dependencies.operations_store,
            at_time=now,
        )
    except Exception as error:  # noqa: BLE001 - the boundary maps every failure.
        return _failed(operation, auth, error, now)
    return _outcome(
        operation,
        "ok",
        auth,
        now,
        payload={
            "trace_hash": trace.trace_hash,
            "run_id": trace.run_id,
            "spans_covered": str(len(trace.spans)),
            "record_count": str(trace.record_count),
            "observed_cost": str(trace.observed_cost),
            "redacted_paths": str(len(trace.redacted_paths)),
        },
    )


def disable_agentic(
    dependencies: AgenticDependencies,
    auth: AuthenticatedPrincipal,
    run_ids: tuple[str, ...],
    policy: DrainPolicy = "drain",
    at_time: datetime | None = None,
) -> OperatorOutcome:
    """Stop the firm taking new work and settle what is already running.

    Disablement rejects new work through `_admission`; this operation settles
    the runs it was handed. `drain` lets non-terminal work finish; `cancel`
    stops it through the normal orchestration path. Nothing is written over the
    audit or operations stores in either case, and every deterministic domain
    is untouched — Agentic holds no kill switch, no risk approval, and no
    execution route to surrender.

    The run identities are supplied rather than enumerated: `FEAT-AGT-04`'s
    store port offers `load_run` and no listing, and widening a completed
    feature's port to make this convenient would be the wrong trade. The
    composition root that owns the store knows what is active.

    Args:
        dependencies: Explicit composition dependencies.
        auth: Authenticated principal.
        run_ids: Runs to settle.
        policy: Whether active work drains or is cancelled.
        at_time: Optional disablement time; current UTC when omitted.

    Returns:
        A typed outcome describing what was settled, or a refusal.
    """
    now = at_time if at_time is not None else utc_now()
    operation = "disable_agentic"
    # Disablement is itself a state change, so it needs the package enabled to
    # be meaningful; the admission check refuses a second disablement.
    failure = _admission(dependencies, auth, operation)
    if failure is not None:
        return _refused(operation, auth, failure, now)

    loaded = tuple(
        run
        for run in (dependencies.workflow_store.load_run(item) for item in run_ids)
        if run is not None
    )
    active = tuple(run for run in loaded if not is_terminal_state(run.state))
    cancelled = 0
    if policy == "cancel":
        for run in active:
            try:
                cancel_task(
                    dependencies.workflow_store,
                    run.run_id,
                    _task_for(run, auth, now),
                    reason="AGENTIC_DISABLED",
                    at_time=now,
                )
            except Exception as error:  # noqa: BLE001 - one run must not stop the rest.
                logger.warning(
                    "Run %s could not be cancelled during disablement: %s",
                    run.run_id,
                    map_exception(error)["code"],
                )
                continue
            cancelled += 1
    logger.info(
        "Agentic disablement settled %d active runs under the %s policy",
        len(active),
        policy,
    )
    return _outcome(
        operation,
        "ok",
        auth,
        now,
        payload={
            "policy": policy,
            "runs_examined": str(len(loaded)),
            "active_runs": str(len(active)),
            "cancelled_runs": str(cancelled),
            "drained_runs": str(len(active) - cancelled),
            # Disablement writes over nothing; the audit and operations stores
            # are untouched by this operation.
            "audit_preserved": "true",
        },
    )


def get_operator_operations() -> tuple[str, ...]:
    """Return every registered operator operation.

    Returns:
        Ordered operator operation names.
    """
    return tuple(sorted(OPERATOR_PERMISSIONS))
