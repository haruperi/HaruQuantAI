"""Authenticated symbol discovery, bar history, dataset preparation, and import.

Symbol discovery is a bounded cursor-paginated read. Bar history is a bounded
read of Data-owned OHLCV records for one symbol and timeframe, and is what the
Chart widget renders. Dataset preparation is a governed write that delegates
twice to Data — fetch, then persist — and returns Data's own storage manifest.
The gateway holds no dataset, chooses no storage location, and never
substitutes a provider result.
"""

from collections.abc import Callable, Iterable, Mapping
from datetime import datetime
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.services.api import build_api_metadata, build_api_response
from app.services.api.identity import (
    require_auth_context,
    require_human_permission,
    require_permission,
    run_idempotent_write,
)
from app.services.api.widgets.data import orchestration
from app.services.api.widgets.data.schemas import (
    BarTimeframe,  # noqa: TC001 - FastAPI resolves runtime annotations.
    DatasetImportRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
    DatasetPrepareRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
)
from app.services.api.widgets.markets import resolve_runtime_source_id
from app.services.api.widgets.settings.limits import (
    API_DEFAULT_BAR_COUNT,
    API_DEFAULT_PAGE_SIZE,
    API_MAX_BAR_COUNT,
    API_MAX_PAGE_SIZE,
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


def _build_symbol_directory_response(response: object, *, request_id: str) -> object:
    """Normalize one Data symbol result into the canonical API envelope.

    Args:
        response: Data-owned standard response from symbol discovery.
        request_id: Canonical API request identifier.

    Returns:
        Canonical API response carrying the Data-owned symbol page directly.
    """
    response_status = str(getattr(response, "status", "error"))
    data_payload = getattr(response, "data", None)
    upstream_error = getattr(response, "error", None)
    gateway_error = None
    if response_status != "success":
        gateway_error = {
            "code": "UPSTREAM_UNAVAILABLE",
            "message": str(
                getattr(upstream_error, "message", "Symbol directory unavailable")
            ),
            "details": {
                "upstream_code": str(getattr(upstream_error, "code", "UNKNOWN_ERROR"))
            },
            "retryable": bool(getattr(upstream_error, "retryable", False)),
            "request_id": request_id,
            "trace_id": None,
        }
    if isinstance(data_payload, Mapping):
        items = data_payload.get("items", ())
        next_cursor = data_payload.get("next_cursor")
    else:
        items = getattr(data_payload, "items", ()) if data_payload is not None else ()
        next_cursor = (
            getattr(data_payload, "next_cursor", None)
            if data_payload is not None
            else None
        )
    return build_api_response(
        status=response_status,
        message=(
            "Symbol directory retrieved"
            if response_status == "success"
            else "Symbol directory unavailable"
        ),
        data=data_payload,
        error=gateway_error,
        metadata=build_api_metadata(
            request_id=request_id,
            route="/api/v1/data/symbols",
            operation="api.data.symbols",
            side_effect="read",
            next_cursor=next_cursor,
            page_size=len(items),
        ),
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
    request_id = generate_id("req")
    # Data requires an explicit source. An omitted source_id must resolve to the
    # configured runtime broker here: reaching the request model as None fails
    # outside Data's error boundary, which surfaces as a 500 rather than a
    # typed error.
    request = build_symbol_list_request(
        source_id=resolve_runtime_source_id(source_id, request_id=request_id),
        query=query,
        cursor=cursor,
        limit=limit,
        request_id=request_id,
    )
    return _build_symbol_directory_response(
        list_symbols(request),
        request_id=request_id,
    )


@router.get("/bars", response_model=None)
def _get_bars(
    context: Annotated[AuthContext, Depends(require_auth_context)],
    symbol: Annotated[str, Query(min_length=1, max_length=128)],
    timeframe: BarTimeframe = "H1",
    limit: Annotated[
        int,
        Query(ge=1, le=API_MAX_BAR_COUNT),
    ] = API_DEFAULT_BAR_COUNT,
    source_id: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> object:
    """Delegate one bounded bar-history read to Data.

    Args:
        context: Authenticated API request context.
        symbol: Broker-native symbol to chart.
        timeframe: Canonical timeframe key from Data's manifest.
        limit: Bounded number of most-recent bars.
        source_id: Optional explicit Data provider.
        start: Optional inclusive window start.
        end: Optional inclusive window end.

    Returns:
        Gateway bar-series response.

    Raises:
        HTTPException: If the caller lacks Data read permission, or if the
            requested window is inverted.
    """
    require_permission(context, "data:read")
    if start is not None and end is not None and end <= start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="BAR_WINDOW_INVALID",
        )
    request_id = generate_id("req")
    return orchestration.orchestrate_bars(
        symbol=symbol.strip(),
        timeframe=timeframe,
        limit=limit,
        source_id=source_id,
        start=start,
        end=end,
        request_id=request_id,
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


@router.get("/datasets", response_model=None)
def _list_datasets(
    context: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[_DatasetSource, Depends(_dataset_source)],
) -> object:
    """Return bounded verified datasets available to SIM sessions.

    Returns:
        Data-owned verified dataset summaries.
    """
    require_permission(context, "data:read")
    return list(cast("Iterable[object]", source("list", generate_id("req"))))


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
