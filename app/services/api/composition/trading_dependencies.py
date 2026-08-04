"""Composition of governed Trading mutations behind the API boundary."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, cast

from app.services.trading import (
    cancel_order,
    close_position,
    create_trading_dependencies,
    create_trading_request,
    submit_order,
)

type AuthContext = Any
type _MutationOperation = Callable[[str, object, AuthContext], Awaitable[object]]


def build_api_trading_dependencies(**values: object) -> object:
    """Build a complete Trading-owned dependency container.

    Args:
        **values: Exact Trading state, broker, Risk, evidence, and lifecycle ports.

    Returns:
        Opaque dependency container accepted by Trading mutation functions.
    """
    return create_trading_dependencies(**values)


def build_trading_mutation_source(dependencies: object | None) -> _MutationOperation:
    """Build one governed Trading mutation dispatcher.

    Args:
        dependencies: Complete Trading-owned dependency container.

    Returns:
        Async route operation delegating exclusively to Trading public functions.
    """

    async def _mutate(
        operation: str, boundary_request: object, _auth: AuthContext
    ) -> object:
        """Validate and delegate one governed mutation.

        Returns:
            Trading-owned mutation receipt.

        Raises:
            RuntimeError: If Trading dependencies are unavailable.
            ValueError: If the requested operation is unsupported.
        """
        if dependencies is None:
            raise RuntimeError("TRADING_MUTATIONS_UNAVAILABLE")
        request = create_trading_request(
            **cast("Any", boundary_request).model_dump(mode="python", warnings=False)
        )
        operations = {
            "submit_order": submit_order,
            "cancel_order": cancel_order,
            "close_position": close_position,
        }
        try:
            selected = operations[operation]
        except KeyError as error:
            raise ValueError("unsupported Trading mutation") from error
        return await selected(request, cast("Any", dependencies))

    return _mutate


__all__ = ("build_api_trading_dependencies", "build_trading_mutation_source")
