"""Authenticated operator kill-switch and protected evidence boundary."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, model_validator

from app.services.api.alerts import (
    CriticalAlertDeliveryResult,
    CriticalAlertSink,
    CriticalOperationalAlert,
    build_kill_switch_activation_alert,
    deliver_critical_alert,
)
from app.services.api.identity import require_auth_context, require_human_permission
from app.services.risk import (
    ApprovalAttestation,
    KillSwitchCommand,
    KillSwitchState,
    RiskDomainError,
)
from app.services.trading import OperationalEvent
from app.utils import AuditEvent, AuthContext, logger

type _KillSwitchTransition = Callable[
    [KillSwitchCommand, AuthContext, ApprovalAttestation | None],
    KillSwitchState,
]
type _ReadinessSource = Callable[[AuthContext], Mapping[str, str]]
type _AuditSource = Callable[[AuthContext, int], Sequence[AuditEvent]]
type _EventSource = Callable[[AuthContext], Sequence[OperationalEvent]]

router = APIRouter(prefix="/api/operator", tags=["operator"])


class _OperatorKillSwitchRequest(BaseModel):
    """Receiver-owned operator input for one scoped Risk transition."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: Literal["activate", "clear"]
    scope_level: Literal["global", "portfolio", "strategy", "symbol"]
    portfolio_id: str | None = None
    strategy_id: str | None = None
    symbol: str | None = None
    reason: str
    requested_at: datetime
    attestation: _OperatorApprovalAttestation | None = None

    @model_validator(mode="after")
    def _validate_closed_values(self) -> _OperatorKillSwitchRequest:
        """Validate the closed command and scope values.

        Returns:
            Validated request.

        Raises:
            ValueError: If action or scope is unsupported.
        """
        if self.action not in {"activate", "clear"}:
            raise ValueError("action must be activate or clear")
        if self.scope_level not in {"global", "portfolio", "strategy", "symbol"}:
            raise ValueError("scope_level is invalid")
        required_scope = {
            "portfolio": self.portfolio_id,
            "strategy": self.strategy_id,
            "symbol": self.symbol,
        }.get(self.scope_level)
        if self.scope_level != "global" and required_scope is None:
            raise ValueError("scoped commands require their matching identifier")
        return self


class _OperatorApprovalAttestation(BaseModel):
    """JSON-facing exact representation of Risk approval evidence."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_version: Literal["v1"] = "v1"
    schema_id: Literal["risk.approval_attestation.v1"] = "risk.approval_attestation.v1"
    attestation_id: str
    principal_id: str
    action: str
    scope: Mapping[str, str]
    policy_ref: str
    policy_version: str
    issued_at: datetime
    expires_at: datetime
    request_id: str
    workflow_id: str
    correlation_id: str

    @model_validator(mode="after")
    def _validate_owner_contract(self) -> _OperatorApprovalAttestation:
        """Validate the decoded JSON against the Risk-owned contract.

        Returns:
            Validated JSON-facing attestation.

        Raises:
            ValueError: If Risk rejects the decoded evidence.
        """
        ApprovalAttestation.model_validate(self.model_dump())
        return self

    def to_contract(self) -> ApprovalAttestation:
        """Return the canonical Risk-owned approval contract.

        Returns:
            Validated Risk approval attestation.
        """
        return ApprovalAttestation.model_validate(self.model_dump())


class _OperatorKillSwitchResponse(BaseModel):
    """Operator-visible canonical state and optional alert-delivery evidence."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    state: KillSwitchState
    alert: CriticalOperationalAlert | None
    delivery: CriticalAlertDeliveryResult | None


def _kill_switch_transition() -> _KillSwitchTransition:
    """Fail closed until composition injects the Risk transition.

    Raises:
        HTTPException: Always when no transition boundary is configured.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="RISK_KILL_SWITCH_UNAVAILABLE",
    )


def _unavailable_alert_sink(
    alert: CriticalOperationalAlert,
    *,
    idempotency_key: str,
) -> None:
    """Represent unavailable alert delivery without blocking Risk activation.

    Args:
        alert: Validated critical alert.
        idempotency_key: Deterministic alert identity.

    Raises:
        RuntimeError: Always so delivery returns structured failure evidence.
    """
    del alert, idempotency_key
    raise RuntimeError("critical alert sink unavailable")


def _critical_alert_sink() -> CriticalAlertSink:
    """Return the default fail-visible alert sink.

    Returns:
        Sink that reports unavailability through delivery evidence.
    """
    return _unavailable_alert_sink


def _readiness_source() -> _ReadinessSource:
    """Fail closed until composition injects protected readiness.

    Raises:
        HTTPException: Always when readiness is unavailable.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="READINESS_UNAVAILABLE",
    )


