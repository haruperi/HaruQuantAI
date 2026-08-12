"""Thin authenticated account-watchlist HTTP routes.

Every read and write delegates to the Watchlists-owned operations,
which own seeding, ownership checks, and the "exactly one default per
account" invariant. The gateway resolves the active runtime broker (the same
composition-layer resolver the Markets route uses) so callers never name a
``source_id`` of their own, then does a bounded HTTP idempotency check for
mutations and nothing else.
"""

from typing import Annotated, Any, NoReturn

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.services.api.identity import (
    IdentityError,
    finalize_idempotency_key,
    require_auth_context,
    require_permission,
    reserve_idempotency_key,
)
from app.services.api.workstation.watchlists.orchestration import (
    create_watchlist,
    delete_watchlist,
    get_watchlist,
    list_runtime_watchlists,
    update_watchlist,
)
from app.services.api.workstation.watchlists.schemas import (
    _WatchlistCreate,  # noqa: TC001 - FastAPI resolves request models at runtime
    _WatchlistUpdate,  # noqa: TC001 - FastAPI resolves request models at runtime
)
from app.utils import canonical_json, generate_id

type AuthContext = Any

router = APIRouter(prefix="/api/v1/watchlists", tags=["watchlists"])

_NOT_FOUND_CODES = frozenset({"WATCHLIST_NOT_FOUND"})
_CONFLICT_CODES = frozenset(
    {"WATCHLIST_NAME_CONFLICT", "WATCHLIST_DEFAULT_UNDELETABLE"}
)
_VALIDATION_CODES = frozenset({"WATCHLIST_LIMIT_EXCEEDED"})


def _raise_for_identity_error(error: IdentityError) -> NoReturn:
    """Map one watchlist ``IdentityError`` to a structured HTTP failure.

    Raises:
        HTTPException: Always, with a status matching the error's category.
    """
    code = str(error)
    if code in _NOT_FOUND_CODES:
        status_code = status.HTTP_404_NOT_FOUND
    elif code in _CONFLICT_CODES:
        status_code = status.HTTP_409_CONFLICT
    elif code in _VALIDATION_CODES:
        status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    else:
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    raise HTTPException(status_code=status_code, detail=code) from error


@router.get("")
def _list_watchlists(
    context: Annotated[AuthContext, Depends(require_auth_context)],
) -> object:
    """List every watchlist owned by the caller, seeding the default first.

    Returns:
        The caller's watchlists, ordered for display.
    """
    require_permission(context, "watchlists:read")
    request_id = generate_id("req")
    return list(list_runtime_watchlists(context.principal_id, request_id=request_id))


@router.post("", status_code=status.HTTP_201_CREATED)
def _create_watchlist(
    body: _WatchlistCreate,
    context: Annotated[AuthContext, Depends(require_auth_context)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Idempotently create one new empty, non-default watchlist.

    Returns:
        The newly created watchlist.

    Raises:
        HTTPException: If idempotency, the account's watchlist limit, or a
            duplicate name is violated.
    """
    require_permission(context, "watchlists:write")
    if idempotency_key is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="IDEMPOTENCY_KEY_REQUIRED",
        )
    request_id = generate_id("req")
    route = "/api/v1/watchlists"
    try:
        decision = reserve_idempotency_key(
            principal_id=context.principal_id,
            method="POST",
            route=route,
            key=idempotency_key,
            request_material=body.model_dump(mode="json"),
            request_id=request_id,
        )
        if decision.state == "replay":
            existing = list_runtime_watchlists(
                context.principal_id, request_id=request_id
            )
            return next(item for item in existing if item.name == body.name)
        created = create_watchlist(
            context.principal_id, body.name, request_id=request_id
        )
        finalize_idempotency_key(
            principal_id=context.principal_id,
            method="POST",
            route=route,
            key=idempotency_key,
            response_json=canonical_json(created.model_dump(mode="json")),
            status_code=status.HTTP_201_CREATED,
            request_id=request_id,
        )
        return created
    except IdentityError as error:
        _raise_for_identity_error(error)


@router.patch("/{watchlist_id}")
def _update_watchlist(
    watchlist_id: str,
    body: _WatchlistUpdate,
    context: Annotated[AuthContext, Depends(require_auth_context)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Idempotently rename, replace items on, and/or promote one watchlist.

    Returns:
        The updated watchlist.

    Raises:
        HTTPException: If idempotency fails, the watchlist is not found or
            not owned, or the requested name is already taken.
    """
    require_permission(context, "watchlists:write")
    if idempotency_key is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="IDEMPOTENCY_KEY_REQUIRED",
        )
    request_id = generate_id("req")
    route = f"/api/v1/watchlists/{watchlist_id}"
    try:
        decision = reserve_idempotency_key(
            principal_id=context.principal_id,
            method="PATCH",
            route=route,
            key=idempotency_key,
            request_material=body.model_dump(mode="json"),
            request_id=request_id,
        )
        if decision.state == "replay":
            return get_watchlist(
                watchlist_id, context.principal_id, request_id=request_id
            )
        current = update_watchlist(
            watchlist_id,
            context.principal_id,
            name=body.name,
            symbols=body.symbols,
            is_default=body.is_default,
            request_id=request_id,
        )
        finalize_idempotency_key(
            principal_id=context.principal_id,
            method="PATCH",
            route=route,
            key=idempotency_key,
            response_json=canonical_json(current.model_dump(mode="json")),
            status_code=status.HTTP_200_OK,
            request_id=request_id,
        )
        return current
    except IdentityError as error:
        _raise_for_identity_error(error)


@router.delete("/{watchlist_id}")
def _delete_watchlist(
    watchlist_id: str,
    context: Annotated[AuthContext, Depends(require_auth_context)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Idempotently delete one non-default watchlist owned by the caller.

    Returns:
        A bounded deletion confirmation.

    Raises:
        HTTPException: If idempotency fails, the watchlist is not found or
            not owned, or it is the account's current default.
    """
    require_permission(context, "watchlists:write")
    if idempotency_key is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="IDEMPOTENCY_KEY_REQUIRED",
        )
    request_id = generate_id("req")
    route = f"/api/v1/watchlists/{watchlist_id}"
    response = {"watchlist_id": watchlist_id, "deleted": True}
    try:
        decision = reserve_idempotency_key(
            principal_id=context.principal_id,
            method="DELETE",
            route=route,
            key=idempotency_key,
            request_material={"watchlist_id": watchlist_id},
            request_id=request_id,
        )
        if decision.state == "replay":
            return response
        delete_watchlist(watchlist_id, context.principal_id, request_id=request_id)
        finalize_idempotency_key(
            principal_id=context.principal_id,
            method="DELETE",
            route=route,
            key=idempotency_key,
            response_json=canonical_json(response),
            status_code=status.HTTP_200_OK,
            request_id=request_id,
        )
        return response
    except IdentityError as error:
        _raise_for_identity_error(error)


__all__ = ("router",)
