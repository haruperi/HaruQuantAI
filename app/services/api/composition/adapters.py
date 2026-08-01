"""Internal bindings from named in-process providers to route dependencies."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from types import MappingProxyType

from app.services.api.routes.dashboards import _dashboard_source
from app.services.api.routes.operator import _audit_source, _event_source

_ROUTE_DEPENDENCIES: Mapping[str, Callable[..., object]] = MappingProxyType(
    {
        "dashboard.source": _dashboard_source,
        "operator.audit_source": _audit_source,
        "operator.event_source": _event_source,
    }
)


def get_route_dependency_bindings() -> Mapping[str, Callable[..., object]]:
    """Return the immutable named route-dependency bindings.

    Returns:
        Mapping from stable provider name to internal FastAPI dependency.
    """
    return _ROUTE_DEPENDENCIES


__all__ = ("get_route_dependency_bindings",)
