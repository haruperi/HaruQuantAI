"""Authenticated Agentic operator HTTP boundaries.

Backend v1 exposes the Agentic reserve/inspect/audit/governance tier: submit
(reserve, never execute), inspect, cancel, replay (validate-only), audit,
approve-handoff, quarantine, and disable (the firm kill switch). Every route
delegates exactly once to the Agentic public operator surface through the
composed dependency bundle; when no bundle is composed the route fails closed
with HTTP 503.

The firm has never run for real (``app/agentic/public_api/README.md`` §1):
``submit`` reserves a run identifier and ``replay`` validates references, but
neither executes agents. Reads (``inspect`` and ``audit``) stay available while
the firm is disabled so an operator can understand why it was stopped.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Any, NoReturn

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Query,
    status,
)

from app.services.api.identity import (
    require_auth_context,
    require_human_permission,
    run_idempotent_write,
)
from app.services.api.workstation.agentic.schemas import (
    AgenticDisableRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
    AgenticHandoffApprovalRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
    AgenticQuarantineRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
    AgenticRunSubmitRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
)
from app.utils import generate_id

type AuthContext = Any
type _AgenticSource = Callable[..., object]

router = APIRouter(prefix="/api/v1/agentic", tags=["agentic"])
_RUNTIME_UNAVAILABLE = "AGENTIC_RUNTIME_UNAVAILABLE"
_MAX_IDEMPOTENCY_KEY_LENGTH = 200


def _agentic_source() -> _AgenticSource:
    """Fail closed until canonical composition injects Agentic operations.

    Raises:
        HTTPException: Always, when the source is not composed.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=_RUNTIME_UNAVAILABLE,
    )


def _require_idempotency(value: str | None) -> str:
    """Require a bounded non-empty HTTP idempotency key.

    Args:
        value: Caller-supplied idempotency key header value.

    Returns:
        Validated idempotency key.

    Raises:
        HTTPException: If the key is absent, blank, or oversized.
    """
    if value is None or not value.strip() or len(value) > _MAX_IDEMPOTENCY_KEY_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="IDEMPOTENCY_KEY_REQUIRED",
        )
    return value


def _runtime_unavailable(error: RuntimeError) -> NoReturn:
    """Translate the unavailable sentinel into HTTP 503.

    Args:
        error: Caught runtime error.

    Raises:
        HTTPException: When the error is the unavailable sentinel.
        RuntimeError: Any other runtime error, re-raised unchanged.
    """
    if str(error) != _RUNTIME_UNAVAILABLE:
        raise error
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=str(error),
    ) from error


