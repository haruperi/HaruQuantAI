"""Authenticated symbol-discovery routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.services.api._limits import API_DEFAULT_PAGE_SIZE, API_MAX_PAGE_SIZE
from app.services.api.identity import require_auth_context, require_permission
from app.services.data import (
    build_symbol_list_request,
    list_symbols,
)
from app.utils import generate_id

type AuthContext = Any

router = APIRouter(prefix="/api/v1/data", tags=["data"])


@router.get("/symbols", response_model=None)
def _list_symbols(
    context: Annotated[AuthContext, Depends(require_auth_context)],
    source_id: str | None = None,
    query: str | None = None,
    cursor: str | None = None,
    limit: Annotated[
        int,
        Query(ge=1, le=API_MAX_PAGE_SIZE),
    ] = API_DEFAULT_PAGE_SIZE,
) -> object:
    """Delegate bounded symbol discovery to Data.

    Returns:
        Data-owned symbol page response.
    """
    require_permission(context, "data:read")
    request = build_symbol_list_request(
        source_id=source_id,
        query=query,
        cursor=cursor,
        limit=limit,
        request_id=generate_id("req"),
    )
    return list_symbols(request)


__all__ = ("router",)
