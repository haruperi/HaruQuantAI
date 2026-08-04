"""Authenticated read-only Risk HTTP boundaries."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.services.api.identity import require_auth_context, require_human_permission

type AuthContext = Any
type _RiskSource = Callable[[str, Mapping[str, object], AuthContext], object]

router = APIRouter(prefix="/api/v1/risk", tags=["risk"])


def _risk_source() -> _RiskSource:
    """Fail closed until canonical composition injects Risk reads.

    Raises:
        HTTPException: Always, when the source is not composed.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="RISK_READ_SOURCE_UNAVAILABLE",
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


__all__ = ("router",)
