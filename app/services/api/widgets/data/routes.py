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
    InstrumentUpdateRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
    SeriesUpdateRequest,  # noqa: TC001 - FastAPI resolves runtime annotations.
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
    get_instrument_spec,
    list_brokers,
    list_instruments,
    list_market_series,
    list_symbols,
    update_instrument_spec,
    update_market_series,
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


@router.get("/series", response_model=None)
def _list_market_series(
    context: Annotated[AuthContext, Depends(require_auth_context)],
    limit: Annotated[
        int,
        Query(ge=1, le=API_MAX_PAGE_SIZE),
    ] = API_DEFAULT_PAGE_SIZE,
) -> object:
    """Return the bounded market-data series reference surface.

    Args:
        context: Authenticated API request context.
        limit: Bounded maximum series rows.

    Returns:
        Successful API response containing series summaries.

    Raises:
        HTTPException: If the caller lacks Data read permission.
    """
    require_permission(context, "data:read")
    request_id = generate_id("req")
    return build_api_response(
        status="success",
        message="Market series retrieved",
        data={"series": list_market_series(request_id=request_id, limit=limit)},
        metadata=build_api_metadata(
            request_id=request_id,
            route="/api/v1/data/series",
            operation="api.data.series",
            side_effect="read",
        ),
    )


@router.get("/instruments", response_model=None)
def _list_instruments(
    context: Annotated[AuthContext, Depends(require_auth_context)],
    limit: Annotated[
        int,
        Query(ge=1, le=API_MAX_PAGE_SIZE),
    ] = API_DEFAULT_PAGE_SIZE,
) -> object:
    """Return the bounded instrument specification surface.

    Args:
        context: Authenticated API request context.
        limit: Bounded maximum instrument rows.

    Returns:
        Successful API response containing instrument summaries.

    Raises:
        HTTPException: If the caller lacks Data read permission.
    """
    require_permission(context, "data:read")
    request_id = generate_id("req")
    return build_api_response(
        status="success",
        message="Instruments retrieved",
        data={"instruments": list_instruments(request_id=request_id, limit=limit)},
        metadata=build_api_metadata(
            request_id=request_id,
            route="/api/v1/data/instruments",
            operation="api.data.instruments",
            side_effect="read",
        ),
    )


@router.get("/brokers", response_model=None)
def _list_brokers(
    context: Annotated[AuthContext, Depends(require_auth_context)],
    limit: Annotated[
        int,
        Query(ge=1, le=API_MAX_PAGE_SIZE),
    ] = API_DEFAULT_PAGE_SIZE,
) -> object:
    """Return the bounded broker profile surface.

    Args:
        context: Authenticated API request context.
        limit: Bounded maximum broker rows.

    Returns:
        Successful API response containing broker summaries.

    Raises:
        HTTPException: If the caller lacks Data read permission.
    """
    require_permission(context, "data:read")
    request_id = generate_id("req")
    return build_api_response(
        status="success",
        message="Brokers retrieved",
        data={"brokers": list_brokers(request_id=request_id, limit=limit)},
        metadata=build_api_metadata(
            request_id=request_id,
            route="/api/v1/data/brokers",
            operation="api.data.brokers",
            side_effect="read",
        ),
    )


@router.get("/instruments/{instrument}", response_model=None)
def _get_instrument(
    instrument: str,
    context: Annotated[AuthContext, Depends(require_auth_context)],
) -> object:
    """Return one full instrument specification by identity.

    Args:
        instrument: Instrument identity (the Data ``symbol_id``).
        context: Authenticated API request context.

    Returns:
        Successful API response containing the instrument specification.

    Raises:
        HTTPException: If the caller lacks Data read permission or the
            instrument is unknown.
    """
    require_permission(context, "data:read")
    request_id = generate_id("req")
    return build_api_response(
        status="success",
        message="Instrument retrieved",
        data=get_instrument_spec(instrument.strip(), request_id=request_id),
        metadata=build_api_metadata(
            request_id=request_id,
            route="/api/v1/data/instruments/{instrument}",
            operation="api.data.instrument",
            side_effect="read",
        ),
    )


