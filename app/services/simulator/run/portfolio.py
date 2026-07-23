"""Deterministic all-or-nothing portfolio candidate simulation."""

from __future__ import annotations

from decimal import Decimal
from hashlib import sha256
from typing import TYPE_CHECKING

from app.services.simulator.accounting import validate_fx_evidence
from app.services.simulator.errors import SimulationError
from app.services.simulator.journal import JournalWriter
from app.services.simulator.reporting import (
    ComponentReturnSeries,
    PortfolioComponentResult,
    PortfolioSimulationResult,
    ReturnObservation,
    RiskBudgetHistoryRow,
    build_artifact_manifest,
)
from app.services.simulator.run.orchestrator import (
    _canonical_hash,
    _write_completed_text,
    run_backtest,
)
from app.utils import AuthContext, canonical_json, logger

if TYPE_CHECKING:
    from datetime import datetime

    from app.services.simulator.reporting import SimulationResult
    from app.services.simulator.run.contracts import (
        PortfolioBacktestRequestV1,
        SimulationRunDependencies,
    )

_MINIMUM_COMMON_OBSERVATIONS = 30
_ENGINE_VERSION = "simulation-engine-v1"


def _measurement_grid(
    start: datetime,
    end: datetime,
    count: int,
) -> tuple[datetime, ...]:
    """Build one fixed UTC cadence shared by every component.

    Args:
        start: Inclusive measurement window start.
        end: Inclusive measurement window end.
        count: Number of observations to place on the grid.

    Returns:
        Ordered unique UTC timestamps inside the window.

    Raises:
        SimulationError: If the window cannot carry the required cadence.
    """
    logger.debug("Building the Simulation portfolio measurement grid")
    span = end - start
    if span.total_seconds() <= 0 or count < _MINIMUM_COMMON_OBSERVATIONS:
        raise SimulationError(
            "SIM_AGGREGATE_UNRECONCILED",
            "Measurement window cannot carry the required return cadence",
        )
    grid = tuple(start + span * ((index + 1) / count) for index in range(count))
    if len(set(grid)) != count:
        raise SimulationError(
            "SIM_AGGREGATE_UNRECONCILED",
            "Measurement cadence produced duplicate timestamps",
        )
    return grid


def _component_return_series(
    component_id: str,
    result: SimulationResult,
    grid: tuple[datetime, ...],
    initial_balance: Decimal,
) -> ComponentReturnSeries:
    """Measure one component's periodic mark-to-market equity returns.

    The equity curve is reconstructed from the component's own closed-trade
    ledger, which is the only completed evidence the component published. Each
    observation is the period return of that curve on the shared cadence.

    Args:
        component_id: Ordered component identity.
        result: Completed component result.
        grid: Shared UTC measurement cadence.
        initial_balance: Component opening balance.

    Returns:
        Aligned immutable component return evidence.

    Raises:
        SimulationError: If the component cannot produce finite return evidence.
    """
    logger.info("Measuring component return series for %s", component_id)
    if initial_balance <= 0:
        raise SimulationError(
            "SIM_COMPONENT_INCOMPLETE", "Component initial balance is invalid"
        )
    observations: list[ReturnObservation] = []
    previous_equity = initial_balance
    for timestamp in grid:
        realized = sum(
            (
                trade.profit + trade.commission + trade.swap
                for trade in result.closed_trades
                if trade.exit_time <= timestamp
            ),
            Decimal(0),
        )
        equity = initial_balance + realized
        if not equity.is_finite() or previous_equity <= 0:
            raise SimulationError(
                "SIM_COMPONENT_INCOMPLETE", "Component equity evidence is invalid"
            )
        observations.append(
            ReturnObservation(
                timestamp=timestamp,
                return_value=(equity - previous_equity) / previous_equity,
            )
        )
        previous_equity = equity
    return ComponentReturnSeries(
        component_id=component_id,
        simulation_result_id=result.run_id,
        observations=tuple(observations),
    )


