"""Validated in-process owner dependency graph."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from app.services.api.composition.adapters import get_route_dependency_bindings


@dataclass(frozen=True, slots=True)
class _InProcessGraph:
    """Internal immutable graph of route providers and owned shutdown hooks."""

    overrides: Mapping[Callable[..., object], Callable[[], object]]
    probes: Mapping[str, Callable[[], object]]
    owned_resource_closers: tuple[Callable[[], object], ...]


def _constant_provider(value: object) -> Callable[[], object]:
    """Bind one already-composed owner dependency for FastAPI injection.

    Returns:
        Zero-argument dependency provider.
    """

    def _provide() -> object:
        """Return the exact composed owner dependency."""
        return value

    return _provide


def get_required_provider_names() -> tuple[str, ...]:
    """Return stable required provider names in deterministic order.

    Returns:
        Exact provider-name tuple.
    """
    return tuple(get_route_dependency_bindings())


def build_in_process_graph(
    providers: Mapping[str, object],
    *,
    owned_resource_closers: tuple[Callable[[], object], ...] = (),
) -> object:
    """Build one exact in-process composition graph.

    Args:
        providers: Exact named owner dependencies or operation callables.
        owned_resource_closers: API-owned shutdown callbacks in acquisition order.

    Returns:
        Opaque validated graph consumed by canonical application composition.

    Raises:
        ValueError: If provider names or values are incomplete or invalid.
        TypeError: If a closer or operation provider is not callable.
    """
    bindings = get_route_dependency_bindings()
    required = set(bindings)
    supplied = set(providers)
    missing = sorted(required - supplied)
    unknown = sorted(supplied - required)
    if missing:
        message = f"missing in-process providers: {', '.join(missing)}"
        raise ValueError(message)
    if unknown:
        message = f"unknown in-process providers: {', '.join(unknown)}"
        raise ValueError(message)
    if any(value is None for value in providers.values()):
        raise ValueError("in-process provider values must not be None")
    for name, value in providers.items():
        if not callable(value):
            message = f"in-process provider must be callable: {name}"
            raise TypeError(message)
    if any(not callable(closer) for closer in owned_resource_closers):
        raise TypeError("owned resource closers must be callable")
    probes = {
        name: _constant_provider(providers[name])
        for name in get_required_provider_names()
    }
    overrides = {bindings[name]: probes[name] for name in get_required_provider_names()}
    return _InProcessGraph(
        overrides=MappingProxyType(overrides),
        probes=MappingProxyType(probes),
        owned_resource_closers=owned_resource_closers,
    )


def _require_graph(value: object) -> _InProcessGraph:
    """Narrow an opaque public graph value.

    Returns:
        Validated internal graph.

    Raises:
        TypeError: If the value did not originate from this composition boundary.
    """
    if not isinstance(value, _InProcessGraph):
        raise TypeError("invalid in-process API graph")
    return value


def get_graph_overrides(
    graph: object,
) -> Mapping[Callable[..., object], Callable[[], object]]:
    """Return internal FastAPI overrides for one graph.

    Returns:
        Immutable dependency override mapping.
    """
    return _require_graph(graph).overrides


def get_graph_probes(graph: object) -> Mapping[str, Callable[[], object]]:
    """Return required startup probes for one graph.

    Returns:
        Immutable named probe mapping.
    """
    return _require_graph(graph).probes


def get_graph_closers(graph: object) -> tuple[Callable[[], object], ...]:
    """Return API-owned shutdown callbacks for one graph.

    Returns:
        Callbacks in acquisition order.
    """
    return _require_graph(graph).owned_resource_closers


__all__ = (
    "build_in_process_graph",
    "get_graph_closers",
    "get_graph_overrides",
    "get_graph_probes",
    "get_required_provider_names",
)
