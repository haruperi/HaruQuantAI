"""Authenticated operational workstation routes."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.services.api.identity import require_auth_context, require_human_permission
from app.services.api.widgets.operational.orchestration import (
    execute_workstation_command,
)

router = APIRouter(prefix="/api/v1/workstation", tags=["workstation"])


@router.get("", response_model=None)
def _read(
    request: Request,
    auth: Annotated[Any, Depends(require_auth_context)],  # noqa: ANN401
) -> object:
    """Read the composed versioned workstation projection.

    Returns:
        Owner-provided read model.

    Raises:
        HTTPException: If authorization or composition fails.
    """
    require_human_permission(auth, "workstation:read")
    source = getattr(request.app.state, "workstation_read_source", None)
    if not callable(source):
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "WORKSTATION_PROVIDER_UNAVAILABLE"
        )
    return source()


@router.post("/commands", response_model=None)
def _command(
    request: Request,
    body: dict[str, object],
    auth: Annotated[Any, Depends(require_auth_context)],  # noqa: ANN401
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Execute one authorized optimistic workstation command.

    Returns:
        Stable command outcome.

    Raises:
        HTTPException: If authorization, evidence, or composition fails.
    """
    require_human_permission(auth, "workstation:command")
    if not idempotency_key:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "IDEMPOTENCY_KEY_REQUIRED"
        )
    handler = getattr(request.app.state, "workstation_command_source", None)
    version = getattr(request.app.state, "workstation_version", None)
    if not callable(handler) or not isinstance(version, int):
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "WORKSTATION_PROVIDER_UNAVAILABLE"
        )
    command = {**body, "idempotency_key": idempotency_key}
    return execute_workstation_command(
        command, current_version=version, owner_handler=handler
    )
