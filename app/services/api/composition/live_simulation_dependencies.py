"""Composition of live what-if Simulation sessions behind the API boundary.

A live session walks a prepared run forward in increments so an analyst can ask
"what if this had been different" without disturbing a recorded result. The
Simulator owns every rule that matters here — determinism, branch lineage,
session capacity, and the advisory status of a branch. This module only
reconstructs the boundary DTO into the owner request and delegates.

Two properties are worth stating at the boundary because they shape what the
routes may claim:

* **Sessions are in-process and non-durable.** A gateway restart loses them.
  The routes therefore never promise persistence, and a lost session is
  reported as unknown rather than silently reopened.
* **Branch output is advisory.** Every projection carries ``advisory: true``
  and a branch journals under its own run identity, so a what-if answer can
  never be mistaken for an official ``SimulationResult``.

The canonical application binds ``simulation.live_source`` to ``None`` by
default, so every live route fails closed with HTTP 503 until an explicit
Simulator dependency bundle is supplied.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, cast

from app.services.simulator import (
    branch_live_simulation,
    close_live_simulation_session,
    create_live_simulation_session,
    create_simulation_value,
    read_live_simulation_state,
    step_live_simulation,
)

type AuthContext = Any
type _LiveOperation = Callable[..., object]
type _Handler = Callable[[tuple[object, ...]], object]


def build_live_simulation_source(dependencies: object | None) -> _LiveOperation:
    """Build one live what-if session dispatcher.

    Args:
        dependencies: Composed Simulator run dependency bundle, or ``None``
            when the canonical application has not composed one.

    Returns:
        Route operation dispatcher bound to the composed bundle.
    """
    handlers = _build_handlers(dependencies)

    def _operation(operation: str, *args: object) -> object:
        """Delegate one live-session operation to the Simulator.

        Args:
            operation: Canonical live-session operation name.
            *args: Operation-specific positional inputs.

        Returns:
            Simulator-owned session projection envelope.

        Raises:
            RuntimeError: If no Simulator dependency bundle is composed.
            ValueError: If the requested operation is not registered.
        """
        if dependencies is None:
            raise RuntimeError("SIMULATION_LIVE_RUNTIME_UNAVAILABLE")
        handler = handlers.get(operation)
        if handler is None:
            raise ValueError("unsupported live Simulation operation")
        return handler(args)

    return _operation


def _build_handlers(dependencies: object | None) -> Mapping[str, _Handler]:
    """Build the immutable operation-name to handler dispatch table.

    Args:
        dependencies: Composed Simulator run dependency bundle.

    Returns:
        Mapping of canonical operation name to its single-delegation handler.
    """
    return {
        "create": lambda args: create_live_simulation_session(
            cast("Any", _run_request(args[0])),
            cast("Any", dependencies),
            request_id=cast("str", args[1]),
        ),
        "step": lambda args: step_live_simulation(
            cast("str", args[0]), cast("int", args[1])
        ),
        "read": lambda args: read_live_simulation_state(cast("str", args[0])),
        "branch": lambda args: branch_live_simulation(
            cast("str", args[0]),
            cast("Mapping[str, object]", args[1]),
            cast("Any", dependencies),
            request_id=cast("str", args[2]),
        ),
        "close": lambda args: close_live_simulation_session(cast("str", args[0])),
    }


def _run_request(boundary_request: object) -> object:
    """Rebuild the Simulator-owned backtest request from a boundary DTO.

    Args:
        boundary_request: Validated ``SimulationRunRequest`` boundary DTO.

    Returns:
        Validated Simulator-owned backtest request value.
    """
    payload = cast("Any", boundary_request).model_dump(mode="python", warnings=False)
    return create_simulation_value(
        "SimulationBacktestRequestV1", **cast("dict[str, object]", payload)
    )


__all__ = ("build_live_simulation_source",)