@router.post("/runs", response_model=None)
def _submit_run(
    request: AgenticRunSubmitRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_AgenticSource, Depends(_agentic_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Reserve one governed Agentic run without executing it.

    Returns:
        Agentic ``OperatorOutcome`` typed outcome envelope.

    Raises:
        HTTPException: If authorization, idempotency, or composition fails.
    """
    require_human_permission(auth, "agentic:submit")
    key = _require_idempotency(idempotency_key)
    try:
        return run_idempotent_write(
            principal_id=auth.principal_id,
            method="POST",
            route="/api/v1/agentic/runs",
            key=key,
            request_material=request.model_dump(mode="json"),
            request_id=generate_id("req"),
            operation=lambda: source(
                "submit",
                auth,
                request.workflow_name,
                request.objective,
                request.input_refs,
                idempotency_key,
                request.deadline_seconds,
                request.cost_budget,
                None,
            ),
        )
    except RuntimeError as error:
        _runtime_unavailable(error)


@router.get("/runs/{run_id}", response_model=None)
def _get_run(
    run_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_AgenticSource, Depends(_agentic_source)],
) -> object:
    """Inspect one Agentic run's durable state.

    Returns:
        Agentic ``OperatorOutcome`` typed outcome envelope.

    Raises:
        HTTPException: If authorization or composition fails.
    """
    require_human_permission(auth, "agentic:read_run")
    try:
        return source("inspect", auth, run_id, None)
    except RuntimeError as error:
        _runtime_unavailable(error)


@router.delete("/runs/{run_id}", response_model=None)
def _cancel_run(
    run_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_AgenticSource, Depends(_agentic_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Cancel one non-terminal Agentic run.

    Returns:
        Agentic ``OperatorOutcome`` typed outcome envelope.

    Raises:
        HTTPException: If authorization, idempotency, or composition fails.
    """
    require_human_permission(auth, "agentic:cancel_run")
    key = _require_idempotency(idempotency_key)
    try:
        return run_idempotent_write(
            principal_id=auth.principal_id,
            method="DELETE",
            route="/api/v1/agentic/runs/{run_id}",
            key=key,
            request_material={"run_id": run_id},
            request_id=generate_id("req"),
            operation=lambda: source(
                "cancel", auth, run_id, "OPERATOR_CANCELLED", None
            ),
        )
    except RuntimeError as error:
        _runtime_unavailable(error)


@router.get("/runs/{run_id}/audit", response_model=None)
def _audit_run(
    run_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_AgenticSource, Depends(_agentic_source)],
    task_id: Annotated[str, Query(min_length=1, max_length=200, alias="task_id")],
) -> object:
    """Return one Agentic run's correlated redacted audit trace.

    Returns:
        Agentic ``OperatorOutcome`` typed outcome envelope.

    Raises:
        HTTPException: If authorization or composition fails.
    """
    require_human_permission(auth, "agentic:read_audit")
    try:
        return source("audit", auth, task_id, run_id, None)
    except RuntimeError as error:
        _runtime_unavailable(error)


@router.post("/handoffs/approve", response_model=None)
def _approve_handoff(
    request: AgenticHandoffApprovalRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_AgenticSource, Depends(_agentic_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Record one authenticated human approval of a staged Agentic artefact.

    Returns:
        Agentic ``OperatorOutcome`` typed outcome envelope.

    Raises:
        HTTPException: If authorization, idempotency, or composition fails.
    """
    require_human_permission(auth, "agentic:approve_promotion")
    key = _require_idempotency(idempotency_key)
    try:
        return run_idempotent_write(
            principal_id=auth.principal_id,
            method="POST",
            route="/api/v1/agentic/handoffs/approve",
            key=key,
            request_material=request.model_dump(mode="json"),
            request_id=generate_id("req"),
            operation=lambda: source(
                "approve",
                auth,
                request.artifact_hash,
                request.artifact_id,
                request.rationale,
                None,
            ),
        )
    except RuntimeError as error:
        _runtime_unavailable(error)


@router.post("/incidents/quarantine", response_model=None)
def _quarantine_agent(
    request: AgenticQuarantineRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_AgenticSource, Depends(_agentic_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Classify, contain, and record one Agentic incident.

    Returns:
        Agentic ``OperatorOutcome`` typed outcome envelope.

    Raises:
        HTTPException: If authorization, idempotency, or composition fails.
    """
    require_human_permission(auth, "agentic:operate")
    key = _require_idempotency(idempotency_key)
    try:
        return run_idempotent_write(
            principal_id=auth.principal_id,
            method="POST",
            route="/api/v1/agentic/incidents/quarantine",
            key=key,
            request_material=request.model_dump(mode="json"),
            request_id=generate_id("req"),
            operation=lambda: source(
                "quarantine",
                auth,
                request.run_id,
                request.kind,
                request.trigger,
                request.role_id,
                request.preserved_evidence_refs,
                request.checkpoint_ref,
                None,
            ),
        )
    except RuntimeError as error:
        _runtime_unavailable(error)


@router.post("/disable", response_model=None)
def _disable_agentic(
    request: AgenticDisableRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_AgenticSource, Depends(_agentic_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Stop the Agentic firm taking new work and settle running work.

    The firm kill switch: new work is refused through the operator admission
    gate and the named runs are settled under the chosen drain or cancel
    policy. Nothing is written over the audit or operations stores.

    Returns:
        Agentic ``OperatorOutcome`` typed outcome envelope.

    Raises:
        HTTPException: If authorization, idempotency, or composition fails.
    """
    require_human_permission(auth, "agentic:operate")
    key = _require_idempotency(idempotency_key)
    try:
        return run_idempotent_write(
            principal_id=auth.principal_id,
            method="POST",
            route="/api/v1/agentic/disable",
            key=key,
            request_material=request.model_dump(mode="json"),
            request_id=generate_id("req"),
            operation=lambda: source(
                "disable", auth, request.run_ids, request.policy, None
            ),
        )
    except RuntimeError as error:
        _runtime_unavailable(error)


__all__ = ("router",)
