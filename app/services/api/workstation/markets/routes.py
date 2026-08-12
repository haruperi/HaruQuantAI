"""Thin HTTP routes for markets directory and quote orchestration."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.services.api.identity import require_auth_context, require_permission
from app.services.api.workstation.markets import orchestration
from app.services.api.workstation.settings.limits import (
    API_DEFAULT_PAGE_SIZE,
    API_MAX_PAGE_SIZE,
)
from app.utils import generate_id

type AuthContext = Any

router = APIRouter(prefix="/api/v1/data", tags=["data"])


@router.get("/markets", response_model=None)
def _list_markets(
    context: Annotated[AuthContext, Depends(require_auth_context)],
    source_id: str | None = None,
    query: str | None = None,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=API_MAX_PAGE_SIZE)] = API_DEFAULT_PAGE_SIZE,
) -> object:
    """Delegate the categorized market-directory read to Data.

    Args:
        context: Authenticated request context.
        source_id: Optional explicit Data provider.
        query: Optional symbol search.
        cursor: Optional pagination cursor.
        limit: Bounded page size.

    Returns:
        Gateway market-directory response.
    """
    require_permission(context, "data:read")
    request_id = generate_id("req")
    return orchestration.orchestrate_market_directory(
        source_id=source_id,
        query=query,
        cursor=cursor,
        limit=limit,
        request_id=request_id,
    )


@router.get("/quotes", response_model=None)
def _get_quotes(
    context: Annotated[AuthContext, Depends(require_auth_context)],
    symbols: str,
    source_id: str | None = None,
    include_technicals: bool = False,
) -> object:
    """Delegate an explicit-symbol quote read to Data.

    Args:
        context: Authenticated request context.
        symbols: Comma-separated broker-native symbols.
        source_id: Optional explicit Data provider.
        include_technicals: Whether to add Indicators-owned projections.

    Returns:
        Gateway quote response.

    Raises:
        HTTPException: If no symbols are supplied.
    """
    require_permission(context, "data:read")
    parsed_symbols = tuple(item.strip() for item in symbols.split(",") if item.strip())
    if not parsed_symbols:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="SYMBOLS_REQUIRED",
        )
    request_id = generate_id("req")
    return orchestration.orchestrate_quotes(
        symbols=parsed_symbols,
        source_id=source_id,
        include_technicals=include_technicals,
        request_id=request_id,
    )


__all__ = ("router",)
