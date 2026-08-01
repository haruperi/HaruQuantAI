"""Authenticated Strategy catalogue HTTP boundary."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.services.api.identity import require_auth_context, require_human_permission
from app.services.strategy import list_strategy_versions

type AuthContext = Any

router = APIRouter(prefix="/api/v1/strategies", tags=["strategies"])


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


__all__ = ("router",)
