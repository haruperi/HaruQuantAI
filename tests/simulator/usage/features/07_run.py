"""Executable Simulation run usage example.

Demonstrates FEAT-SIM-07 running official backtests, portfolio backtests, fast research, and governed AuditEvent persistence.
"""

from __future__ import annotations

import sys
import tempfile
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.simulator import (
    calculate_portfolio_backtest_config_hash,
    calculate_simulation_backtest_config_hash,
    create_simulation_value,
    run_backtest,
    run_fast_research,
    run_portfolio_backtest,
    unwrap_simulation_response,
)
from app.utils import canonical_digest, create_auth_context, generate_id
from tests.simulator.usage.workflows._support import (
    authority,
    dependencies,
    fx_evidence,
    live_tick_dataset,
)


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


def _build_request(
    dataset: object,
    runtime_profile: str = "simulation",
    canonical: bool = True,
) -> object:
    """Build a valid backtest request with valid UUID trace IDs."""
    req_id = generate_id("req")
    wf_id = generate_id("wf")
    cor_id = generate_id("cor")
    start = dataset.start
    end = dataset.end

    payload: dict[str, object] = {
        "request_id": req_id,
        "workflow_id": wf_id,
        "correlation_id": cor_id,
        "strategy_id": "strategy-1",
        "strategy_version": "v1",
        "strategy_config_ref": "strategy-config",
        "strategy_config_hash": "a" * 64,
        "data_ref": "dataset",
        "data_version": "v1",
        "data_hash": canonical_digest(
            dataset.model_dump(mode="python", warnings=False)
        ),
        "tick_generation_ref": "tick-profile",
        "tick_generation_version": "v1",
        "tick_generation_hash": "b" * 64,
        "execution_profile_ref": "execution-profile",
        "execution_profile_version": "v1",
        "execution_profile_hash": "c" * 64,
        "risk_policy_ref": "risk-policy",
        "risk_policy_version": "v1",
        "risk_policy_hash": "d" * 64,
        "symbol": "EURUSD",
        "timeframe": "M1",
        "start": start,
        "end": end,
        "parameters": {"period": 14},
        "initial_balance": Decimal(10_000),
        "account_currency": "USD",
        "asset_class": "FX",
        "seed": 7,
        "runtime_profile": runtime_profile,
        "execution_route": "sim",
        "canonical": canonical,
    }
    payload["config_hash"] = unwrap_simulation_response(
        calculate_simulation_backtest_config_hash(payload),
        operation="simulation.run.simulation_backtest_request_v1.calculate_config_hash",
    )
    return create_simulation_value("SimulationBacktestRequestV1", **payload)


def _build_portfolio_request(
    dataset: object,
) -> tuple[object, object]:
    """Build a valid portfolio backtest request and authority with valid trace IDs."""
    child_req = _build_request(dataset)
    component = create_simulation_value(
        "PortfolioComponentRequest",
        component_id="component-1",
        capital_weight=Decimal(1),
        risk_budget=Decimal(100),
        risk_decision_id="risk-1",
        metrics_ref="metrics-1",
        backtest_request=child_req,
    )
    req_id = generate_id("req")
    wf_id = generate_id("wf")
    cor_id = generate_id("cor")
    start = dataset.start
    conversion_evidence = fx_evidence(dataset)

    payload: dict[str, object] = {
        "request_id": req_id,
        "workflow_id": wf_id,
        "correlation_id": cor_id,
        "portfolio_id": "portfolio",
        "construction_result_id": "construction",
        "construction_version": "v1",
        "components": (component.model_dump(mode="python", warnings=False),),
        "measurement_start": start,
        "measurement_end": start + timedelta(days=30),
        "base_currency": "USD",
        "fx_evidence_ids": ("fx-1",),
        "fx_evidence_versions": (conversion_evidence.contract_version,),
        "fx_evidence_hashes": (
            canonical_digest(
                conversion_evidence.model_dump(mode="python", warnings=False)
            ),
        ),
        "execution_profile_version": "v1",
        "risk_policy_version": "v1",
        "seed": 7,
        "initial_balance": Decimal(10_000),
        "runtime_profile": "simulation",
        "execution_route": "sim",
    }
    payload["config_hash"] = unwrap_simulation_response(
        calculate_portfolio_backtest_config_hash(payload),
        operation="simulation.run.portfolio_backtest_request_v1.calculate_config_hash",
    )
    port_req = create_simulation_value("PortfolioBacktestRequestV1", **payload)

    auth = create_auth_context(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="simulator-test",
        principal_type="SERVICE_ACCOUNT",
        roles=("builder",),
        permissions=("simulation:run",),
        scopes=("simulation:run",),
        tenant_or_environment="test",
        request_id=req_id,
        workflow_id=wf_id,
        correlation_id=cor_id,
        issued_at=start - timedelta(days=1),
    )
    return port_req, auth


def fr_sim_029() -> None:
    """
    FR-SIM-029: Stage 1 — Construct SimulationBacktestRequestV1 request envelope.

    The system shall expose the exact `docs/PROJECT.md` §5 request for one synchronous bounded FX run, with separate contract version/schema ID, immutable Strategy/Data/Simulation/Risk references, JSON-safe parameters, symbol/timeframe/UTC range, positive initial balance, trace IDs, simulation profile/route, config hash, and no raw code/provider objects/inline data.
    """
    _header("Stage 1: Request Envelope - SimulationBacktestRequestV1 (FR-SIM-029)")
    request = _build_request(live_tick_dataset())
    print(_format_result(request))
    print(
        f"Data -> symbol='{request.symbol}', initial_balance={request.initial_balance}"
    )


