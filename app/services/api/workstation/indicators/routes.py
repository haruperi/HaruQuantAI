"""Authenticated read-only Indicators catalogue and spec routes."""

from collections.abc import Mapping
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.services.api import build_api_metadata, build_api_response
from app.services.api.identity import (
    require_auth_context,
    require_permission,
)
from app.services.api.workstation.data.schemas import BarTimeframe  # noqa: TC001
from app.services.api.workstation.indicators.orchestration import (
    orchestrate_indicator_series,
)
from app.services.api.workstation.indicators.schemas import (
    ChartIndicatorId,  # noqa: TC001
    IndicatorSource,  # noqa: TC001
)
from app.services.api.workstation.settings.limits import API_MAX_BAR_COUNT
from app.services.indicators import (
    get_capability_matrix,
    get_indicator,
    list_indicators,
)
from app.utils import generate_id

type AuthContext = Any

router = APIRouter(prefix="/api/v1/indicators", tags=["indicators"])


def _to_jsonable(obj: object) -> object:
    """Recursively convert mappingproxies and dataclasses to JSON-serializable types.

    Args:
        obj: Target object to serialize.

    Returns:
        JSON-serializable representation of obj.
    """
    if isinstance(obj, Mapping):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, tuple | list):
        return [_to_jsonable(v) for v in obj]
    if hasattr(obj, "__dataclass_fields__"):
        return {
            field_name: _to_jsonable(getattr(obj, field_name))
            for field_name in obj.__dataclass_fields__
        }
    return obj


def _format_response(
    response: object,
    *,
    route: str,
    operation: str,
) -> object:
    """Project an Indicators owner response into the canonical API envelope.

    Args:
        response: Response envelope to format.
        route: Canonical HTTP route template.
        operation: Registered API operation identifier.

    Returns:
        Canonical API response with a JSON-serializable owner payload.
    """
    owner_status = str(getattr(response, "status", "error"))
    owner_data = getattr(response, "data", None)
    owner_error = getattr(response, "error", None)
    request_id = generate_id("req")
    succeeded = owner_status == "success" and owner_data is not None
    return build_api_response(
        status="success" if succeeded else "error",
        message=(
            str(getattr(response, "message", "Indicators request completed"))
            if succeeded
            else "Indicator unavailable"
        ),
        data=_to_jsonable(owner_data) if succeeded else None,
        error=(
            None
            if succeeded
            else {
                "code": "NOT_FOUND",
                "message": str(
                    getattr(owner_error, "message", "Indicator unavailable")
                ),
                "details": {},
                "retryable": False,
                "request_id": request_id,
                "trace_id": None,
            }
        ),
        metadata=build_api_metadata(
            request_id=request_id,
            route=route,
            operation=operation,
            side_effect="read",
        ),
    )


@router.get("", response_model=None)
def _list_indicator_catalogue(
    context: Annotated[AuthContext, Depends(require_auth_context)],
) -> object:
    """Return the registered Indicators catalogue."""
    require_permission(context, "indicators:read")
    return _format_response(
        list_indicators(),
        route="/api/v1/indicators",
        operation="api.indicators.list",
    )


@router.get("/capabilities", response_model=None)
def _get_indicator_capabilities(
    context: Annotated[AuthContext, Depends(require_auth_context)],
) -> object:
    """Return the Indicators capability matrix."""
    require_permission(context, "indicators:read")
    return _format_response(
        get_capability_matrix(),
        route="/api/v1/indicators/capabilities",
        operation="api.indicators.capabilities",
    )


@router.get("/{indicator_id}/series", response_model=None)
def _get_indicator_series(
    indicator_id: ChartIndicatorId,
    context: Annotated[AuthContext, Depends(require_auth_context)],
    symbol: Annotated[str, Query(min_length=1, max_length=128)],
    timeframe: BarTimeframe = "H1",
    period: Annotated[int, Query(ge=2, le=10_000)] = 14,
    source: IndicatorSource = "close",
    limit: Annotated[int, Query(ge=2, le=API_MAX_BAR_COUNT)] = 500,
    start: datetime | None = None,
    end: datetime | None = None,
    source_id: str | None = None,
) -> object:
    """Return one Indicators-owned chart series over uncached Data bars."""
    require_permission(context, "indicators:read")
    return orchestrate_indicator_series(
        indicator_id=indicator_id,
        symbol=symbol,
        timeframe=timeframe,
        period=period,
        source=source,
        limit=limit,
        start=start,
        end=end,
        source_id=source_id,
        request_id=generate_id("req"),
    )


@router.get("/{indicator_id}", response_model=None)
def _get_indicator_spec(
    indicator_id: str,
    context: Annotated[AuthContext, Depends(require_auth_context)],
) -> object:
    """Return one registered indicator specification."""
    require_permission(context, "indicators:read")
    return _format_response(
        get_indicator(indicator_id),
        route="/api/v1/indicators/{indicator_id}",
        operation="api.indicators.get_spec",
    )


__all__ = ("router",)
