"""Authenticated operator evidence and approval boundary."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from app.services.api.identity import (
    create_approval,
    require_auth_context,
    require_human_permission,
)

type AuthContext = Any
type OperationalEvent = Any
type _AuditSource = Callable[[AuthContext, int], Sequence[Any]]
type _EventSource = Callable[[AuthContext], Sequence[OperationalEvent]]

router = APIRouter(prefix="/api/v1/operator", tags=["operator"])


class _ApprovalRequest(BaseModel):
    """Scoped UI/API-owned human approval request."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    subject_id: str = Field(min_length=1, max_length=200)
    scope: str = Field(min_length=1, max_length=200)
    evidence: Mapping[str, object]
    ttl_seconds: int = Field(ge=1, le=86_400)


def _audit_source() -> _AuditSource:
    """Fail closed until composition injects the Data audit query.

    Raises:
        HTTPException: Always when the audit query is unavailable.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="AUDIT_QUERY_UNAVAILABLE",
    )


def _event_source() -> _EventSource:
    """Fail closed until composition injects the Trading event view.

    Raises:
        HTTPException: Always when the event view is unavailable.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="OPERATIONAL_EVENTS_UNAVAILABLE",
    )


@router.get("/audit-events", response_model=None)
def _get_audit_events(
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_AuditSource, Depends(_audit_source)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> Sequence[Any]:
    """Return a protected bounded Data-owned audit page.

    Args:
        auth: Authenticated operator.
        source: Injected Data audit-query boundary.
        limit: Bounded requested page size.

    Returns:
        Owner-produced audit events.
    """
    require_human_permission(auth, "ops:audit:read")
    return tuple(source(auth, limit))


@router.get("/events", response_model=tuple[OperationalEvent, ...])
def _get_events(
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_EventSource, Depends(_event_source)],
) -> tuple[OperationalEvent, ...]:
    """Return protected bounded Trading operational events.

    Args:
        auth: Authenticated operator.
        source: Injected Trading event view.

    Returns:
        Owner-produced operational events.
    """
    require_human_permission(auth, "ops:events:read")
    return tuple(source(auth))


@router.post("/approvals", response_model=None)
def _create_approval(
    request: _ApprovalRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
) -> object:
    """Persist one distinct-principal scoped operator approval.

    Args:
        request: Exact subject, scope, evidence, and expiry.
        auth: Authenticated human approver.

    Returns:
        Secret-free UI/API approval record.
    """
    require_human_permission(auth, "ops:approve")
    return create_approval(
        issuer_id=auth.principal_id,
        subject_id=request.subject_id,
        scope=request.scope,
        evidence=request.evidence,
        ttl_seconds=request.ttl_seconds,
        request_id=auth.request_id,
    )


__all__ = ("router",)
