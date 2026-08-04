"""Authenticated versioned user-settings HTTP routes."""

from collections.abc import Mapping
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from app.services.api.identity import (
    IdentityError,
    finalize_idempotency_key,
    get_system_settings,
    get_user_settings,
    require_auth_context,
    require_permission,
    reserve_idempotency_key,
    update_system_settings,
    update_user_settings,
)
from app.utils import canonical_json, generate_id

type AuthContext = Any

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


class _SettingsUpdate(BaseModel):
    """Complete settings replacement request."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    settings: Mapping[str, str]
    expected_version: int = Field(ge=0)
    scope: Literal["system", "user"] = "user"


@router.get("")
def _get_settings(
    context: Annotated[AuthContext, Depends(require_auth_context)],
    scope: Literal["system", "user"] = "user",
) -> object:
    """Read authenticated user or authorized global system settings.

    Returns:
        Current versioned settings record.

    Raises:
        IdentityError: If the caller lacks settings read permission.
    """
    if scope == "system":
        require_permission(context, "settings:admin")
        return get_system_settings(request_id=generate_id("req"))
    require_permission(context, "settings:read")
    return get_user_settings(context.principal_id, request_id=generate_id("req"))


@router.put("")
def _put_settings(
    body: _SettingsUpdate,
    context: Annotated[AuthContext, Depends(require_auth_context)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Idempotently replace authenticated user settings.

    Returns:
        Updated versioned settings record.

    Raises:
        HTTPException: If idempotency or optimistic version validation fails.
    """
    permission = "settings:admin" if body.scope == "system" else "settings:write"
    require_permission(context, permission)
    if idempotency_key is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="IDEMPOTENCY_KEY_REQUIRED",
        )
    request_id = generate_id("req")
    try:
        decision = reserve_idempotency_key(
            principal_id=context.principal_id,
            method="PUT",
            route="/api/v1/settings",
            key=idempotency_key,
            request_material=body.model_dump(mode="json"),
            request_id=request_id,
        )
        if decision.state == "replay":
            if body.scope == "system":
                return get_system_settings(request_id=request_id)
            return get_user_settings(context.principal_id, request_id=request_id)
        if body.scope == "system":
            updated = update_system_settings(
                body.settings,
                actor_id=context.principal_id,
                expected_version=body.expected_version,
                request_id=request_id,
            )
        else:
            updated = update_user_settings(
                context.principal_id,
                body.settings,
                expected_version=body.expected_version,
                request_id=request_id,
            )
        finalize_idempotency_key(
            principal_id=context.principal_id,
            method="PUT",
            route="/api/v1/settings",
            key=idempotency_key,
            response_json=canonical_json(updated.model_dump(mode="json")),
            status_code=status.HTTP_200_OK,
            request_id=request_id,
        )
        return updated
    except IdentityError as error:
        code = str(error)
        status_code = (
            status.HTTP_409_CONFLICT
            if code.endswith("CONFLICT")
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        raise HTTPException(status_code=status_code, detail=code) from error


__all__ = ("router",)
