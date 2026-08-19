"""Authenticated Strategy catalogue and governed mutation HTTP boundary.

Catalogue and version reads delegate straight to the Strategy public API.
Registration and parameter updates are governed writes: they require an exact
permission, a durable HTTP idempotency key, and a composed Strategy validation
policy. The gateway never chooses that policy and never evaluates a strategy —
Strategy owns registration semantics and returns immutable mutation truth.
"""

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.services.api.identity import (
    require_auth_context,
    require_human_permission,
    run_idempotent_write,
)
from app.services.api.widgets.strategies.schemas import (
    StrategyParameterUpdateRequestModel,  # noqa: TC001 - FastAPI runtime annotation.
    StrategyRegistrationRequestModel,  # noqa: TC001 - FastAPI runtime annotation.
)
from app.services.strategy import list_strategy_versions
from app.utils import generate_id

type AuthContext = Any
type _StrategySource = Callable[..., object]

router = APIRouter(prefix="/api/v1/strategies", tags=["strategies"])
_MAX_IDEMPOTENCY_KEY_LENGTH = 200


def _strategy_mutation_source() -> _StrategySource:
    """Fail closed until composition injects Strategy mutation authority.

    Raises:
        HTTPException: Always, when the source is not composed.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="STRATEGY_RUNTIME_UNAVAILABLE",
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


def _delegate(source: _StrategySource, operation: str, *args: object) -> object:
    """Delegate once and translate the unavailable sentinel into HTTP 503.

    Args:
        source: Composed Strategy mutation dispatcher.
        operation: Canonical Strategy operation name.
        *args: Operation-specific positional inputs.

    Returns:
        Strategy-owned immutable mutation result.

    Raises:
        HTTPException: If no Strategy mutation bundle is composed.
        RuntimeError: If Strategy reports an unexpected runtime failure.
    """
    try:
        return source(operation, *args)
    except RuntimeError as error:
        if str(error) != "STRATEGY_RUNTIME_UNAVAILABLE":
            raise
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


@router.get("", response_model=None)
def _list_strategy_catalogue(
    auth: Annotated[AuthContext, Depends(require_auth_context)],
) -> object:
    """Return registered Strategy versions through the owner public API.

    Args:
        auth: Authenticated human reader.

    Returns:
        Strategy-owned version catalogue response.
    """
    require_human_permission(auth, "strategy:read")
    return list_strategy_versions()


@router.get("/{strategy_id}/versions", response_model=None)
def _list_versions(
    strategy_id: str,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
) -> object:
    """Return versions for one registered Strategy.

    Args:
        strategy_id: Strategy identity filter.
        auth: Authenticated human reader.

    Returns:
        Strategy-owned version catalogue response.
    """
    require_human_permission(auth, "strategy:read")
    return list_strategy_versions(strategy_id)


@router.post("", response_model=None)
def _register_strategy_version(
    request: StrategyRegistrationRequestModel,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_StrategySource, Depends(_strategy_mutation_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Register one new Strategy version through the owner public API.

    Returns:
        Strategy-owned immutable mutation result.

    Raises:
        HTTPException: If authentication, authorization, idempotency, or
            composition fails.
    """
    require_human_permission(auth, "strategy:write")
    key = _require_idempotency(idempotency_key)
    return run_idempotent_write(
        principal_id=auth.principal_id,
        method="POST",
        route="/api/v1/strategies",
        key=key,
        request_material=request.model_dump(mode="json"),
        request_id=generate_id("req"),
        operation=lambda: _delegate(source, "register", request.payload, auth),
    )


@router.patch("/{strategy_id}/parameters", response_model=None)
def _update_strategy_parameters(
    strategy_id: str,
    request: StrategyParameterUpdateRequestModel,
    auth: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_StrategySource, Depends(_strategy_mutation_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Update approved parameters for one registered Strategy version.

    Returns:
        Strategy-owned immutable mutation result.

    Raises:
        HTTPException: If authentication, authorization, idempotency, the
            strategy identity binding, or composition fails.
    """
    require_human_permission(auth, "strategy:write")
    key = _require_idempotency(idempotency_key)
    payload = dict(request.payload)
    body_id = payload.get("strategy_id")
    if body_id is not None and body_id != strategy_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="STRATEGY_IDENTITY_MISMATCH",
        )
    return run_idempotent_write(
        principal_id=auth.principal_id,
        method="PATCH",
        route="/api/v1/strategies/{strategy_id}/parameters",
        key=key,
        request_material=request.model_dump(mode="json"),
        request_id=generate_id("req"),
        operation=lambda: _delegate(source, "update_parameters", payload, auth),
    )


__all__ = ("router",)
