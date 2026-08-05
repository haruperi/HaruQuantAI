"""Authenticated symbol discovery, dataset preparation, and external import.

Symbol discovery is a bounded cursor-paginated read. Dataset preparation is a
governed write that delegates twice to Data — fetch, then persist — and returns
Data's own storage manifest. The gateway holds no dataset, chooses no storage
location, and never substitutes a provider result.
"""

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.services.api._limits import API_DEFAULT_PAGE_SIZE, API_MAX_PAGE_SIZE
from app.services.api.contracts import (
    DatasetImportRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
    DatasetPrepareRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
)
from app.services.api.identity import (
    require_auth_context,
    require_human_permission,
    require_permission,
    run_idempotent_write,
)
from app.services.data import (
    build_symbol_list_request,
    list_symbols,
)
from app.utils import generate_id

type AuthContext = Any
type _DatasetSource = Callable[..., object]

router = APIRouter(prefix="/api/v1/data", tags=["data"])
_MAX_IDEMPOTENCY_KEY_LENGTH = 200


def _dataset_source() -> _DatasetSource:
    """Fail closed until canonical composition injects dataset preparation.

    Raises:
        HTTPException: Always, when the source is not composed.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="DATASET_RUNTIME_UNAVAILABLE",
    )


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


@router.post("/datasets/prepare", response_model=None)
def _prepare_dataset(
    request: DatasetPrepareRequest,
    context: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_DatasetSource, Depends(_dataset_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Fetch and persist one requested market dataset through Data.

    Returns:
        Data-owned storage manifest response.

    Raises:
        HTTPException: If authentication, authorization, idempotency, or the
            dataset availability check fails.
        RuntimeError: If Data reports an unexpected runtime failure.
    """
    require_human_permission(context, "data:write")
    if (
        idempotency_key is None
        or not idempotency_key.strip()
        or len(idempotency_key) > _MAX_IDEMPOTENCY_KEY_LENGTH
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="IDEMPOTENCY_KEY_REQUIRED",
        )
    try:
        return run_idempotent_write(
            principal_id=context.principal_id,
            method="POST",
            route="/api/v1/data/datasets/prepare",
            key=idempotency_key,
            request_material=request.model_dump(mode="json"),
            request_id=generate_id("req"),
            operation=lambda: source(
                "prepare", request.market_request, request.save_request
            ),
        )
    except RuntimeError as error:
        if str(error) not in {"DATASET_RUNTIME_UNAVAILABLE", "DATASET_UNAVAILABLE"}:
            raise
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


@router.get("/imports/dialects", response_model=None)
def _import_dialects(
    context: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_DatasetSource, Depends(_dataset_source)],
) -> object:
    """Return the import dialects Data itself supports.

    The gateway keeps no dialect list of its own, so a caller always chooses
    from owner truth rather than from a gateway copy that could drift.

    Returns:
        Data-owned supported-dialect mapping.

    Raises:
        HTTPException: If authorization or composition fails.
        RuntimeError: If data runtime fails with an unhandled runtime error.
    """
    require_permission(context, "data:read")
    try:
        return source("dialects")
    except RuntimeError as error:
        if str(error) != "DATASET_RUNTIME_UNAVAILABLE":
            raise
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


@router.post("/imports", response_model=None)
def _import_dataset(
    request: DatasetImportRequest,
    context: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_DatasetSource, Depends(_dataset_source)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Import one external dataset through Data.

    Returns:
        Data-owned storage manifest response.

    Raises:
        HTTPException: If authentication, authorization, idempotency, or
            composition fails.
        RuntimeError: If Data reports an unexpected runtime failure.
    """
    require_human_permission(context, "data:write")
    if (
        idempotency_key is None
        or not idempotency_key.strip()
        or len(idempotency_key) > _MAX_IDEMPOTENCY_KEY_LENGTH
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="IDEMPOTENCY_KEY_REQUIRED",
        )
    try:
        return run_idempotent_write(
            principal_id=context.principal_id,
            method="POST",
            route="/api/v1/data/imports",
            key=idempotency_key,
            request_material=request.model_dump(mode="json"),
            request_id=generate_id("req"),
            operation=lambda: source("import", request.payload),
        )
    except RuntimeError as error:
        if str(error) != "DATASET_RUNTIME_UNAVAILABLE":
            raise
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error


__all__ = ("router",)
