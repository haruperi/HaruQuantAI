"""Composition of synchronous Simulator execution behind the API boundary."""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Mapping
from pathlib import Path
from typing import Any, Literal, cast

from app.services.simulator import (
    build_simulation_run_dependencies,
    build_simulation_state_store,
    create_simulation_session,
    create_simulation_value,
    run_backtest,
    run_portfolio_backtest,
    stream_simulation_session_frames,
    to_simulation_error_payload,
    unwrap_simulation_response,
)

type AuthContext = Any
type _RunOperation = Callable[
    [Literal["run", "portfolio-run"], object, AuthContext], object
]
type _SessionOperation = Callable[..., object]


def build_api_simulation_dependencies(
    *,
    artifact_root: Path,
    ports: Mapping[str, Callable[..., object]],
    fast_research_enabled: bool = False,
) -> object:
    """Build the complete Simulator receiver-owned dependency bundle.

    Args:
        artifact_root: Approved Simulator artifact directory.
        ports: Exact eleven public owner operations required by Simulator.
        fast_research_enabled: Whether explicitly non-canonical research may run.

    Returns:
        Opaque bundle accepted by Simulator public run operations.
    """
    state_store = build_simulation_state_store(artifact_root=artifact_root)
    return build_simulation_run_dependencies(
        state_store=state_store,
        artifact_root=artifact_root,
        fast_research_enabled=fast_research_enabled,
        ports=ports,
    )


def build_simulation_run_source(dependencies: object | None) -> _RunOperation:
    """Build one synchronous Simulation route operation.

    Args:
        dependencies: Complete receiver-owned ``SimulationRunDependencies`` bundle.

    Returns:
        Route operation that validates API DTOs through Simulator-owned contracts.
    """

    def _run(
        operation: Literal["run", "portfolio-run"],
        boundary_request: object,
        auth: AuthContext,
    ) -> object:
        """Validate and execute one canonical Simulation operation.

        Returns:
            Simulator-owned canonical result.

        Raises:
            RuntimeError: If the Simulator dependency bundle is unavailable.
        """
        if dependencies is None:
            raise RuntimeError("SIMULATION_RUNTIME_UNAVAILABLE")
        payload = cast("Any", boundary_request).model_dump(
            mode="python", warnings=False
        )
        if operation == "run":
            request = create_simulation_value("SimulationBacktestRequestV1", **payload)
            return run_backtest(request, auth, dependencies)
        request = create_simulation_value("PortfolioBacktestRequestV1", **payload)
        return run_portfolio_backtest(request, auth, dependencies)

    return _run


def _runtime_code(error: Exception) -> str:
    """Map one Simulator failure to its bounded public code.

    Returns:
        Stable Simulator error code.
    """
    payload = to_simulation_error_payload(error)
    return str(payload["code"])


def build_simulation_session_source(  # noqa: C901 - two bounded operations.
    dependencies: object | None,
) -> _SessionOperation:
    """Build completed-run session creation and frame delivery operations.

    Args:
        dependencies: Complete receiver-owned Simulation dependency bundle.

    Returns:
        Operation dispatcher bound to the approved Simulation artifact root.
    """

    async def _frames(
        session_id: str, resume_after: int | None
    ) -> AsyncIterator[object]:
        """Yield owner journal events and expose only bounded failures.

        Yields:
            Ordered Simulator-owned journal events.

        Raises:
            RuntimeError: If playback is unavailable or fails validation.
        """
        if dependencies is None:
            raise RuntimeError("SIMULATION_PLAYBACK_UNAVAILABLE")
        try:
            iterator = cast(
                "AsyncIterator[object]",
                stream_simulation_session_frames(
                    session_id,
                    resume_after=resume_after,
                    dependencies=dependencies,
                ),
            )
            async for event in iterator:
                yield event
        except RuntimeError:
            raise
        except Exception as error:
            raise RuntimeError(_runtime_code(error)) from error

    def _session(operation: str, *args: object, **kwargs: object) -> object:
        """Dispatch one session operation through Simulator package-root APIs.

        Returns:
            Created session projection or frame iterator.

        Raises:
            RuntimeError: If playback is unavailable or Simulator fails.
            ValueError: If the requested operation is unsupported.
        """
        if dependencies is None:
            raise RuntimeError("SIMULATION_PLAYBACK_UNAVAILABLE")
        if operation == "create":
            try:
                response = create_simulation_session(
                    str(args[0]), request_id=str(kwargs["request_id"])
                )
                return unwrap_simulation_response(
                    response,
                    operation="api.simulation.create_session",
                )
            except Exception as error:
                raise RuntimeError(_runtime_code(error)) from error
        if operation == "frames":
            return _frames(str(args[0]), cast("int | None", kwargs["resume_after"]))
        raise ValueError("unsupported Simulation session operation")

    return _session


__all__ = (
    "build_api_simulation_dependencies",
    "build_simulation_run_source",
    "build_simulation_session_source",
)
