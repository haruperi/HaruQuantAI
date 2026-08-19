"""Authenticated Risk HTTP boundaries.

Kill-switch state and immutable decision records are read-only projections.
The kill-switch command is the single governed Risk write exposed by backend v1:
it requires an authenticated human operator, an exact permission, a durable
idempotency key, and a distinct-principal approval attestation. Risk validates
the attestation and remains the sole authority over canonical safety state — the
gateway can request a transition but can never decide, override, or clear one.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.services.api.identity import (
    require_auth_context,
    require_human_permission,
    run_idempotent_write,
)
from app.services.api.widgets.risk.schemas import (
    KillSwitchCommandRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
)
from app.utils import generate_id

type AuthContext = Any
type _RiskSource = Callable[[str, Mapping[str, object], AuthContext], object]
type _RiskCommandSource = Callable[..., object]

router = APIRouter(prefix="/api/v1/risk", tags=["risk"])
_MAX_IDEMPOTENCY_KEY_LENGTH = 200


def _risk_source() -> _RiskSource:
    """Fail closed until canonical composition injects Risk reads.

    Raises:
        HTTPException: Always, when the source is not composed.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="RISK_READ_SOURCE_UNAVAILABLE",
    )


def _risk_command_source() -> _RiskCommandSource:
    """Fail closed until composition injects kill-switch command authority.

    Raises:
        HTTPException: Always, when the source is not composed.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="RISK_COMMAND_RUNTIME_UNAVAILABLE",
    )


@router.get("/kill-switch", response_model=None)
def _get_kill_switch(
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_RiskSource, Depends(_risk_source)],
    scope_level: Annotated[
        Literal["global", "portfolio", "strategy", "symbol"], Query()
    ] = "global",
    scope: Annotated[str | None, Query(max_length=200)] = None,
) -> object:
    """Read the current exact-scope canonical kill-switch state.

    Returns:
        Risk-owned kill-switch state.

    Raises:
        HTTPException: If authorization, scope validation, or lookup fails.
    """
    require_human_permission(auth, "risk:read")
    if scope_level != "global" and not scope:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="RISK_SCOPE_REQUIRED",
        )
    result = source(
        "kill-switch",
        {
            "scope_level": scope_level,
            "scope": {} if scope is None else {scope_level: scope},
        },
        auth,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="KILL_SWITCH_STATE_NOT_FOUND",
        )
    return result


@router.get("/decisions", response_model=None)
def _list_decisions(
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_RiskSource, Depends(_risk_source)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> Sequence[object]:
    """Return a bounded newest-first canonical Risk decision page.

    Returns:
        Risk-owned immutable decision records.

    Raises:
        HTTPException: If authentication or authorization fails.
    """
    require_human_permission(auth, "risk:read")
    result = source("decisions", {"limit": limit}, auth)
    if not isinstance(result, Sequence):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RISK_DECISIONS_INVALID",
        )
    return tuple(result)


@router.post("/kill-switch", response_model=None)
def _apply_kill_switch(
    request: KillSwitchCommandRequest,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_RiskCommandSource, Depends(_risk_command_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Request one governed canonical kill-switch transition from Risk.

    Returns:
        Risk-authored canonical kill-switch state.

    Raises:
        HTTPException: If authentication, authorization, idempotency, the
            required attestation, or composition fails.
        RuntimeError: If Risk reports an unexpected runtime failure.
    """
    require_human_permission(auth, "risk:kill_switch")
    if (
        idempotency_key is None
        or not idempotency_key.strip()
        or len(idempotency_key) > _MAX_IDEMPOTENCY_KEY_LENGTH
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="IDEMPOTENCY_KEY_REQUIRED",
        )
    if request.attestation is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="GOVERNANCE_REQUIRED",
        )
    try:
        return run_idempotent_write(
            principal_id=auth.principal_id,
            method="POST",
            route="/api/v1/risk/kill-switch",
            key=idempotency_key,
            request_material=request.model_dump(mode="json"),
            request_id=generate_id("req"),
            operation=lambda: source("kill_switch", request, auth, request.attestation),
        )
    except RuntimeError as error:
        if str(error) not in {
            "RISK_COMMAND_RUNTIME_UNAVAILABLE",
            "KILL_SWITCH_STATE_UNAVAILABLE",
        }:
            raise
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


__all__ = ("router",)