def _validate_fx_lineage(
    request: PortfolioBacktestRequestV1,
    dependencies: SimulationRunDependencies,
) -> None:
    """Resolve and freshness-validate every referenced FX evidence identifier.

    Args:
        request: Portfolio candidate request.
        dependencies: Explicit composition supplying the FX seam.

    Raises:
        SimulationError: If evidence is missing, unresolvable, or stale.
    """
    logger.info("Validating portfolio FX lineage for %s", request.portfolio_id)
    if not request.fx_evidence_ids:
        return
    try:
        resolved = dependencies.resolve_fx_evidence(request.fx_evidence_ids)
    except SimulationError:
        raise
    except Exception as error:
        raise SimulationError(
            "SIM_FX_EVIDENCE_UNAVAILABLE", "FX evidence could not be resolved"
        ) from error
    for evidence_id in request.fx_evidence_ids:
        evidence = resolved.get(evidence_id)
        if evidence is None:
            raise SimulationError(
                "SIM_FX_EVIDENCE_UNAVAILABLE", "FX evidence is missing"
            )
        validate_fx_evidence(evidence, as_of=request.measurement_end)


def _reconcile(
    request: PortfolioBacktestRequestV1,
    results: tuple[SimulationResult, ...],
    aggregate_net_profit: Decimal,
) -> tuple[PortfolioComponentResult, ...]:
    """Reconcile aggregate evidence against the component evidence.

    Args:
        request: Portfolio candidate request.
        results: Ordered completed component results.
        aggregate_net_profit: Aggregate ledger net profit.

    Returns:
        Ordered reconciled component rows.

    Raises:
        SimulationError: If the aggregate does not reconcile exactly.
    """
    logger.info("Reconciling the portfolio aggregate for %s", request.portfolio_id)
    if len(results) != len(request.components):
        raise SimulationError(
            "SIM_COMPONENT_INCOMPLETE", "Portfolio components are incomplete"
        )
    component_net_total = sum(
        (result.accounting.net_profit for result in results), Decimal(0)
    )
    if aggregate_net_profit != component_net_total:
        raise SimulationError(
            "SIM_AGGREGATE_UNRECONCILED",
            "Aggregate net profit differs from the component total",
        )
    rows: list[PortfolioComponentResult] = []
    for component, result in zip(request.components, results, strict=True):
        reconciled = (
            result.status == "completed"
            and result.account_currency == request.base_currency
            and bool(result.journal_ref)
        )
        if not reconciled:
            raise SimulationError(
                "SIM_AGGREGATE_UNRECONCILED",
                "A component did not reconcile against the aggregate",
            )
        rows.append(
            PortfolioComponentResult(
                component_id=component.component_id,
                simulation_result_id=result.run_id,
                journal_ref=result.journal_ref,
                metrics_ref=component.metrics_ref,
                account_currency=result.account_currency,
                reconciled=reconciled,
            )
        )
    return tuple(rows)


