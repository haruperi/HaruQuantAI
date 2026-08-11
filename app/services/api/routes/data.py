"""Authenticated symbol discovery, market directory, dataset preparation, and import.

Symbol discovery is a bounded cursor-paginated read. The market directory
delegates once to Data's categorized directory builder (which composes symbol
listing, metadata, and snapshot reads) and is rendered by the Markets widget.
Dataset preparation is a governed write that delegates twice to Data — fetch,
then persist — and returns Data's own storage manifest. The gateway holds no
dataset, chooses no storage location, and never substitutes a provider result.
"""

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.services.api import build_api_metadata, build_api_response
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
from app.services.api.markets_source import resolve_runtime_source_id
from app.services.data import (
    build_symbol_list_request,
    list_market_directory,
    list_symbols,
)
from app.services.data.market_data.markets_directory import MarketDirectoryRequest
from app.utils import generate_id

type AuthContext = Any
type _DatasetSource = Callable[..., object]

router = APIRouter(prefix="/api/v1/data", tags=["data"])
_MAX_IDEMPOTENCY_KEY_LENGTH = 200
_DATA_CAPABILITIES = (
    ("FEAT-DATA-01", "Market Data", "symbols, snapshots, and historical retrieval"),
    ("FEAT-DATA-02", "Datasets", "preparation, import, catalog, and manifests"),
    ("FEAT-DATA-03", "Synthetic Data", "seeded synthetic evidence"),
    ("FEAT-DATA-04", "Transformation", "closed bars and deterministic resampling"),
    ("FEAT-DATA-05", "Alignment", "backward-only multi-series alignment"),
    ("FEAT-DATA-06", "Integrity", "quality inspection and anomaly evidence"),
    ("FEAT-DATA-07", "Time and Sessions", "venue and named-session evidence"),
    ("FEAT-DATA-08", "Economic Calendar", "point-in-time releases and revisions"),
    ("FEAT-DATA-09", "Sources", "source readiness, licensing, and provenance"),
    ("FEAT-DATA-10", "Market Events", "ordered streaming and feed status"),
    ("FEAT-DATA-11", "Data Jobs", "bounded update and backfill state"),
    ("FEAT-DATA-12", "Evidence", "market, account, FX, and audit evidence"),
    ("FEAT-DATA-13", "Runtime Stores", "namespaced durable runtime state"),
    ("FEAT-DATA-14", "Replay", "availability-gated replay packages"),
)


def _dataset_source() -> _DatasetSource:
    """Fail closed until canonical composition injects dataset preparation.

    Raises:
        HTTPException: Always, when the source is not composed.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="DATASET_RUNTIME_UNAVAILABLE",
    )


@router.get("/capabilities", response_model=None)
def _list_data_capabilities(
    context: Annotated[AuthContext, Depends(require_auth_context)],
) -> object:
    """Return the bounded Data feature surface available to the workstation.

    Args:
        context: Authenticated API request context.

    Returns:
        Successful API response containing fourteen capability summaries.

    Raises:
        HTTPException: If the caller lacks Data read permission.
    """
    require_permission(context, "data:read")
    request_id = generate_id("req")
    capabilities = tuple(
        {
            "feature_id": feature_id,
            "name": name,
            "summary": summary,
            "availability": "available",
        }
        for feature_id, name, summary in _DATA_CAPABILITIES
    )
    return build_api_response(
        status="success",
        message="Data capabilities retrieved",
        data={"capabilities": capabilities},
        metadata=build_api_metadata(
            request_id=request_id,
            route="/api/v1/data/capabilities",
            operation="api.data.capabilities",
            side_effect="read",
        ),
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


@router.get("/markets", response_model=None)
def _list_markets(
    context: Annotated[AuthContext, Depends(require_auth_context)],
    source_id: str | None = None,
    query: str | None = None,
    cursor: str | None = None,
    limit: Annotated[
        int,
        Query(ge=1, le=API_MAX_PAGE_SIZE),
    ] = API_DEFAULT_PAGE_SIZE,
) -> object:
    """Delegate the categorized market-directory read to Data.

    The ``source_id`` is resolved to the configured runtime broker by the
    composition layer when the caller omits it; this handler performs no
    business logic and delegates exactly once to Data's directory builder,
    then normalizes the Data standard response into the gateway envelope.

    Returns:
        Gateway-envelope categorized market-directory response.
    """
    require_permission(context, "data:read")
    request_id = generate_id("req")
    resolved_source_id = resolve_runtime_source_id(source_id, request_id=request_id)
    request = MarketDirectoryRequest(
        source_id=resolved_source_id,
        query=query,
        cursor=cursor,
        limit=limit,
        request_id=request_id,
    )
    directory_response = list_market_directory(request)
    response_status = str(getattr(directory_response, "status", "success"))
    data_payload = getattr(directory_response, "data", None)
    # Data errors carry domain-specific codes (e.g. UNSUPPORTED_SOURCE) outside
    # the gateway's ApiErrorCode family; map them to UPSTREAM_UNAVAILABLE so
    # the response validates against the gateway contract. The original code
    # and details are preserved in the error ``details`` for diagnostics.
    data_error = getattr(directory_response, "error", None)
    gateway_error = None
    if response_status != "success" and data_error is not None:
        original_code = str(getattr(data_error, "code", "UNKNOWN_ERROR"))
        gateway_error = {
            "code": "UPSTREAM_UNAVAILABLE",
            "message": str(
                getattr(data_error, "message", "Market directory unavailable")
            ),
            "details": {"upstream_code": original_code},
            "retryable": bool(getattr(data_error, "retryable", False)),
            "request_id": request_id,
            "trace_id": None,
        }
    return build_api_response(
        status=response_status,
        message=(
            "Market directory retrieved"
            if response_status == "success"
            else "Market directory unavailable"
        ),
        data=data_payload,
        error=gateway_error,
        metadata=build_api_metadata(
            request_id=request_id,
            route="/api/v1/data/markets",
            operation="api.data.markets",
            side_effect="read",
        ),
    )


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
