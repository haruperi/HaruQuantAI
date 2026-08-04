"""Composition of synchronous Simulator execution behind the API boundary."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Literal, cast

from app.services.simulator import (
    build_simulation_run_dependencies,
    build_simulation_state_store,
    create_simulation_value,
    run_backtest,
    run_portfolio_backtest,
)

type AuthContext = Any
type _RunOperation = Callable[
    [Literal["run", "portfolio-run"], object, AuthContext], object
]


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


__all__ = ("build_api_simulation_dependencies", "build_simulation_run_source")
