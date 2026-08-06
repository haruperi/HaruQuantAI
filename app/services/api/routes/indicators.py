"""Authenticated read-only Indicators catalogue and spec routes."""

from collections.abc import Mapping
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from app.services.api.identity import (
    require_auth_context,
    require_permission,
)
from app.services.indicators import (
    get_capability_matrix,
    get_indicator,
    list_indicators,
)

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


def _format_response(response: object) -> object:
    """Ensure StandardResponse data field contains only JSON-serializable types.

    Args:
        response: Response envelope to format.

    Returns:
        Formatted response envelope with JSON-serializable data payload.
    """
    if hasattr(response, "data") and response.data is not None:
        data = response.data
        if hasattr(response, "model_copy"):
            return response.model_copy(update={"data": _to_jsonable(data)})
    return response


@router.get("", response_model=None)
def _list_indicator_catalogue(
    context: Annotated[AuthContext, Depends(require_auth_context)],
) -> object:
    """Return the registered Indicators catalogue."""
    require_permission(context, "indicators:read")
    return _format_response(list_indicators())


@router.get("/capabilities", response_model=None)
def _get_indicator_capabilities(
    context: Annotated[AuthContext, Depends(require_auth_context)],
) -> object:
    """Return the Indicators capability matrix."""
    require_permission(context, "indicators:read")
    return _format_response(get_capability_matrix())


@router.get("/{indicator_id}", response_model=None)
def _get_indicator_spec(
    indicator_id: str,
    context: Annotated[AuthContext, Depends(require_auth_context)],
) -> object:
    """Return one registered indicator specification."""
    require_permission(context, "indicators:read")
    return _format_response(get_indicator(indicator_id))


__all__ = ("router",)
