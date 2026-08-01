"""Public liveness and protected readiness HTTP routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.services.api.health import get_liveness, get_readiness
from app.services.api.identity import require_auth_context

type AuthContext = Any

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("/liveness", response_model=None)
def _liveness() -> object:
    """Return coarse public process liveness.

    Returns:
        Canonical liveness response.
    """
    return get_liveness()


@router.get("/readiness", response_model=None)
def _readiness(
    context: Annotated[AuthContext, Depends(require_auth_context)],
) -> object:
    """Return protected dependency readiness.

    Args:
        context: Authenticated operator context.

    Returns:
        Canonical readiness response.
    """
    return get_readiness(context)


__all__ = ("router",)
