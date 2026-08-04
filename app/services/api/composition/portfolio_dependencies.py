"""Composition of governed Portfolio construction behind the API boundary.

The Portfolio domain exposes a function-only, opaque-handle public API. This
module mirrors :mod:`app.services.api.composition.simulation_dependencies` and
:mod:`app.services.api.composition.trading_dependencies`: it assembles the
Portfolio receiver-owned dependency bundle through Portfolio package-root
factories only, then exposes one route-layer dispatcher that validates API
DTOs and delegates exactly once to Portfolio public functions.

The canonical application binds ``portfolio.source`` to ``None`` by default so
every Portfolio route fails closed (HTTP 503) until an explicit dependency
bundle is supplied via ``create_app(..., portfolio_dependencies=...)``. This
honours "No Live Action by Default".
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, cast

from app.services.portfolio import (
    build_portfolio_state_store,
    construct_portfolio,
    create_portfolio_handle,
    create_portfolio_value,
    get_portfolio_history,
    get_portfolio_status,
)

type AuthContext = Any
type _PortfolioOperation = Callable[..., object]


def _to_tuple_strict(value: object) -> object:
    """Recursively convert JSON-style lists to tuples for strict contracts.

    Portfolio contracts enable Pydantic ``strict=True`` and reject ``list``
    inputs for ``tuple``-typed fields. API boundary DTOs serialize sequences
    as JSON lists, so the bridge normalizes every nested list to a tuple before
    handing the payload to the strict Portfolio value factory.

    Args:
        value: Candidate JSON-style payload fragment.

    Returns:
        The same fragment with every list replaced by a tuple.
    """
    if isinstance(value, list):
        return tuple(_to_tuple_strict(item) for item in value)
    if isinstance(value, dict):
        return {key: _to_tuple_strict(item) for key, item in value.items()}
    return value


def build_api_portfolio_dependencies(
    *,
    settings: object,
    ports: Mapping[str, Callable[..., object]],
) -> object:
    """Build the complete Portfolio receiver-owned dependency bundle.

    The Portfolio service is composed through three opaque handle layers, all
    constructed through Portfolio package-root factories only:

    1. ``PortfolioRepository`` over a durable Portfolio state store.
    2. ``PortfolioWorkflowDependencies`` binding the twelve cross-domain
       callbacks supplied by the caller.
    3. ``PortfolioWorkflowService`` from settings, repository, and dependencies.
    4. ``PortfolioService`` from the workflow service and repository.

    Args:
        settings: Complete Portfolio-owned settings value built through
            :func:`create_portfolio_value`.
        ports: Exact twelve public owner operations required by Portfolio
            workflows, keyed by their ``PortfolioWorkflowDependencies`` field
            names: ``strategy_reference_source``,
            ``eligibility_decision_source``, ``construction_evidence_source``,
            ``simulation_runner``, ``risk_reviewer``,
            ``risk_budget_activator``, ``kill_switch_source``,
            ``trading_executor``, ``trading_execution_source``,
            ``analytics_measurer``, ``audit_persister``, and ``clock``.

    Returns:
        Opaque ``PortfolioService`` handle accepted by Portfolio public
        operations.
    """
    repository = create_portfolio_handle(
        "PortfolioRepository",
        build_portfolio_state_store(),
    )
    dependencies = create_portfolio_handle(
        "PortfolioWorkflowDependencies",
        **dict(ports),
    )
    workflows = create_portfolio_handle(
        "PortfolioWorkflowService",
        settings,
        repository,
        dependencies,
    )
    return create_portfolio_handle("PortfolioService", workflows, repository)


def build_portfolio_source(
    service_handle: object | None,
) -> _PortfolioOperation:
    """Build one Portfolio route operation dispatcher.

    The dispatcher validates each API DTO through the Portfolio value factory
    and delegates exactly once to the matching Portfolio public function. When
    no dependency bundle has been composed it raises a deterministic sentinel
    error that the route layer translates to HTTP 503.

    Args:
        service_handle: Complete opaque ``PortfolioService`` handle, or
            ``None`` when the canonical application has not composed a
            Portfolio dependency bundle.

    Returns:
        Route operation dispatcher bound to the composed handle.
    """

    def _operation(operation: str, *args: object) -> object:
        """Validate API inputs and delegate once to Portfolio public functions.

        Args:
            operation: Canonical Portfolio route operation name
                (``construct``, ``status``, or ``history``).
            *args: Operation-specific positional inputs.

        Returns:
            Portfolio-owned standard response envelope.

        Raises:
            RuntimeError: If the Portfolio dependency bundle is unavailable.
            ValueError: If the requested operation is not one of the three
                registered Portfolio route operations.
        """
        if service_handle is None:
            raise RuntimeError("PORTFOLIO_RUNTIME_UNAVAILABLE")
        if operation == "construct":
            boundary_request = cast("Any", args[0])
            payload = cast(
                "dict[str, object]",
                _to_tuple_strict(
                    boundary_request.model_dump(mode="python", warnings=False)
                ),
            )
            request = create_portfolio_value("PortfolioConstructionRequest", **payload)
            auth_context = cast("AuthContext", args[1])
            return construct_portfolio(service_handle, request, auth_context)
        if operation == "status":
            portfolio_id = cast("str", args[0])
            scope = cast("Mapping[str, str]", args[1])
            auth_context = cast("AuthContext", args[2])
            return get_portfolio_status(
                service_handle, portfolio_id, scope, auth_context
            )
        if operation == "history":
            portfolio_id = cast("str", args[0])
            auth_context = cast("AuthContext", args[1])
            return get_portfolio_history(service_handle, portfolio_id, auth_context)
        raise ValueError("unsupported Portfolio operation")

    return _operation


__all__ = ("build_api_portfolio_dependencies", "build_portfolio_source")
