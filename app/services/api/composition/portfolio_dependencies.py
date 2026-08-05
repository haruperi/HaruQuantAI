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

from app.services import risk
from app.services.portfolio import (
    activate_portfolio,
    assess_portfolio_drift,
    build_portfolio_state_store,
    construct_portfolio,
    create_portfolio_handle,
    create_portfolio_value,
    execute_portfolio_handle_operation,
    get_portfolio_history,
    get_portfolio_status,
    recompute_portfolio_measurement,
    rollback_portfolio,
    submit_portfolio_rebalance,
)
from app.services.simulator import create_simulation_value

type AuthContext = Any
type _PortfolioOperation = Callable[..., object]
type _Handler = Callable[[tuple[object, ...]], object]


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
    service = create_portfolio_handle("PortfolioService", workflows, repository)
    return {"service": service, "workflows": workflows}


def _resolve_handles(bundle: object) -> tuple[object, object | None]:
    """Split a composed Portfolio bundle into its service and workflow handles.

    ``build_api_portfolio_dependencies`` returns both handles because the
    governed lifecycle operations need the workflow handle's allow-listed
    ``construct`` and ``coordinate_review`` operations, which the outer
    ``PortfolioService`` does not expose. A bare handle remains accepted so an
    existing composition that supplies only a ``PortfolioService`` keeps working
    for the three read/construct operations.

    Args:
        bundle: Composed Portfolio dependency bundle or a bare service handle.

    Returns:
        Tuple of the service handle and the optional workflow handle.
    """
    if isinstance(bundle, Mapping):
        return bundle.get("service"), bundle.get("workflows")
    return bundle, None


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
    service, workflows = _resolve_handles(service_handle)
    handlers = _build_handlers(service, workflows)

    def _operation(operation: str, *args: object) -> object:
        """Validate API inputs and delegate once to Portfolio public functions.

        Args:
            operation: Canonical Portfolio route operation name.
            *args: Operation-specific positional inputs.

        Returns:
            Portfolio-owned standard response envelope.

        Raises:
            RuntimeError: If the Portfolio dependency bundle is unavailable.
            ValueError: If the requested operation is not registered.
        """
        if service is None:
            raise RuntimeError("PORTFOLIO_RUNTIME_UNAVAILABLE")
        handler = handlers.get(operation)
        if handler is None:
            raise ValueError("unsupported Portfolio operation")
        return handler(args)

    return _operation


def _build_handlers(
    service: object | None,
    workflows: object | None,
) -> Mapping[str, _Handler]:
    """Build the immutable operation-name to handler dispatch table.

    Args:
        service: Composed ``PortfolioService`` handle, or ``None``.
        workflows: Composed ``PortfolioWorkflowService`` handle, or ``None``.

    Returns:
        Mapping of canonical operation name to its single-delegation handler.
    """
    return {
        "construct": lambda args: construct_portfolio(
            service,
            _construction_request(args[0]),
            cast("AuthContext", args[1]),
        ),
        "status": lambda args: get_portfolio_status(
            service,
            cast("str", args[0]),
            cast("Mapping[str, str]", args[1]),
            cast("AuthContext", args[2]),
        ),
        "history": lambda args: get_portfolio_history(
            service, cast("str", args[0]), cast("AuthContext", args[1])
        ),
        "activate": lambda args: _activation(service, workflows, "activate", args),
        "rollback": lambda args: _activation(service, workflows, "rollback", args),
        "drift": lambda args: _drift(service, args),
        "rebalance": lambda args: _rebalance(service, args),
        "recompute": lambda args: _recompute(service, args),
    }


def _recompute(service: object, args: tuple[object, ...]) -> object:
    """Delegate one measurement recomputation to Portfolio.

    Args:
        service: Composed ``PortfolioService`` handle.
        args: ``(boundary_request, auth_context)`` inputs.

    Returns:
        Portfolio-owned measurement envelope.
    """
    boundary = cast("Any", args[0])
    return recompute_portfolio_measurement(
        service,
        boundary.plan_id,
        trading_request_id=boundary.trading_request_id,
        auth_context=cast("AuthContext", args[1]),
    )


def _dump(payload: object) -> dict[str, object]:
    """Normalize a boundary DTO into strict-contract-safe constructor fields.

    Args:
        payload: Boundary DTO (Pydantic model) or serialized mapping.

    Returns:
        Field mapping with every nested list converted to a tuple.
    """
    source = (
        cast("Any", payload).model_dump(mode="python", warnings=False)
        if hasattr(payload, "model_dump")
        else payload
    )
    return cast("dict[str, object]", _to_tuple_strict(source))


def _construction_request(boundary_request: object) -> object:
    """Rebuild the strict Portfolio construction request from a boundary DTO.

    Args:
        boundary_request: Validated ``PortfolioConstructRequest`` boundary DTO.

    Returns:
        Validated Portfolio-owned construction request value.
    """
    return create_portfolio_value(
        "PortfolioConstructionRequest", **_dump(boundary_request)
    )


