"""Composition of governed Strategy mutations behind the API boundary.

Strategy registration requires a Strategy-owned validation policy that the
gateway must never choose for itself: the policy decides what counts as an
acceptable strategy version. This module therefore accepts an already-built
policy as an explicit composition dependency and exposes one route-layer
dispatcher that forwards caller payloads to Strategy package-root factories and
functions.

The canonical application binds ``strategy.mutation_source`` to ``None`` by
default so every Strategy mutation route fails closed (HTTP 503) until a policy
is supplied via ``create_app(..., strategy_dependencies=...)``. Catalogue and
version reads are unaffected and remain always available.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, cast

from app.services.strategy import (
    create_strategy_parameter_update_request,
    create_strategy_registration_request,
    register_strategy_version,
    update_strategy_parameters,
)

type AuthContext = Any
type _StrategyOperation = Callable[..., object]


def build_api_strategy_dependencies(*, validation_policy: object) -> object:
    """Build the Strategy receiver-owned dependency bundle.

    Args:
        validation_policy: Strategy-owned validation policy built through a
            Strategy package-root factory, such as
            ``build_development_strategy_validation_policy``.

    Returns:
        Opaque bundle accepted by the Strategy mutation dispatcher.
    """
    return {"validation_policy": validation_policy}


def build_strategy_mutation_source(bundle: object | None) -> _StrategyOperation:
    """Build one Strategy mutation dispatcher.

    Args:
        bundle: Composed Strategy dependency bundle, or ``None`` when the
            canonical application has not composed one.

    Returns:
        Route operation dispatcher bound to the composed bundle.
    """

    def _operation(operation: str, *args: object) -> object:
        """Forward one Strategy mutation to its public owner function.

        Args:
            operation: Either ``register`` or ``update_parameters``.
            *args: ``(payload, auth_context)`` positional inputs.

        Returns:
            Strategy-owned immutable mutation result.

        Raises:
            RuntimeError: If no Strategy dependency bundle is composed.
            ValueError: If the requested operation is not registered.
        """
        if bundle is None:
            raise RuntimeError("STRATEGY_RUNTIME_UNAVAILABLE")
        payload = dict(cast("Mapping[str, object]", args[0]))
        auth_context = cast("AuthContext", args[1])
        if operation == "register":
            policy = cast("dict[str, object]", bundle)["validation_policy"]
            request = create_strategy_registration_request(**payload)
            return register_strategy_version(
                cast("Any", request), auth_context, cast("Any", policy)
            )
        if operation == "update_parameters":
            update = create_strategy_parameter_update_request(**payload)
            return update_strategy_parameters(cast("Any", update), auth_context)
        raise ValueError("unsupported Strategy operation")

    return _operation


__all__ = ("build_api_strategy_dependencies", "build_strategy_mutation_source")
