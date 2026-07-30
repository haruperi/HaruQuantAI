"""Concrete Simulation/Analytics adapter and compatibility gate."""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable, Mapping
from decimal import Decimal
from typing import Any, cast

from app.services.analytics import (
    build_performance_report,
    is_analytics_value,
)
from app.services.optimization.errors import OptimizationError
from app.services.optimization.execution.contracts import (
    BacktestExecutionAdapter,
    BacktestExecutionRequest,
    EngineOptimizationResult,
)
from app.services.simulator import (
    calculate_simulation_backtest_config_hash,
    create_simulation_value,
    dump_simulation_value,
    get_simulation_value_field,
    is_simulation_value,
    run_backtest,
)
from app.utils import get_logger, get_standard_response_type

type AuthContext = Any
type StandardResponse[T] = Any
AnalyticsRunConfig = Any
PerformanceReport = Any
SimulationRunDependencies = Any

logger = get_logger(__name__)

type SimulationRunner = Callable[
    [object, AuthContext, SimulationRunDependencies],
    object,
]


def _unwrap_upstream_response(
    value: object,
    *,
    predicate: Callable[[object], bool],
    operation: str,
    candidate_hash: str,
) -> object:
    """Unwrap one upstream response while preserving safe failure evidence.

    Args:
        value: Raw or shared-response upstream value.
        predicate: Public producer-owned payload predicate.
        operation: Qualified upstream operation name.
        candidate_hash: Optimization candidate identity.

    Returns:
        The raw producer-owned payload.

    Raises:
        OptimizationError: If the upstream operation failed or returned an
            incompatible payload.
    """
    if isinstance(value, get_standard_response_type()):
        response = cast("Any", value)
        if response.status != "success" or response.data is None:
            upstream_code = (
                response.error.code
                if response.error is not None
                else "INVALID_RESPONSE"
            )
            raise OptimizationError(
                "OPT_EXECUTION_FAILED",
                "UPSTREAM_OPERATION_FAILED",
                safe_details={
                    "candidate_hash": candidate_hash,
                    "upstream_domain": response.metadata.domain,
                    "upstream_code": upstream_code,
                },
            )
        value = response.data
    if not predicate(value):
        raise OptimizationError(
            "OPT_EXECUTION_FAILED",
            "UPSTREAM_RESPONSE_INVALID",
            safe_details={
                "candidate_hash": candidate_hash,
                "operation": operation,
                "upstream_type": type(value).__name__,
            },
        )
    return value


def _simulation_source(
    result: object, request: BacktestExecutionRequest
) -> Mapping[str, object]:
    """Project a completed Simulation result to Analytics ledger input.

    Args:
        result: Completed Simulation result.
        request: Source Optimization execution request.

    Returns:
        Producer-neutral Analytics source mapping.
    """
    logger.debug("Projecting Simulation result to Analytics source evidence")
    context = request.context
    return {
        "contract_version": get_simulation_value_field(result, "contract_version"),
        "schema_id": get_simulation_value_field(result, "schema_id"),
        "source_id": get_simulation_value_field(result, "run_id"),
        "phase": "simulation",
        "window_start": context.start,
        "window_end": context.end,
        "strategy_id": context.strategy_id,
        "strategy_version": context.strategy_version,
        "symbols": (context.symbol,),
        "timeframe": context.timeframe,
        "closed_trades": tuple(
            dump_simulation_value(row)
            for row in cast(
                "Iterable[object]",
                get_simulation_value_field(result, "closed_trades"),
            )
        ),
        "quality_metadata": {
            "diagnostics": get_simulation_value_field(result, "diagnostics")
        },
        "source_metadata": {
            "simulation_request_hash": get_simulation_value_field(
                result, "request_hash"
            ),
            "candidate_hash": request.candidate_hash,
        },
    }


