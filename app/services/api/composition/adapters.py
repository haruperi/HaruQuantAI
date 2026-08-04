"""Internal bindings from named in-process providers to route dependencies."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from types import MappingProxyType

from app.services.api.routes.agentic import _agentic_source
from app.services.api.routes.dashboards import _dashboard_source
from app.services.api.routes.operator import _audit_source, _event_source
from app.services.api.routes.optimization import _optimization_source
from app.services.api.routes.portfolio import _portfolio_source
from app.services.api.routes.risk import _risk_source
from app.services.api.routes.simulation import (
    _simulation_result_source,
    _simulation_run_source,
)
from app.services.api.routes.simulation_sessions import _simulation_session_source
from app.services.api.routes.trading import (
    _trading_mutation_source,
    _trading_session_source,
)

_ROUTE_DEPENDENCIES: Mapping[str, Callable[..., object]] = MappingProxyType(
    {
        "agentic.source": _agentic_source,
        "dashboard.source": _dashboard_source,
        "operator.audit_source": _audit_source,
        "operator.event_source": _event_source,
        "optimization.source": _optimization_source,
        "portfolio.source": _portfolio_source,
        "risk.source": _risk_source,
        "simulation.result_source": _simulation_result_source,
        "simulation.run_source": _simulation_run_source,
        "simulation.session_source": _simulation_session_source,
        "trading.mutation_source": _trading_mutation_source,
        "trading.session_source": _trading_session_source,
    }
)


def get_route_dependency_bindings() -> Mapping[str, Callable[..., object]]:
    """Return the immutable named route-dependency bindings.

    Returns:
        Mapping from stable provider name to internal FastAPI dependency.
    """
    return _ROUTE_DEPENDENCIES


__all__ = ("get_route_dependency_bindings",)