def run_portfolio_backtest(
    request: PortfolioBacktestRequestV1,
    auth_context: AuthContext,
    dependencies: SimulationRunDependencies,
) -> PortfolioSimulationResult:
    """Execute every component and publish only a reconciled aggregate.

    Args:
        request: Self-contained receiver-owned portfolio projection.
        auth_context: Authenticated portfolio trace context.
        dependencies: Explicit run and persistence composition.

    Returns:
        Completed reconciled portfolio result.

    Raises:
        SimulationError: If any component or aggregate evidence fails.
    """
    logger.info("Starting portfolio Simulation %s", request.portfolio_id)
    if (
        request.request_id != auth_context.request_id
        or request.workflow_id != auth_context.workflow_id
        or request.correlation_id != auth_context.correlation_id
    ):
        raise SimulationError("SIM_INVALID_CONFIG", "Portfolio auth trace differs")
    _validate_fx_lineage(request, dependencies)
    results: list[SimulationResult] = []
    for component in request.components:
        child = component.backtest_request
        child_auth = auth_context.model_copy(
            update={
                "request_id": child.request_id,
                "workflow_id": child.workflow_id,
                "correlation_id": child.correlation_id,
            }
        )
        try:
            results.append(run_backtest(child, child_auth, dependencies))
        except SimulationError as error:
            raise SimulationError(
                "SIM_COMPONENT_INCOMPLETE",
                "A portfolio component did not complete",
                request_id=request.request_id,
            ) from error
    completed = tuple(results)
    aggregate_net_profit = sum(
        (result.accounting.net_profit for result in completed), Decimal(0)
    )
    component_results = _reconcile(request, completed, aggregate_net_profit)
    grid = _measurement_grid(
        request.measurement_start,
        request.measurement_end,
        _MINIMUM_COMMON_OBSERVATIONS,
    )
    return_series = tuple(
        _component_return_series(
            component.component_id,
            result,
            grid,
            component.backtest_request.initial_balance,
        )
        for component, result in zip(request.components, completed, strict=True)
    )
    budgets = tuple(
        RiskBudgetHistoryRow(
            risk_decision_id=component.risk_decision_id,
            component_id=component.component_id,
            effective_at=request.measurement_start,
            expires_at=request.measurement_end,
            approved_budget=component.risk_budget,
            currency=request.base_currency,
        )
        for component in request.components
    )
    request_hash = _canonical_hash(request.model_dump(mode="python", warnings=False))
    run_id = f"sim-portfolio-{request_hash[:24]}"
    data_hash = sha256(
        "".join(result.data_hash for result in completed).encode("ascii")
    ).hexdigest()
    result_hash = sha256(
        canonical_json(
            {
                "request_hash": request_hash,
                "components": tuple(result.run_id for result in completed),
                "aggregate_net_profit": aggregate_net_profit,
            }
        ).encode("utf-8")
    ).hexdigest()
    result = PortfolioSimulationResult(
        result_id=f"portfolio-result-{result_hash[:24]}",
        run_id=run_id,
        request_hash=request_hash,
        config_hash=request.config_hash,
        data_hash=data_hash,
        result_hash=result_hash,
        engine_version=_ENGINE_VERSION,
        status="completed",
        portfolio_id=request.portfolio_id,
        construction_result_id=request.construction_result_id,
        construction_version=request.construction_version,
        measurement_start=request.measurement_start,
        measurement_end=request.measurement_end,
        base_currency=request.base_currency,
        component_results=component_results,
        component_return_series=return_series,
        aggregate_journal_ref=f"{run_id}/journal.jsonl",
        aggregate_metrics_ref=f"{run_id}/metrics.json",
        risk_budget_history=budgets,
        fx_evidence_ids=request.fx_evidence_ids,
        artifact_manifest_ref=f"{run_id}/manifest.json",
    )
    run_root = dependencies.artifact_root.resolve() / run_id
    journal_path = run_root / "journal.jsonl"
    result_path = run_root / "result.json"
    report_path = run_root / "report.md"
    writer = JournalWriter(
        dependencies.state_store,
        run_id,
        request.request_id,
        request.correlation_id,
    )
    writer.append(
        "run_started",
        {
            "config_hash": request.config_hash,
            "data_hash": data_hash,
            "engine_version": _ENGINE_VERSION,
        },
        request.measurement_start,
    )
    writer.append(
        "portfolio_completed",
        {
            "component_run_ids": tuple(item.run_id for item in completed),
            "aggregate_net_profit": aggregate_net_profit,
        },
        request.measurement_end,
    )
    writer.finalize()
    _write_completed_text(
        result_path,
        canonical_json(
            result.model_dump(mode="python", warnings=False), max_items=None
        ),
    )
    _write_completed_text(
        report_path,
        "# Portfolio Simulation Report\n\n"
        f"Components: {len(completed)}\n\n"
        f"Aggregate net profit: {aggregate_net_profit} {request.base_currency}\n\n"
        "Status: completed\n",
    )
    _write_completed_text(
        run_root / "metrics.json",
        canonical_json(
            {
                "aggregate_net_profit": aggregate_net_profit,
                "component_net_profit": {
                    row.component_id: item.accounting.net_profit
                    for row, item in zip(component_results, completed, strict=True)
                },
            }
        ),
    )
    manifest = build_artifact_manifest(
        run_root,
        (journal_path, result_path, report_path),
        created_at=request.measurement_end,
    )
    _write_completed_text(
        run_root / "manifest.json",
        canonical_json(
            manifest.model_dump(mode="python", warnings=False), max_items=None
        ),
    )
    return result


__all__ = ["run_portfolio_backtest"]
