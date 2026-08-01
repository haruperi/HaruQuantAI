"""Read-only timestamped dashboard snapshot routes."""

from collections.abc import Callable
from typing import Annotated, Any, Literal, NoReturn

from fastapi import APIRouter, Depends, HTTPException, status

from app.services.api.identity import require_auth_context, require_permission

type AuthContext = Any
type DashboardName = Literal[
    "broker", "equity_curve", "summary", "resources", "market_hours", "calendar"
]
type DashboardSource = Callable[[DashboardName, AuthContext], object]

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboards"])


def _dashboard_source() -> NoReturn:
    """Fail closed until composition injects public owner snapshot functions.

    Raises:
        HTTPException: Always when snapshot dependencies are unavailable.
    """
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="DASHBOARD_DEPENDENCY_UNAVAILABLE",
    )


def _snapshot(
    name: DashboardName, context: AuthContext, source: DashboardSource
) -> object:
    """Read one owner-authored timestamped snapshot.

    Returns:
        Owner-authored snapshot with freshness evidence.
    """
    require_permission(context, "dashboard:read")
    return source(name, context)


@router.get("/broker", response_model=None)
def _broker(
    context: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[DashboardSource, Depends(_dashboard_source)],
) -> object:
    """Return broker snapshot evidence.

    Returns:
        Owner-authored broker snapshot.
    """
    return _snapshot("broker", context, source)


@router.get("/equity-curve", response_model=None)
def _equity_curve(
    context: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[DashboardSource, Depends(_dashboard_source)],
) -> object:
    """Return equity-curve snapshot evidence.

    Returns:
        Analytics-authored snapshot.
    """
    return _snapshot("equity_curve", context, source)


@router.get("/summary", response_model=None)
def _summary(
    context: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[DashboardSource, Depends(_dashboard_source)],
) -> object:
    """Return bounded dashboard summary evidence.

    Returns:
        Owner-authored summary snapshot.
    """
    return _snapshot("summary", context, source)


@router.get("/system/resources", response_model=None)
def _resources(
    context: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[DashboardSource, Depends(_dashboard_source)],
) -> object:
    """Return system resource snapshot evidence.

    Returns:
        Owner-authored resource snapshot.
    """
    return _snapshot("resources", context, source)


@router.get("/market-hours", response_model=None)
def _market_hours(
    context: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[DashboardSource, Depends(_dashboard_source)],
) -> object:
    """Return market-hours snapshot evidence.

    Returns:
        Data-authored market-hours snapshot.
    """
    return _snapshot("market_hours", context, source)


@router.get("/forex-calendar", response_model=None)
def _calendar(
    context: Annotated[AuthContext, Depends(require_auth_context)],
    source: Annotated[DashboardSource, Depends(_dashboard_source)],
) -> object:
    """Return economic-calendar snapshot evidence.

    Returns:
        Data-authored calendar snapshot.
    """
    return _snapshot("calendar", context, source)


__all__ = ("router",)