class SimulationAnalyticsBacktestAdapter:
    """Optimization-owned composition of public Simulation and Analytics APIs."""

    contract_version = "v1"
    schema_id = "optimization.backtest_execution_adapter.v1"
    deterministic = True

    def __init__(
        self,
        *,
        auth_context: AuthContext,
        simulation_dependencies: SimulationRunDependencies,
        analytics_config: AnalyticsRunConfig,
        engine_type: str,
        engine_version: str,
        simulation_runner: SimulationRunner = run_backtest,
    ) -> None:
        """Initialize the injected public-contract adapter.

        Args:
            auth_context: Shared authenticated principal context.
            simulation_dependencies: Simulation-owned run dependencies.
            analytics_config: Caller-constructed Analytics bounds and policy.
            engine_type: Expected engine type.
            engine_version: Expected engine version.
            simulation_runner: Injectable official Simulation operation.
        """
        logger.info("Initializing Optimization Simulation/Analytics adapter")
        self._auth_context = auth_context
        self._simulation_dependencies = simulation_dependencies
        self._analytics_config = analytics_config
        self._simulation_runner = simulation_runner
        self.engine_type = engine_type
        self.engine_version = engine_version

    def execute(self, request: BacktestExecutionRequest) -> EngineOptimizationResult:
        """Package, execute, and measure one deterministic candidate.

        Args:
            request: Complete candidate execution request.

        Returns:
            Optimization-facing Simulation and Analytics evidence.

        Raises:
            OptimizationError: If Simulation or Analytics rejects the candidate.
        """
        logger.info("Executing Optimization candidate through public domain contracts")
        context = request.context
        payload: dict[str, object] = {
            "request_id": request.request_id,
            "workflow_id": request.workflow_id,
            "correlation_id": request.correlation_id,
            "strategy_id": context.strategy_id,
            "strategy_version": context.strategy_version,
            "strategy_config_ref": context.strategy_config_ref,
            "strategy_config_hash": context.strategy_config_hash,
            "data_ref": context.data_ref,
            "data_version": context.data_version,
            "data_hash": context.data_hash,
            "tick_generation_ref": context.tick_generation_ref,
            "tick_generation_version": context.tick_generation_version,
            "tick_generation_hash": context.tick_generation_hash,
            "execution_profile_ref": context.execution_profile_ref,
            "execution_profile_version": context.execution_profile_version,
            "execution_profile_hash": context.execution_profile_hash,
            "risk_policy_ref": context.risk_policy_ref,
            "risk_policy_version": context.risk_policy_version,
            "risk_policy_hash": context.risk_policy_hash,
            "symbol": context.symbol,
            "timeframe": context.timeframe,
            "start": context.start,
            "end": context.end,
            "parameters": request.executable_parameters,
            "initial_balance": context.initial_balance,
            "account_currency": context.account_currency,
            "asset_class": "FX",
            "seed": request.seed,
            "runtime_profile": context.runtime_profile,
            "execution_route": "sim",
            "canonical": context.canonical,
        }
        payload["config_hash"] = str(
            _unwrap_upstream_response(
                calculate_simulation_backtest_config_hash(payload),
                predicate=lambda value: isinstance(value, str),
                operation="simulation.run.simulation_backtest_request_v1.calculate_config_hash",
                candidate_hash=request.candidate_hash,
            )
        )
        started = time.monotonic()
        try:
            simulation_request = create_simulation_value(
                "SimulationBacktestRequestV1", **payload
            )
            candidate_auth = self._auth_context.model_copy(
                update={
                    "request_id": request.request_id,
                    "workflow_id": request.workflow_id,
                    "correlation_id": request.correlation_id,
                }
            )
            simulation_result: object = _unwrap_upstream_response(
                self._simulation_runner(
                    simulation_request,
                    candidate_auth,
                    self._simulation_dependencies,
                ),
                predicate=lambda value: is_simulation_value(value, "SimulationResult"),
                operation="simulation.run_backtest",
                candidate_hash=request.candidate_hash,
            )
            report: PerformanceReport = _unwrap_upstream_response(
                build_performance_report(
                    _simulation_source(simulation_result, request),
                    source_contract="simulation.result",
                    request_id=request.request_id,
                    correlation_id=request.correlation_id,
                    created_at=context.end,
                    initial_balance=cast(
                        "Decimal",
                        get_simulation_value_field(
                            simulation_result, "initial_balance"
                        ),
                    ),
                    account_currency=str(
                        get_simulation_value_field(
                            simulation_result, "account_currency"
                        )
                    ),
                    config=self._analytics_config,
                ),
                predicate=lambda value: is_analytics_value(value, "PerformanceReport"),
                operation="analytics.build_performance_report",
                candidate_hash=request.candidate_hash,
            )
        except ValueError as error:
            raise OptimizationError(
                "OPT_EXECUTION_FAILED",
                "CANDIDATE_EXECUTION_REJECTED",
                safe_details={"candidate_hash": request.candidate_hash},
            ) from error
        runtime_ms = (time.monotonic() - started) * 1000
        return EngineOptimizationResult(
            candidate_hash=request.candidate_hash,
            simulation_run_id=str(
                get_simulation_value_field(simulation_result, "run_id")
            ),
            simulation_request_hash=str(
                get_simulation_value_field(simulation_result, "request_hash")
            ),
            analytics_report=report,
            runtime_ms=runtime_ms,
            engine_type=self.engine_type,
            engine_version=self.engine_version,
        )


def execute_candidate(
    request: BacktestExecutionRequest,
    adapter: BacktestExecutionAdapter,
    *,
    deterministic_only: bool,
) -> EngineOptimizationResult:
    """Validate adapter compatibility and execute one candidate.

    Args:
        request: Candidate execution request.
        adapter: Injected Optimization execution adapter.
        deterministic_only: Whether non-deterministic adapters are forbidden.

    Returns:
        Completed measured candidate result.

    Raises:
        OptimizationError: If adapter compatibility or result identity fails.
    """
    logger.info("Validating and invoking Optimization execution adapter")
    context = request.context
    if (
        adapter.contract_version != request.contract_version
        or adapter.engine_type != context.engine_type
        or adapter.engine_version != context.engine_version
        or (deterministic_only and not adapter.deterministic)
    ):
        raise OptimizationError(
            "OPT_ADAPTER_INCOMPATIBLE",
            "EXECUTION_CONTRACT_MISMATCH",
        )
    result = adapter.execute(request)
    if (
        result.candidate_hash != request.candidate_hash
        or result.engine_type != context.engine_type
        or result.engine_version != context.engine_version
    ):
        raise OptimizationError(
            "OPT_ADAPTER_INCOMPATIBLE",
            "EXECUTION_RESULT_MISMATCH",
        )
    return result


__all__ = ["SimulationAnalyticsBacktestAdapter", "execute_candidate"]
