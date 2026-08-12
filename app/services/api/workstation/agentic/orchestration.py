"""Composition of the Agentic operator surface behind the API boundary.

The Agentic domain exposes a function-only public operator surface
(:mod:`app.agentic`). This module mirrors
the Portfolio feature orchestrator: it assembles the
explicit ``AgenticDependencies`` bundle through the Agentic package-root
factories only, then exposes one route-layer dispatcher that delegates exactly
once to the eight Agentic operator operations.

``submit_firm_request`` reserves a run; it does **not** execute agents. The
firm has never run for real (see ``app/agentic/public_api/README.md`` §1), and
this bridge intentionally exposes the reserve/inspect/audit/governance tier
only. Execution remains a separate, future effort.

The canonical application binds ``agentic.source`` to ``None`` by default so
every Agentic route fails closed (HTTP 503) until an explicit dependency
bundle is supplied via ``create_app(..., agentic_dependencies=...)``. This
honours "No Live Action by Default".
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal, cast

from app.agentic import (
    approve_agentic_handoff,
    build_durable_agentic_dependencies,
    cancel_firm_run,
    disable_agentic,
    get_firm_audit,
    get_firm_run,
    quarantine_firm_agent,
    submit_firm_request,
)
from app.utils import get_logger

logger = get_logger(__name__)

type AuthContext = Any
type DrainPolicy = Literal["cancel", "drain"]
type OperatorArgs = tuple[object, ...]
type OperatorDispatcher = Callable[..., object]
type OperationHandler = Callable[
    [Any, AuthContext, OperatorArgs, datetime | None], object
]

_RUNTIME_UNAVAILABLE = "AGENTIC_RUNTIME_UNAVAILABLE"
_UNSUPPORTED_OPERATION = "unsupported Agentic operation"


def build_api_agentic_dependencies(
    settings: object,
    mandate: object,
    registry: object,
    definitions: Mapping[str, object],
    agent_policies: Mapping[str, object],
    tool_policies: Mapping[str, object],
) -> object:
    """Build the complete Agentic dependency bundle with durable stores.

    Every argument is required: the Agentic domain refuses a partially wired
    firm, and constructing one here would only defer the failure to the point
    where it matters least. The durable store adapters are wired by the
    Agentic package-root :func:`build_durable_agentic_dependencies` factory.

    Args:
        settings: Resolved Agentic settings, including master enablement.
        mandate: Validated signed firm mandate.
        registry: Validated role registry.
        definitions: Registered workflow definition per workflow name. May be
            empty; ``submit`` then refuses ``WORKFLOW_NOT_REGISTERED``.
        agent_policies: Registered agent policy per role.
        tool_policies: Registered tool policy per tool name.

    Returns:
        The frozen ``AgenticDependencies`` record accepted by every Agentic
        operator operation.
    """
    logger.info("Building durable Agentic API dependencies")
    return build_durable_agentic_dependencies(
        cast("Any", settings),
        cast("Any", mandate),
        cast("Any", registry),
        cast("Any", definitions),
        cast("Any", agent_policies),
        cast("Any", tool_policies),
    )


def build_agentic_source(
    dependencies: object | None,
) -> OperatorDispatcher:
    """Build one Agentic route operation dispatcher.

    The dispatcher delegates exactly once to the matching Agentic operator
    function. When no dependency bundle has been composed it raises a
    deterministic sentinel error that the route layer translates to HTTP 503.

    Operator payloads are string mappings by design
    (:mod:`app.agentic.public_api.service`): no prompt, credential, or
    provider internal crosses this boundary, and the operator ``auth``
    principal is projected from the Utils-owned ``AuthContext``.

    Args:
        dependencies: Complete ``AgenticDependencies`` bundle, or ``None`` when
            the canonical application has not composed one.

    Returns:
        Route operation dispatcher bound to the composed bundle.
    """
    handlers = _operation_handlers()

    def _operation(operation: str, *args: object) -> object:
        """Delegate once to one Agentic operator function.

        Args:
            operation: Canonical Agentic route operation name.
            *args: Operation-specific positional inputs. The authenticated
                principal is always ``args[0]`` and the optional operation
                time is always ``args[-1]``.

        Returns:
            The Agentic ``OperatorOutcome`` typed outcome.

        Raises:
            RuntimeError: If the Agentic dependency bundle is unavailable.
            ValueError: If the requested operation is not registered.
        """
        if dependencies is None:
            raise RuntimeError(_RUNTIME_UNAVAILABLE)
        handler = handlers.get(operation)
        if handler is None:
            raise ValueError(_UNSUPPORTED_OPERATION)
        auth = cast("AuthContext", args[0])
        rest = args[1:-1]
        at_time = _datetime_or_none(args[-1])
        deps = cast("Any", dependencies)
        return handler(deps, auth, rest, at_time)

    return _operation


def _operation_handlers() -> Mapping[str, OperationHandler]:
    """Return the canonical operation-name to handler-function map.

    Each handler adapts the positional route arguments to the keyword
    signature of one Agentic operator function. Argument arity is enforced by
    the route layer's validated DTOs; the handlers trust that contract.

    Returns:
        Immutable mapping of operation name to handler.
    """

    def submit(
        deps: object,
        auth: AuthContext,
        args: OperatorArgs,
        at_time: datetime | None,
    ) -> object:
        """Forward workflow, objective, refs, key, and budget once.

        Returns:
            The Agentic ``OperatorOutcome`` typed outcome.
        """
        return submit_firm_request(
            cast("Any", deps),
            auth,
            workflow_name=str(args[0]),
            objective=str(args[1]),
            input_refs=_tuple_str(args[2]),
            idempotency_key=str(args[3]),
            deadline_seconds=cast("int", args[4]),
            cost_budget=_decimal_or_none(args[5]),
            at_time=at_time,
        )

    def inspect(
        deps: object,
        auth: AuthContext,
        args: OperatorArgs,
        at_time: datetime | None,
    ) -> object:
        """Forward one run identifier once.

        Returns:
            The Agentic ``OperatorOutcome`` typed outcome.
        """
        return get_firm_run(cast("Any", deps), auth, str(args[0]), at_time=at_time)

    def cancel(
        deps: object,
        auth: AuthContext,
        args: OperatorArgs,
        at_time: datetime | None,
    ) -> object:
        """Forward one run identifier and cancellation reason once.

        Returns:
            The Agentic ``OperatorOutcome`` typed outcome.
        """
        return cancel_firm_run(
            cast("Any", deps), auth, str(args[0]), reason=str(args[1]), at_time=at_time
        )

    def audit(
        deps: object,
        auth: AuthContext,
        args: OperatorArgs,
        at_time: datetime | None,
    ) -> object:
        """Forward one task and run identifier once.

        Returns:
            The Agentic ``OperatorOutcome`` typed outcome.
        """
        return get_firm_audit(
            cast("Any", deps),
            auth,
            task_id=str(args[0]),
            run_id=str(args[1]),
            at_time=at_time,
        )

    def approve(
        deps: object,
        auth: AuthContext,
        args: OperatorArgs,
        at_time: datetime | None,
    ) -> object:
        """Forward one artefact hash, id, and rationale once.

        Returns:
            The Agentic ``OperatorOutcome`` typed outcome.
        """
        return approve_agentic_handoff(
            cast("Any", deps),
            auth,
            artifact_hash=str(args[0]),
            artifact_id=str(args[1]),
            rationale=str(args[2]),
            at_time=at_time,
        )

    def quarantine(
        deps: object,
        auth: AuthContext,
        args: OperatorArgs,
        at_time: datetime | None,
    ) -> object:
        """Forward one incident classification and evidence once.

        Returns:
            The Agentic ``OperatorOutcome`` typed outcome.
        """
        return quarantine_firm_agent(
            cast("Any", deps),
            auth,
            run_id=str(args[0]),
            kind=cast("Any", args[1]),
            trigger=str(args[2]),
            role_id=str(args[3]),
            preserved_evidence_refs=_tuple_str(args[4]),
            checkpoint_ref=str(args[5]),
            at_time=at_time,
        )

    def disable(
        deps: object,
        auth: AuthContext,
        args: OperatorArgs,
        at_time: datetime | None,
    ) -> object:
        """Forward run identifiers and drain policy once.

        Returns:
            The Agentic ``OperatorOutcome`` typed outcome.
        """
        return disable_agentic(
            cast("Any", deps),
            auth,
            run_ids=_tuple_str(args[0]),
            policy=cast("DrainPolicy", args[1]),
            at_time=at_time,
        )

    return {
        "approve": approve,
        "audit": audit,
        "cancel": cancel,
        "disable": disable,
        "inspect": inspect,
        "quarantine": quarantine,
        "submit": submit,
    }


def _datetime_or_none(value: object) -> datetime | None:
    """Coerce one optional operation time.

    Args:
        value: Candidate time, or ``None`` for "now".

    Returns:
        Validated operation time, or ``None``.
    """
    if value is None:
        return None
    return cast("datetime", value)


def _tuple_str(value: object) -> tuple[str, ...]:
    """Normalize one JSON-style sequence into a tuple of strings.

    API DTOs serialize evidence references and run identifiers as JSON lists;
    Agentic strict contracts require tuples.

    Args:
        value: Candidate sequence.

    Returns:
        Tuple of strings.
    """
    if isinstance(value, str):
        return (value,)
    return tuple(cast("tuple[str, ...] | list[str]", value))


def _decimal_or_none(value: object) -> Decimal | None:
    """Coerce one optional decimal budget.

    Args:
        value: Candidate decimal, numeric string, or ``None``.

    Returns:
        Validated decimal budget, or ``None``.
    """
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


__all__ = ("build_agentic_source", "build_api_agentic_dependencies")
