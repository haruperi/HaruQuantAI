"""Concrete Simulation/Analytics adapter and compatibility gate."""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping

from app.services.analytics import (
    AnalyticsRunConfig,
    build_performance_report,
)
from app.services.optimization.errors import OptimizationError
from app.services.optimization.execution.contracts import (
    BacktestExecutionAdapter,
    BacktestExecutionRequest,
    EngineOptimizationResult,
)
from app.services.simulator import (
    SimulationBacktestRequestV1,
    SimulationError,
    SimulationResult,
    SimulationRunDependencies,
    run_backtest,
)
from app.utils import AuthContext, logger

type SimulationRunner = Callable[
    [SimulationBacktestRequestV1, AuthContext, SimulationRunDependencies],
    SimulationResult,
]


def _simulation_source(
    result: SimulationResult, request: BacktestExecutionRequest
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
        "contract_version": result.contract_version,
        "schema_id": result.schema_id,
        "source_id": result.run_id,
        "phase": "simulation",
        "window_start": context.start,
        "window_end": context.end,
        "strategy_id": context.strategy_id,
        "strategy_version": context.strategy_version,
        "symbols": (context.symbol,),
        "timeframe": context.timeframe,
        "closed_trades": tuple(
            row.model_dump(mode="python") for row in result.closed_trades
        ),
        "quality_metadata": {"diagnostics": result.diagnostics},
        "source_metadata": {
            "simulation_request_hash": result.request_hash,
            "candidate_hash": request.candidate_hash,
        },
    }


class SimulationAnalyticsBacktestAdapter:
    """Optimization-owned composition of public Simulation and Analytics APIs."""

    contract_version = "v1"
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
        payload["config_hash"] = SimulationBacktestRequestV1.calculate_config_hash(
            payload
        )
        started = time.monotonic()
        try:
            simulation_request = SimulationBacktestRequestV1.model_validate(payload)
            candidate_auth = self._auth_context.model_copy(
                update={
                    "request_id": request.request_id,
                    "workflow_id": request.workflow_id,
                    "correlation_id": request.correlation_id,
                }
            )
            simulation_result = self._simulation_runner(
                simulation_request,
                candidate_auth,
                self._simulation_dependencies,
            )
            report = build_performance_report(
                _simulation_source(simulation_result, request),
                source_contract="simulation.result",
                request_id=request.request_id,
                initial_balance=simulation_result.initial_balance,
                account_currency=simulation_result.account_currency,
                config=self._analytics_config,
            )
        except (SimulationError, ValueError) as error:
            raise OptimizationError(
                "OPT_EXECUTION_FAILED",
                "CANDIDATE_EXECUTION_REJECTED",
                safe_details={"candidate_hash": request.candidate_hash},
            ) from error
        runtime_ms = (time.monotonic() - started) * 1000
        return EngineOptimizationResult(
            candidate_hash=request.candidate_hash,
            simulation_run_id=simulation_result.run_id,
            simulation_request_hash=simulation_result.request_hash,
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
