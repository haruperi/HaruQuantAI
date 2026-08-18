"""Internal bindings from named in-process providers to route dependencies."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from types import MappingProxyType

from app.services.api.workstation.agentic.routes import _agentic_source
from app.services.api.workstation.analytics_workbench.routes import (
    _analytics_workbench_source,
)
from app.services.api.workstation.dashboards.routes import _dashboard_source
from app.services.api.workstation.data.routes import _dataset_source
from app.services.api.workstation.operator.routes import _audit_source, _event_source
from app.services.api.workstation.optimization.routes import _optimization_source
from app.services.api.workstation.portfolio.routes import _portfolio_source
from app.services.api.workstation.research.routes import _research_source
from app.services.api.workstation.risk.routes import _risk_command_source, _risk_source
from app.services.api.workstation.simulation.live_routes import _live_source
from app.services.api.workstation.simulation.routes import (
    _simulation_result_source,
    _simulation_run_source,
)
from app.services.api.workstation.simulation.session_routes import (
    _simulation_session_source,
)
from app.services.api.workstation.simulation_workbench.routes import (
    _simulation_workbench_source,
)
from app.services.api.workstation.simulator.routes import (
    _simulator_run_source,
    _simulator_strategy_source,
)
from app.services.api.workstation.strategies.routes import _strategy_mutation_source
from app.services.api.workstation.trading.routes import (
    _trading_account_profile_source,
    _trading_cancel_all_preflight_source,
    _trading_cancel_order_preflight_source,
    _trading_mutation_source,
    _trading_preflight_source,
    _trading_session_source,
)

_ROUTE_DEPENDENCIES: Mapping[str, Callable[..., object]] = MappingProxyType(
    {
        "agentic.source": _agentic_source,
        "analytics.workbench.source": _analytics_workbench_source,
        "dashboard.source": _dashboard_source,
        "data.dataset_source": _dataset_source,
        "operator.audit_source": _audit_source,
        "operator.event_source": _event_source,
        "optimization.source": _optimization_source,
        "portfolio.source": _portfolio_source,
        "research.source": _research_source,
        "risk.command_source": _risk_command_source,
        "risk.source": _risk_source,
        "simulation.live_source": _live_source,
        "simulation.result_source": _simulation_result_source,
        "simulation.run_source": _simulation_run_source,
        "simulation.session_source": _simulation_session_source,
        "simulator.run_source": _simulator_run_source,
        "simulator.strategy_source": _simulator_strategy_source,
        "simulator.workbench_source": _simulation_workbench_source,
        "strategy.mutation_source": _strategy_mutation_source,
        "trading.account_profile_source": _trading_account_profile_source,
        "trading.cancel_all_preflight_source": _trading_cancel_all_preflight_source,
        "trading.cancel_order_preflight_source": _trading_cancel_order_preflight_source,
        "trading.mutation_source": _trading_mutation_source,
        "trading.preflight_source": _trading_preflight_source,
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
