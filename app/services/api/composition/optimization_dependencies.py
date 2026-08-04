"""Composition of Optimization execution behind the API boundary.

The Optimization domain exposes a function-only public API whose run
operations require a concrete
:class:`~app.services.optimization.execution.contracts.BacktestExecutionAdapter`
built by threading an already-composed ``SimulationRunDependencies`` bundle
together with an Analytics configuration. This module mirrors
:mod:`app.services.api.composition.simulation_dependencies` and
:mod:`app.services.api.composition.portfolio_dependencies`: it assembles the
Optimization receiver-owned bundle through Optimization package-root factories
only, then exposes one route-layer dispatcher that validates API DTOs and
delegates exactly once to the Optimization public operations.

The canonical application binds ``optimization.source`` to ``None`` by default
so every Optimization route fails closed (HTTP 503) until an explicit
dependency bundle is supplied via
``create_app(..., optimization_dependencies=...)``. This honours "No Live
Action by Default".
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any, cast

from app.services.optimization import (
    build_optimization_handoff,
    build_simulation_analytics_backtest_adapter,
    calculate_parameter_stability,
    calculate_robustness_score,
    compare_optimization_runs,
    create_optimization_value,
    detect_overfit_parameters,
    load_optimization_result,
    rank_parameter_sets,
    run_parameter_sweep,
    run_robustness_analysis,
    run_walk_forward_matrix,
    run_walk_forward_optimization,
)

type AuthContext = Any
type _OptimizationOperation = Callable[..., object]
type _Handler = Callable[[tuple[object, ...]], object]


def build_api_optimization_dependencies(
    *,
    auth_context: object,
    simulation_dependencies: object,
    analytics_config: object,
    engine_type: str,
    engine_version: str,
    state_store: object | None = None,
) -> object:
    """Build the complete Optimization receiver-owned dependency bundle.

    The adapter wraps the already-composed ``SimulationRunDependencies`` plus
    the caller-constructed Analytics configuration through Optimization's
    package-root adapter factory. The optional state store is retained so the
    read operation can recover persisted results through Optimization's public
    read function.

    Args:
        auth_context: Shared authenticated invocation context.
        simulation_dependencies: Already-composed Simulator receiver-owned
            dependency bundle.
        analytics_config: Caller-constructed Analytics bounds and policy.
        engine_type: Expected backtest execution engine type.
        engine_version: Expected engine implementation version.
        state_store: Optional Optimization state port used to read persisted
            results. When omitted the result-read route fails closed.

    Returns:
        Opaque bundle accepted by Optimization public run operations.
    """
    adapter = build_simulation_analytics_backtest_adapter(
        auth_context=auth_context,
        simulation_dependencies=simulation_dependencies,
        analytics_config=analytics_config,
        engine_type=engine_type,
        engine_version=engine_version,
    )
    return {
        "adapter": adapter,
        "auth_context": auth_context,
        "state_store": state_store,
    }


def build_optimization_source(bundle: object | None) -> _OptimizationOperation:
    """Build one Optimization route operation dispatcher.

    The dispatcher validates each API DTO through the Optimization value
    factory and delegates exactly once to the matching Optimization public
    function. When no dependency bundle has been composed it raises a
    deterministic sentinel error that the route layer translates to HTTP 503.

    Args:
        bundle: Complete opaque Optimization dependency bundle, or ``None``
            when the canonical application has not composed an Optimization
            dependency bundle.

    Returns:
        Route operation dispatcher bound to the composed bundle.
    """
    fields_adapter = _FieldsAdapter(bundle)
    handlers = _build_handlers(fields_adapter)

    def _operation(operation: str, *args: object) -> object:
        """Validate API inputs and delegate once to Optimization functions.

        Args:
            operation: Canonical Optimization route operation name.
            *args: Operation-specific positional inputs.

        Returns:
            Optimization-owned standard response envelope.

        Raises:
            RuntimeError: If the Optimization dependency bundle is unavailable.
            ValueError: If the requested operation is not registered.
        """
        fields_adapter.require_available()
        handler = handlers.get(operation)
        if handler is None:
            raise ValueError("unsupported Optimization operation")
        return handler(args)

    return _operation


class _FieldsAdapter:
    """Bundle-bound helper exposing the adapter, store, and value factory."""

    __slots__ = ("_bundle",)

    def __init__(self, bundle: object | None) -> None:
        """Bind the composed Optimization dependency bundle.

        Args:
            bundle: Opaque Optimization dependency bundle or ``None``.
        """
        self._bundle = bundle

    def require_available(self) -> None:
        """Fail closed when no dependency bundle has been composed.

        Raises:
            RuntimeError: If the Optimization dependency bundle is unavailable.
        """
        if self._bundle is None:
            raise RuntimeError("OPTIMIZATION_RUNTIME_UNAVAILABLE")

    def adapter(self) -> object:
        """Return the composed backtest execution adapter.

        Returns:
            Adapter value bound to the composed dependency bundle.
        """
        return cast("dict[str, object]", self._bundle)["adapter"]

    def state_store(self) -> object | None:
        """Return the optional persisted-result state port.

        Returns:
            State store value or ``None`` when no store was composed.
        """
        return cast("dict[str, object]", self._bundle)["state_store"]

    def value(self, name: str, payload: object) -> object:
        """Reconstruct one Optimization value from a validated API payload.

        Args:
            name: Registered Optimization value contract name.
            payload: Boundary DTO or serialized mapping.

        Returns:
            Validated opaque Optimization value.
        """
        return create_optimization_value(name, **self._dump(payload))

    @staticmethod
    def _dump(payload: object) -> Mapping[str, object]:
        """Normalize a boundary DTO or mapping into JSON-safe fields.

        Args:
            payload: Boundary DTO (Pydantic model) or serialized mapping.

        Returns:
            Field mapping accepted by the Optimization value factory.
        """
        if hasattr(payload, "model_dump"):
            dumped = cast("Any", payload).model_dump(mode="python", warnings=False)
            return cast("Mapping[str, object]", dumped)
        return cast("Mapping[str, object]", payload)


def _build_handlers(adapter: _FieldsAdapter) -> Mapping[str, _Handler]:
    """Build the immutable operation-name to handler dispatch table.

    Args:
        adapter: Bundle-bound helper for value reconstruction and adapter access.

    Returns:
        Mapping of canonical operation name to its single-delegation handler.
    """
    return {
        "compare": lambda args: compare_optimization_runs(cast("Any", args[0])),
        "handoff": lambda args: build_optimization_handoff(
            cast("Any", adapter.value("EvidenceAssemblyRequest", args[0]))
        ),
        "overfit": lambda args: detect_overfit_parameters(
            cast("Any", args[0]),
            cast("Any", args[1]),
            threshold=cast("float", args[2]),
        ),
        "parameter-sweep": lambda args: run_parameter_sweep(
            cast("Any", adapter.value("SearchRequest", args[0])),
            cast("Any", adapter.adapter()),
        ),
        "rank": lambda args: rank_parameter_sets(cast("Any", args[0])),
        "read": lambda args: _read_result(adapter, args),
        "robustness": lambda args: run_robustness_analysis(
            cast("Any", _robustness_request(adapter, cast("Any", args[0]))),
            max_simulations=cast("int", args[1]),
        ),
        "robustness-score": lambda args: calculate_robustness_score(
            cast("Any", args[0])
        ),
        "stability": lambda args: calculate_parameter_stability(cast("Any", args[0])),
        "walk-forward": lambda args: run_walk_forward_optimization(
            cast("Any", adapter.value("WalkForwardRequest", args[0])),
            cast("Any", adapter.adapter()),
        ),
        "walk-forward-matrix": lambda args: run_walk_forward_matrix(
            cast("Any", _matrix_requests(adapter, cast("Any", args[0]))),
            cast("Any", adapter.adapter()),
            max_requests=cast("int", args[1]),
        ),
    }


def _read_result(adapter: _FieldsAdapter, args: tuple[object, ...]) -> object:
    """Delegate one persisted-result read to the Optimization public function.

    Args:
        adapter: Bundle-bound helper exposing the optional state port.
        args: ``(search_id, reproducibility_hash)`` positional inputs.

    Returns:
        Optimization-owned canonical result or ``None`` when absent.

    Raises:
        RuntimeError: If no state store has been composed.
    """
    store = adapter.state_store()
    if store is None:
        raise RuntimeError("OPTIMIZATION_RESULTS_UNAVAILABLE")
    return load_optimization_result(
        search_id=cast("str", args[0]),
        reproducibility_hash=cast("str", args[1]),
        store=cast("Any", store),
    )


def _matrix_requests(
    adapter: _FieldsAdapter, payload: Sequence[object]
) -> tuple[object, ...]:
    """Reconstruct a sequence of walk-forward requests.

    Args:
        adapter: Bundle-bound helper for value reconstruction.
        payload: Sequence of boundary DTOs or serialized mappings.

    Returns:
        Tuple of validated ``WalkForwardRequest`` values.
    """
    return tuple(adapter.value("WalkForwardRequest", item) for item in payload)


def _robustness_request(
    adapter: _FieldsAdapter, payload: Mapping[str, object]
) -> object:
    """Reconstruct one robustness request of the correct variant.

    The Optimization robustness contract is a discriminated union of
    ``MonteCarloRequest`` and ``ExecutionStressAnalysisRequest``. The presence
    of the ``stress`` field selects the stress variant; otherwise the
    Monte-Carlo variant is reconstructed.

    Args:
        adapter: Bundle-bound helper for value reconstruction.
        payload: Serialized robustness request mapping.

    Returns:
        Validated robustness request value.
    """
    fields = dict(payload)
    if "stress" in fields:
        return adapter.value("ExecutionStressAnalysisRequest", fields)
    return adapter.value("MonteCarloRequest", fields)


__all__ = ("build_api_optimization_dependencies", "build_optimization_source")