def _activation(
    service: object,
    workflows: object | None,
    operation: str,
    args: tuple[object, ...],
) -> object:
    """Run the complete governed activation or rollback chain.

    Activation is one governed write spanning the owner workflow chain
    WF-PORT-001 through WF-PORT-004. The workflow handle constructs the
    candidate together with its validated evidence, coordinates the Simulation
    and Risk review, and the outer service performs the atomic activation. The
    gateway supplies no evidence and decides no approval; Risk remains the sole
    approval authority and Portfolio remains the sole activation authority.

    Args:
        service: Composed ``PortfolioService`` handle.
        workflows: Composed ``PortfolioWorkflowService`` handle.
        operation: Either ``activate`` or ``rollback``.
        args: ``(boundary_request, auth_context, idempotency_key)`` inputs.

    Returns:
        Portfolio-owned active allocation envelope.

    Raises:
        RuntimeError: If no workflow handle has been composed.
    """
    if workflows is None:
        raise RuntimeError("PORTFOLIO_RUNTIME_UNAVAILABLE")
    boundary = cast("Any", args[0])
    auth_context = cast("AuthContext", args[1])
    idempotency_key = cast("str", args[2])

    request = _construction_request(boundary.construction)
    candidate, evidence = cast(
        "tuple[Any, Any]",
        execute_portfolio_handle_operation(workflows, "construct", request),
    )
    simulation_request = create_simulation_value(
        "PortfolioBacktestRequestV1", **_dump(boundary.simulation)
    )
    review = execute_portfolio_handle_operation(
        workflows,
        "coordinate_review",
        candidate,
        simulation_request,
        evidence,
        approval_refs=tuple(boundary.approval_refs),
    )
    attestation = _risk_value("approval_attestation", boundary.approval_attestation)
    validation = _risk_value("approval_validation", boundary.approval_validation)
    if operation == "activate":
        return activate_portfolio(
            service,
            candidate,
            evidence,
            review,
            approval_attestation=attestation,
            approval_validation=validation,
            expires_at=boundary.expires_at,
            idempotency_key=idempotency_key,
            expected_predecessor=boundary.expected_predecessor,
            expected_revision=boundary.expected_revision,
            auth_context=auth_context,
        )
    return rollback_portfolio(
        service,
        candidate,
        evidence,
        review,
        rollback_of_version=boundary.rollback_of_version,
        approval_attestation=attestation,
        approval_validation=validation,
        expires_at=boundary.expires_at,
        idempotency_key=idempotency_key,
        expected_predecessor=boundary.expected_predecessor,
        expected_revision=boundary.expected_revision,
        auth_context=auth_context,
    )


_RISK_GOVERNANCE_FACTORIES: Mapping[str, Callable[..., object]] = {
    "approval_attestation": risk.create_approval_attestation,
    "approval_validation": risk.create_approval_validation_result,
}


def _risk_value(kind: str, payload: object | None) -> object | None:
    """Rebuild one optional Risk-owned governance value through Risk's factory.

    Risk owns approval semantics; the gateway only projects the caller-supplied
    payload back into a Risk-validated value and never fills in a default.

    Args:
        kind: Registered governance value kind.
        payload: Caller-supplied owner-shaped mapping, or ``None``.

    Returns:
        Validated Risk-owned value, or ``None`` when no payload was supplied.
    """
    if payload is None:
        return None
    factory = _RISK_GOVERNANCE_FACTORIES[kind]
    return factory(**dict(cast("Mapping[str, object]", payload)))


def _drift(service: object, args: tuple[object, ...]) -> object:
    """Delegate one drift assessment against the active allocation.

    Args:
        service: Composed ``PortfolioService`` handle.
        args: ``(portfolio_id, boundary_request, auth_context)`` inputs.

    Returns:
        Portfolio-owned drift observation envelope.

    Raises:
        RuntimeError: If the active allocation cannot be read.
    """
    portfolio_id = cast("str", args[0])
    boundary = cast("Any", args[1])
    auth_context = cast("AuthContext", args[2])

    status_response = get_portfolio_status(
        service, portfolio_id, dict(boundary.scope), auth_context
    )
    allocation = getattr(status_response, "data", None)
    if allocation is None:
        raise RuntimeError("PORTFOLIO_ALLOCATION_UNAVAILABLE")
    eligibility = {
        key: cast(
            "Any",
            risk.create_strategy_operational_eligibility_decision(**dict(value)),
        )
        for key, value in boundary.eligibility_decisions.items()
    }
    return assess_portfolio_drift(
        service,
        allocation,
        actual_exposures=dict(boundary.actual_exposures),
        evidence_as_of=boundary.evidence_as_of,
        risk_decision=risk.create_allocation_risk_decision(
            **dict(boundary.risk_decision)
        ),
        eligibility_decisions=eligibility,
        auth_context=auth_context,
    )


def _rebalance(service: object, args: tuple[object, ...]) -> object:
    """Delegate one governed rebalance submission to Portfolio.

    Args:
        service: Composed ``PortfolioService`` handle.
        args: ``(boundary_request, auth_context)`` inputs.

    Returns:
        Awaitable Portfolio-owned rebalance submission envelope.
    """
    boundary = cast("Any", args[0])
    auth_context = cast("AuthContext", args[1])
    plan = create_portfolio_value(
        "PortfolioRebalancePlan", **_dump(dict(boundary.plan))
    )
    return submit_portfolio_rebalance(
        service,
        plan,
        account_evidence_ref=boundary.account_evidence_ref,
        market_evidence_ref=boundary.market_evidence_ref,
        fx_evidence_refs=tuple(boundary.fx_evidence_refs),
        runtime_profile=boundary.runtime_profile,
        execution_route=boundary.execution_route,
        approval_refs=tuple(boundary.approval_refs),
        approval_token_ref=boundary.approval_token_ref,
        trading_request_id=boundary.trading_request_id,
        valid_until=boundary.valid_until,
        auth_context=auth_context,
    )


__all__ = ("build_api_portfolio_dependencies", "build_portfolio_source")