def _audit_source() -> _AuditSource:
    """Fail closed until composition injects the Data-owned audit query.

    Raises:
        HTTPException: Always when audit query is unavailable.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="AUDIT_QUERY_UNAVAILABLE",
    )


def _event_source() -> _EventSource:
    """Fail closed until composition injects the Trading event view.

    Raises:
        HTTPException: Always when events are unavailable.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="OPERATIONAL_EVENTS_UNAVAILABLE",
    )


def _scope(request: _OperatorKillSwitchRequest) -> dict[str, str]:
    """Derive the exact Risk scope mapping.

    Args:
        request: Validated operator request.

    Returns:
        Canonical Risk scope mapping.
    """
    values = {
        "portfolio": request.portfolio_id,
        "strategy": request.strategy_id,
        "symbol": request.symbol,
    }
    value = values.get(request.scope_level)
    return {} if request.scope_level == "global" else {request.scope_level: str(value)}


def _validate_clearance(
    request: _OperatorKillSwitchRequest,
    auth: AuthContext,
    attestation: ApprovalAttestation | None,
) -> None:
    """Reject incomplete or same-principal clearance before Risk delegation.

    Args:
        request: Validated operator request.
        auth: Authenticated command principal.
        attestation: Canonical optional Risk clearance evidence.

    Raises:
        HTTPException: If clearance evidence is absent or incompatible.
    """
    if request.action != "clear":
        return
    if attestation is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="CLEARANCE_ATTESTATION_REQUIRED",
        )
    expected_scope = _scope(request) or {"global": "*"}
    if attestation.principal_id == auth.principal_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="DISTINCT_PRINCIPAL_REQUIRED",
        )
    if (
        attestation.action != "risk.kill.clear"
        or dict(attestation.scope) != expected_scope
        or attestation.request_id != auth.request_id
        or attestation.workflow_id != auth.workflow_id
        or attestation.correlation_id != auth.correlation_id
        or not (attestation.issued_at <= request.requested_at < attestation.expires_at)
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="CLEARANCE_ATTESTATION_MISMATCH",
        )


@router.post("/kill-switch", response_model=_OperatorKillSwitchResponse)
def _apply_kill_switch(
    request: _OperatorKillSwitchRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    transition: Annotated[_KillSwitchTransition, Depends(_kill_switch_transition)],
    alert_sink: Annotated[CriticalAlertSink, Depends(_critical_alert_sink)],
) -> _OperatorKillSwitchResponse:
    """Delegate one authorized scoped command to canonical Risk authority.

    Args:
        request: Receiver-owned operator input.
        auth: Authenticated command principal and trace.
        transition: Injected Risk-owned transition boundary.
        alert_sink: Injected channel-neutral alert sink.

    Returns:
        Canonical state plus visible activation alert-delivery evidence.

    Raises:
        HTTPException: If authorization, clearance, or Risk delegation fails.
    """
    permission = (
        "risk.kill.activate" if request.action == "activate" else "risk.kill.clear"
    )
    require_human_permission(auth, permission)
    attestation = (
        None if request.attestation is None else request.attestation.to_contract()
    )
    _validate_clearance(request, auth, attestation)
    try:
        command = KillSwitchCommand(
            action=request.action,
            scope_level=request.scope_level,
            portfolio_id=request.portfolio_id,
            strategy_id=request.strategy_id,
            symbol=request.symbol,
            reason=request.reason,
            requested_at=request.requested_at,
            request_id=auth.request_id,
            workflow_id=auth.workflow_id,
            correlation_id=auth.correlation_id,
        )
        state = transition(command, auth, attestation)
    except RiskDomainError as error:
        logger.warning("Risk rejected operator kill-switch command")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=error.risk_code.value,
        ) from error
    if state.state != "active":
        return _OperatorKillSwitchResponse(state=state, alert=None, delivery=None)
    alert = build_kill_switch_activation_alert(state, auth)
    delivery = deliver_critical_alert(alert, alert_sink)
    return _OperatorKillSwitchResponse(
        state=state,
        alert=alert,
        delivery=delivery,
    )


@router.get("/readiness", response_model=dict[str, str])
def _get_readiness(
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_ReadinessSource, Depends(_readiness_source)],
) -> dict[str, str]:
    """Return protected bounded readiness evidence.

    Args:
        auth: Authenticated operator.
        source: Injected readiness source.

    Returns:
        Bounded readiness mapping.
    """
    require_human_permission(auth, "ops:read")
    return dict(source(auth))


@router.get("/audit-events", response_model=tuple[AuditEvent, ...])
def _get_audit_events(
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_AuditSource, Depends(_audit_source)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> tuple[AuditEvent, ...]:
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


__all__ = ("router",)