def fr_sim_032() -> None:
    """FR-SIM-032: Stage 1 — Construct PortfolioBacktestRequestV1 request envelope.

    The system shall expose `PortfolioBacktestRequestV1` with
    `contract_version="v1"`, `schema_id="simulation.portfolio_backtest_request.v1"`,
    portfolio and construction-result identifiers and versions, ordered component
    allocations, exact Strategy/Data/FX/execution/Risk references and versions,
    bounded UTC range, explicit seed, positive initial balance,
    `runtime_profile="simulation"`, `execution_route="sim"`, and a SHA-256 config
    hash. Every FX evidence ID is positionally bound to an explicit `v1`
    compatibility version and lowercase canonical SHA-256 evidence hash. Each child
    request's initial balance equals the portfolio balance multiplied by its exact
    capital weight and its account currency equals the portfolio base currency. It
    carries scalar values, identifiers, references, and hashes only, never embeds a
    Portfolio-owned contract type, and carries no caller-supplied measurement
    series.
    """
    _header("Stage 1: Portfolio Request - PortfolioBacktestRequestV1 (FR-SIM-032)")
    request, _ = _build_portfolio_request(live_tick_dataset())
    print(_format_result(request))
    print(
        f"Data -> portfolio_id='{request.portfolio_id}', base_currency='{request.base_currency}'"
    )


def fr_sim_030() -> None:
    """
    FR-SIM-030: Stage 3 — Orchestrate official synchronous backtest run.

    The system shall authenticate, deduplicate, validate, execute, journal, report, persist, and return one deterministic canonical FX run, never publishing a partial completed result. It persists bounded `simulation.run_started`, `simulation.run_completed`, `simulation.run_replayed`, or `simulation.run_failed` `AuditEvent v1` evidence through `SimulationRunDependencies.persist_audit_event`; unavailable audit persistence fails closed.
    """
    _header("Stage 3: Official Run - Orchestrate Synchronous Backtest (FR-SIM-030)")
    dataset = live_tick_dataset()
    request = _build_request(dataset)
    with tempfile.TemporaryDirectory() as tmp_dir:
        run_dependencies = dependencies(Path(tmp_dir), dataset)
        resp = run_backtest(request, authority(request), run_dependencies)
        result = unwrap_simulation_response(resp, operation="usage.run_backtest")
        print(_format_result(resp))
        print(f"Data -> run_status='{resp.status}', result_schema='{result.schema_id}'")


def fr_sim_034() -> None:
    """
    FR-SIM-034: Stage 3 — Orchestrate portfolio candidate backtest run.

    The system shall execute every component of an approved portfolio candidate through the ordinary deterministic simulation path, maintain one aggregate account ledger and the Risk-owned budget history, and publish `PortfolioSimulationResult v1` only when every component and the aggregate journal reconcile. Reconciliation is arithmetic and falsifiable: exact allocated opening capital equals portfolio opening capital, aggregate net profit equals the exact sum of component net profit, and aggregate component count equals the request. Component returns are sampled from each engine's actual end-of-tick mark-to-market equity observations on one shared 30-point UTC cadence; open-position price movement is included and closed-trade reconstruction is forbidden. Every resolved FX evidence object must match its request-bound version and canonical hash before freshness validation. The run persists bounded portfolio start/completion/failure audit evidence.
    """
    _header("Stage 3: Portfolio Run - Orchestrate Portfolio Backtest (FR-SIM-034)")
    dataset = live_tick_dataset()
    request, auth = _build_portfolio_request(dataset)
    with tempfile.TemporaryDirectory() as tmp_dir:
        run_dependencies = dependencies(Path(tmp_dir), dataset)
        resp = run_portfolio_backtest(request, auth, run_dependencies)
        unwrap_simulation_response(resp, operation="usage.run_portfolio_backtest")
        print(_format_result(resp))
        print(f"Data -> portfolio_run_status='{resp.status}'")


def fr_sim_031() -> None:
    """
    FR-SIM-031: Stage 3 — Execute fast research mode approximation.

    The system shall run an explicitly requested approximation only when enabled, mark every output `canonical=false`, disclose assumptions, prohibit canonical fills, promotion evidence, and reports, and persist bounded research start/completion/failure audit evidence.
    """
    _header("Stage 3: Fast Research - Execute Fast Research Path (FR-SIM-031)")
    dataset = live_tick_dataset()
    request = _build_request(
        dataset,
        runtime_profile="fast_research",
        canonical=False,
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        run_dependencies = dependencies(Path(tmp_dir), dataset)
        resp = run_fast_research(request, authority(request), run_dependencies)
        result = unwrap_simulation_response(resp, operation="usage.run_fast_research")
        print(_format_result(resp))
        print(f"Data -> canonical={result.canonical}")


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-SIM-07 — run/ — Official and Research Orchestration\n\n"
        "Purpose: Orchestrate official synchronous backtests, portfolio backtests, fast research approximations, and governed AuditEvent persistence.\n\n"
        "Module flow:\n"
        "-> Stage 1: Request payload construction and config hash computation\n"
        "-> Stage 2: Authentication, deduplication, and dependency resolution\n"
        "-> Stage 3: Official backtest, portfolio backtest, and fast research execution with audit logging"
    )

    # Stage 1: Request construction
    fr_sim_029()
    fr_sim_032()

    # Stage 3: Backtest & research orchestration
    fr_sim_030()
    fr_sim_034()
    fr_sim_031()


if __name__ == "__main__":
    main()