@router.patch("/series/{series_id}", response_model=None)
def _update_series(
    series_id: int,
    request: SeriesUpdateRequest,
    context: Annotated[AuthContext, Depends(require_auth_context)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Update one series row and its linked instrument specification.

    Args:
        series_id: Series identity to update.
        request: Governed edit payload carrying series and instrument fields.
        context: Authenticated API request context.
        idempotency_key: Required durable HTTP idempotency key.

    Returns:
        Successful API response containing the updated series summary.

    Raises:
        HTTPException: If authentication, authorization, idempotency, or the
            owner validation fails.
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
    request_id = generate_id("req")
    body = request.model_dump(mode="json")
    try:
        series = update_market_series(
            series_id,
            symbol=body["symbol"],
            instrument=body["instrument"],
            broker_id=body["broker_id"],
            timeframe=body["timeframe"],
            timezone=body["timezone"],
            date_from=body["date_from"],
            date_to=body["date_to"],
            data_type=body["data_type"],
            decimals=body["decimals"],
            source=body["source"],
            row_count=body["row_count"],
            remove_weekends=body["remove_weekends"],
            show=body["show"],
            instrument_description=body["description"],
            point_value=body["point_value"],
            tick_size=body["tick_size"],
            tick_step=body["tick_step"],
            default_spread=body["default_spread"],
            default_slippage=body["default_slippage"],
            min_distance=body["min_distance"],
            order_size_multiplier=body["order_size_multiplier"],
            order_size_step=body["order_size_step"],
            request_id=request_id,
        )
    except Exception as error:
        # Data signals typed owner failures through the error code attribute;
        # anything without one is an unexpected failure and re-raises.
        code = str(getattr(error, "code", "") or "")
        if code in {"SERIES_NOT_FOUND", "INSTRUMENT_NOT_FOUND"}:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=code
            ) from error
        if code:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=code
            ) from error
        raise
    return build_api_response(
        status="success",
        message="Market series updated",
        data=series,
        metadata=build_api_metadata(
            request_id=request_id,
            route="/api/v1/data/series/{series_id}",
            operation="api.data.series_update",
            side_effect="write",
        ),
    )


@router.patch("/instruments/{instrument}", response_model=None)
def _update_instrument(
    instrument: str,
    request: InstrumentUpdateRequest,
    context: Annotated[AuthContext, Depends(require_auth_context)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> object:
    """Update exactly one instrument specification.

    Args:
        instrument: Instrument identity (the Data ``symbol_id``).
        request: Governed edit payload carrying the instrument fields.
        context: Authenticated API request context.
        idempotency_key: Required durable HTTP idempotency key.

    Returns:
        Successful API response containing the updated specification.

    Raises:
        HTTPException: If authentication, authorization, idempotency, or the
            owner validation fails.
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
    request_id = generate_id("req")
    body = request.model_dump(mode="json")
    try:
        spec = update_instrument_spec(
            instrument.strip(),
            description=body["description"],
            point_value=body["point_value"],
            tick_size=body["tick_size"],
            tick_step=body["tick_step"],
            default_spread=body["default_spread"],
            default_slippage=body["default_slippage"],
            min_distance=body["min_distance"],
            order_size_multiplier=body["order_size_multiplier"],
            order_size_step=body["order_size_step"],
            request_id=request_id,
        )
    except Exception as error:
        # Data signals typed owner failures through the error code attribute;
        # anything without one is an unexpected failure and re-raises.
        code = str(getattr(error, "code", "") or "")
        if code == "INSTRUMENT_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=code
            ) from error
        if code:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=code
            ) from error
        raise
    return build_api_response(
        status="success",
        message="Instrument updated",
        data=spec,
        metadata=build_api_metadata(
            request_id=request_id,
            route="/api/v1/data/instruments/{instrument}",
            operation="api.data.instrument_update",
            side_effect="write",
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
