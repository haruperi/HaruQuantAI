"""Authenticated versioned user-settings HTTP routes."""

from collections.abc import Mapping
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field

from app.services.api.identity import (
    IdentityError,
    finalize_idempotency_key,
    get_system_credential_statuses,
    get_system_settings,
    get_system_settings_manifest,
    get_user_settings,
    require_auth_context,
    require_permission,
    reserve_idempotency_key,
    store_system_credential,
    update_system_settings,
    update_user_settings,
)
from app.utils import canonical_digest, canonical_json, generate_id

type AuthContext = Any

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


class _SettingsUpdate(BaseModel):
    """Complete settings replacement request."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    settings: Mapping[str, str]
    expected_version: int = Field(ge=0)
    scope: Literal["system", "user"] = "user"


class _CredentialUpdate(BaseModel):
    """Complete write-only material for one approved credential slot."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    material: Mapping[str, str]


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


@router.get("/manifest")
def _get_system_manifest(
    context: Annotated[AuthContext, Depends(require_auth_context)],
) -> object:
    """Read secret-free definitions for administrator settings fields.

    Returns:
        Ordered settings manifest mappings.

    Raises:
        IdentityError: If the caller lacks administrator permission.
    """
    require_permission(context, "settings:admin")
    # FastAPI's serializer does not support MappingProxyType directly.
    return [dict(definition) for definition in get_system_settings_manifest()]


@router.get("/credentials")
def _get_credential_statuses(
    context: Annotated[AuthContext, Depends(require_auth_context)],
) -> object:
    """Read write-only credential slot status without protected values.

    Returns:
        Ordered secret-free credential status mappings.

    Raises:
        IdentityError: If the caller lacks administrator permission.
    """
    require_permission(context, "settings:admin")
    return get_system_credential_statuses(request_id=generate_id("req"))


def _credential_key_material(request: Request) -> tuple[Mapping[str, bytes], str]:
    """Read externally provisioned credential-encryption keys from app state.

    Args:
        request: Active HTTP request.

    Returns:
        Key set and explicit active key identifier.

    Raises:
        HTTPException: If encryption-key bootstrap is unavailable.
    """
    key_set = getattr(request.app.state, "api_credential_key_set", None)
    active_key_id = getattr(request.app.state, "api_active_credential_key_id", None)
    if not isinstance(key_set, Mapping) or not isinstance(active_key_id, str):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CREDENTIAL_KEY_BOOTSTRAP_UNAVAILABLE",
        )
    if any(
        not isinstance(name, str) or not isinstance(value, bytes)
        for name, value in key_set.items()
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CREDENTIAL_KEY_BOOTSTRAP_INVALID",
        )
    return key_set, active_key_id


@router.put("/credentials/{slot}")
def _put_credential(
    slot: str,
    body: _CredentialUpdate,
    request: Request,
    context: Annotated[AuthContext, Depends(require_auth_context)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Idempotently replace one write-only encrypted credential slot.

    Returns:
        Secret-free persisted credential metadata.

    Raises:
        HTTPException: If authority, idempotency, key bootstrap, or storage fails.
    """
    require_permission(context, "settings:admin")
    if idempotency_key is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="IDEMPOTENCY_KEY_REQUIRED",
        )
    request_id = generate_id("req")
    route = "/api/v1/settings/credentials/{slot}"
    key_set, active_key_id = _credential_key_material(request)
    try:
        decision = reserve_idempotency_key(
            principal_id=context.principal_id,
            method="PUT",
            route=route,
            key=idempotency_key,
            request_material={
                "slot": slot,
                "material_digest": canonical_digest(body.material),
            },
            request_id=request_id,
        )
        if decision.state == "replay":
            return next(
                item
                for item in get_system_credential_statuses(request_id=request_id)
                if item["slot"] == slot
            )
        record = store_system_credential(
            slot,
            body.material,
            key_set=key_set,
            active_key_id=active_key_id,
            request_id=request_id,
        )
        response = {
            "slot": slot,
            "configured": True,
            "version": record.version,
            "updated_at": record.created_at.isoformat(),
            "activation": "restart_required",
        }
        finalize_idempotency_key(
            principal_id=context.principal_id,
            method="PUT",
            route=route,
            key=idempotency_key,
            response_json=canonical_json(response),
            status_code=status.HTTP_200_OK,
            request_id=request_id,
        )
        return response
    except (IdentityError, StopIteration) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                str(error)
                if isinstance(error, IdentityError)
                else "CREDENTIAL_SLOT_UNKNOWN"
            ),
        ) from error


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
