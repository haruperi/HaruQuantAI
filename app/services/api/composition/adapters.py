"""Internal bindings from named in-process providers to route dependencies."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from types import MappingProxyType
from typing import Final, cast

from app.services.api.composition.capabilities import (
    get_capability_id,
    import_capability_attribute,
)

_WIDGETS: Final[str] = "app.services.api.widgets"

# Declared provider surface: provider name to the module and attribute owning
# it. Optional-capability entries resolve to nothing when that capability is
# absent, so the composed manifest shrinks instead of failing at import.
_PROVIDER_SOURCES: Final[Mapping[str, tuple[str, str]]] = MappingProxyType(
    {
        "agentic.source": (f"{_WIDGETS}.agentic.routes", "_agentic_source"),
        "analytics.workbench.source": (
            f"{_WIDGETS}.analytics.routes",
            "_analytics_workbench_source",
        ),
        "dashboard.source": (f"{_WIDGETS}.dashboards.routes", "_dashboard_source"),
        "data.dataset_source": (f"{_WIDGETS}.data.routes", "_dataset_source"),
        "operator.audit_source": (f"{_WIDGETS}.operator.routes", "_audit_source"),
        "operator.event_source": (f"{_WIDGETS}.operator.routes", "_event_source"),
        "optimization.source": (
            f"{_WIDGETS}.optimization.routes",
            "_optimization_source",
        ),
        "portfolio.source": (f"{_WIDGETS}.portfolio.routes", "_portfolio_source"),
        "research.source": (f"{_WIDGETS}.research.routes", "_research_source"),
        "risk.command_source": (f"{_WIDGETS}.risk.routes", "_risk_command_source"),
        "risk.source": (f"{_WIDGETS}.risk.routes", "_risk_source"),
        "simulation.live_source": (
            f"{_WIDGETS}.simulation.live_routes",
            "_live_source",
        ),
        "simulation.result_source": (
            f"{_WIDGETS}.simulation.routes",
            "_simulation_result_source",
        ),
        "simulation.run_source": (
            f"{_WIDGETS}.simulation.routes",
            "_simulation_run_source",
        ),
        "simulation.session_source": (
            f"{_WIDGETS}.simulation.session_routes",
            "_simulation_session_source",
        ),
        "simulator.run_source": (
            f"{_WIDGETS}.simulator.routes",
            "_simulator_run_source",
        ),
        "simulator.strategy_source": (
            f"{_WIDGETS}.simulator.routes",
            "_simulator_strategy_source",
        ),
        "simulator.workbench_source": (
            f"{_WIDGETS}.simulator.workbench_routes",
            "_simulation_workbench_source",
        ),
        "strategy.mutation_source": (
            f"{_WIDGETS}.strategies.routes",
            "_strategy_mutation_source",
        ),
        "trading.account_profile_source": (
            f"{_WIDGETS}.trading.routes",
            "_trading_account_profile_source",
        ),
        "trading.cancel_all_preflight_source": (
            f"{_WIDGETS}.trading.routes",
            "_trading_cancel_all_preflight_source",
        ),
        "trading.cancel_order_preflight_source": (
            f"{_WIDGETS}.trading.routes",
            "_trading_cancel_order_preflight_source",
        ),
        "trading.mutation_source": (
            f"{_WIDGETS}.trading.routes",
            "_trading_mutation_source",
        ),
        "trading.preflight_source": (
            f"{_WIDGETS}.trading.routes",
            "_trading_preflight_source",
        ),
        "trading.session_source": (
            f"{_WIDGETS}.trading.routes",
            "_trading_session_source",
        ),
    }
)


def _resolve_route_dependencies() -> Mapping[str, Callable[..., object]]:
    """Resolve every declared provider that its owning capability still supplies.

    Returns:
        Immutable mapping from provider name to route dependency.
    """
    resolved: dict[str, Callable[..., object]] = {}
    for name, (module_path, attribute) in _PROVIDER_SOURCES.items():
        dependency = import_capability_attribute(
            module_path,
            attribute,
            capability_id=get_capability_id(name),
        )
        if dependency is None:
            continue
        resolved[name] = cast("Callable[..., object]", dependency)
    return MappingProxyType(resolved)


_ROUTE_DEPENDENCIES: Final[Mapping[str, Callable[..., object]]] = (
    _resolve_route_dependencies()
)


def get_route_dependency_bindings() -> Mapping[str, Callable[..., object]]:
    """Return the immutable named route-dependency bindings.

    Returns:
        Mapping from stable provider name to internal FastAPI dependency.
    """
    return _ROUTE_DEPENDENCIES


def get_absent_capability_ids() -> tuple[str, ...]:
    """Return optional capability identifiers that supplied no provider.

    Returns:
        Sorted identifiers of capabilities absent from this composition.
    """
    declared = {get_capability_id(name) for name in _PROVIDER_SOURCES}
    present = {get_capability_id(name) for name in _ROUTE_DEPENDENCIES}
    return tuple(sorted(declared - present))


__all__ = ("get_absent_capability_ids", "get_route_dependency_bindings")
