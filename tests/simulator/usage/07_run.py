"""Executable Simulation run usage example.

Demonstrates running backtests, fast research, and portfolio backtests.
"""

import sys
import tempfile
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

# Add repository root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.simulator import (
    PortfolioBacktestRequestV1,
    PortfolioComponentRequest,
    SimulationBacktestRequestV1,
    run_backtest,
    run_fast_research,
    run_portfolio_backtest,
    unwrap_simulation_response,
)
from app.utils import AuthContext, canonical_digest, generate_id
from tests.simulator.unit.test_orchestrator import (
    FakeDependencies,
    _auth,
    _data_hash,
    _dataset,
    _fx_evidence,
)


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _build_request(
    dataset: object,
    runtime_profile: str = "simulation",
    canonical: bool = True,
) -> SimulationBacktestRequestV1:
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
        "data_hash": _data_hash(dataset),  # type: ignore[arg-type]
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
        SimulationBacktestRequestV1.calculate_config_hash(payload),
        operation="simulation.run.simulation_backtest_request_v1.calculate_config_hash",
    )
    return SimulationBacktestRequestV1.model_validate(payload)


def _build_portfolio_request(
    dataset: object,
) -> tuple[PortfolioBacktestRequestV1, AuthContext]:
    """Build a valid portfolio backtest request and authority with valid trace IDs."""
    child_req = _build_request(dataset)
    component = PortfolioComponentRequest(
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
    fx_evidence = _fx_evidence(dataset)  # type: ignore[arg-type]

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
        "fx_evidence_versions": (fx_evidence.contract_version,),
        "fx_evidence_hashes": (
            canonical_digest(fx_evidence.model_dump(mode="python", warnings=False)),
        ),
        "execution_profile_version": "v1",
        "risk_policy_version": "v1",
        "seed": 7,
        "initial_balance": Decimal(10_000),
        "runtime_profile": "simulation",
        "execution_route": "sim",
    }
    payload["config_hash"] = unwrap_simulation_response(
        PortfolioBacktestRequestV1.calculate_config_hash(payload),
        operation="simulation.run.portfolio_backtest_request_v1.calculate_config_hash",
    )
    port_req = PortfolioBacktestRequestV1.model_validate(payload)

    auth = AuthContext(
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


def example_run() -> None:
    """Demonstrate backtest, fast research, and portfolio backtest execution."""
    _header("Demonstrate backtest, fast research, and portfolio backtest execution.")
    print("Simulator Example 7: Backtest and Portfolio Orchestration")

    req_id = generate_id("req")
    dataset = _dataset(req_id)
    request = _build_request(dataset)

    print(f"Request type: {type(request).__name__}")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # 1. Run canonical backtest
        deps = FakeDependencies(tmp_path, dataset)  # type: ignore[arg-type]
        result = unwrap_simulation_response(
            run_backtest(request, _auth(request), deps), operation="usage.run_backtest"
        )
        print(f"Canonical backtest status: {result.status}")

        # 2. Run fast research
        fast_req_id = generate_id("req")
        fast_dataset = _dataset(fast_req_id)
        fast_request = _build_request(
            fast_dataset,
            runtime_profile="fast_research",
            canonical=False,
        )
        fast_deps = FakeDependencies(tmp_path, fast_dataset)  # type: ignore[arg-type]
        fast_result = unwrap_simulation_response(
            run_fast_research(fast_request, _auth(fast_request), fast_deps),
            operation="usage.run_fast_research",
        )
        print(f"Fast research canonical status: {fast_result.canonical}")

        # 3. Run portfolio backtest
        port_req_id = generate_id("req")
        port_dataset = _dataset(port_req_id)
        port_request, port_auth = _build_portfolio_request(port_dataset)
        port_deps = FakeDependencies(tmp_path, port_dataset)  # type: ignore[arg-type]
        port_result = unwrap_simulation_response(
            run_portfolio_backtest(port_request, port_auth, port_deps),
            operation="usage.run_portfolio_backtest",
        )
        print(f"Portfolio backtest status: {port_result.status}")


def fr_sim_029() -> None:
    """Demonstrate FR-SIM-029.

    Responsibility:
        The system shall expose the exact `docs/PROJECT.md` §5 request for one
        synchronous bounded FX run, with separate contract version/schema ID, immutable
        Strategy/Data/Simulation/Risk references, JSON-safe parameters,
        symbol/timeframe/UTC range, positive initial balance, trace IDs, simulation
        profile/route, config hash, and no raw code/provider objects/inline data.
    """
    _header(
        "Demonstrate FR-SIM-029. Responsibility: The system shall expose the exact `docs/PROJECT.md` §5 request for one synchronous bounded FX run, with separate contract version/schema ID, immutable Strategy/Data/Simulation/Risk references, JSON-safe parameters, symbol/timeframe/UTC range, positive initial balance, trace IDs, simulation profile/route, config hash, and no raw code/provider objects/inline data."
    )
    request_id = generate_id("req")
    request = _build_request(_dataset(request_id))
    print(f"Backtest request: {request.schema_id}")


def fr_sim_032() -> None:
    """Demonstrate FR-SIM-032.

    Responsibility:
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
    _header(
        "Demonstrate FR-SIM-032. Responsibility: The system shall expose `PortfolioBacktestRequestV1` with `contract_version='v1'`, `schema_id='simulation.portfolio_backtest_request.v1'`, portfolio and construction-result identifiers and versions, ordered component allocations, exact Strategy/Data/FX/execution/Risk references and versions, bounded UTC range, explicit seed, positive initial balance, `runtime_profile='simulation'`, `execution_route='sim'`, and a SHA-256 config hash. Every FX evidence ID is positionally bound to an explicit `v1` compatibility version and lowercase canonical SHA-256 evidence hash. Each child request's initial balance equals the portfolio balance multiplied by its exact capital weight and its account currency equals the portfolio base currency. It carries scalar values, identifiers, references, and hashes only, never embeds a Portfolio-owned contract type, and carries no caller-supplied measurement series."
    )
    request_id = generate_id("req")
    request, _ = _build_portfolio_request(_dataset(request_id))
    print(f"Portfolio request: {request.schema_id}")


def fr_sim_030() -> None:
    """Demonstrate FR-SIM-030.

    Responsibility:
        The system shall authenticate, deduplicate, validate, execute, journal, report,
        persist, and return one deterministic canonical FX run, never publishing a
        partial completed result. It persists bounded `simulation.run_started`,
        `simulation.run_completed`, `simulation.run_replayed`, or
        `simulation.run_failed` `AuditEvent v1` evidence through
        `SimulationRunDependencies.persist_audit_event`; unavailable audit persistence
        fails closed.
    """
    _header(
        "Demonstrate FR-SIM-030. Responsibility: The system shall authenticate, deduplicate, validate, execute, journal, report, persist, and return one deterministic canonical FX run, never publishing a partial completed result. It persists bounded `simulation.run_started`, `simulation.run_completed`, `simulation.run_replayed`, or `simulation.run_failed` `AuditEvent v1` evidence through `SimulationRunDependencies.persist_audit_event`; unavailable audit persistence fails closed."
    )
    request_id = generate_id("req")
    dataset = _dataset(request_id)
    request = _build_request(dataset)
    with tempfile.TemporaryDirectory() as tmp_dir:
        dependencies = FakeDependencies(Path(tmp_dir), dataset)
        result = unwrap_simulation_response(
            run_backtest(request, _auth(request), dependencies),
            operation="usage.run_backtest",
        )
        print(f"Canonical status: {result.status}")


def fr_sim_034() -> None:
    """Demonstrate FR-SIM-034.

    Responsibility:
        The system shall execute every component of an approved portfolio candidate
        through the ordinary deterministic simulation path, maintain one aggregate
        account ledger and the Risk-owned budget history, and publish
        `PortfolioSimulationResult v1` only when every component and the aggregate
        journal reconcile. Reconciliation is arithmetic and falsifiable: exact allocated
        opening capital equals portfolio opening capital, aggregate net profit equals
        the exact sum of component net profit, and aggregate component count equals the
        request. Component returns are sampled from each engine's actual end-of-tick
        mark-to-market equity observations on one shared 30-point UTC cadence;
        open-position price movement is included and closed-trade reconstruction is
        forbidden. Every resolved FX evidence object must match its request-bound
        version and canonical hash before freshness validation. The run persists bounded
        portfolio start/completion/failure audit evidence.
    """
    _header(
        "Demonstrate FR-SIM-034. Responsibility: The system shall execute every component of an approved portfolio candidate through the ordinary deterministic simulation path, maintain one aggregate account ledger and the Risk-owned budget history, and publish `PortfolioSimulationResult v1` only when every component and the aggregate journal reconcile. Reconciliation is arithmetic and falsifiable: exact allocated opening capital equals portfolio opening capital, aggregate net profit equals the exact sum of component net profit, and aggregate component count equals the request. Component returns are sampled from each engine's actual end-of-tick mark-to-market equity observations on one shared 30-point UTC cadence; open-position price movement is included and closed-trade reconstruction is forbidden. Every resolved FX evidence object must match its request-bound version and canonical hash before freshness validation. The run persists bounded portfolio start/completion/failure audit evidence."
    )
    request_id = generate_id("req")
    dataset = _dataset(request_id)
    request, auth = _build_portfolio_request(dataset)
    with tempfile.TemporaryDirectory() as tmp_dir:
        dependencies = FakeDependencies(Path(tmp_dir), dataset)
        result = unwrap_simulation_response(
            run_portfolio_backtest(request, auth, dependencies),
            operation="usage.run_portfolio_backtest",
        )
        print(f"Portfolio status: {result.status}")


def fr_sim_031() -> None:
    """Demonstrate FR-SIM-031.

    Responsibility:
        The system shall run an explicitly requested approximation only when enabled,
        mark every output `canonical=false`, disclose assumptions, prohibit canonical
        fills, promotion evidence, and reports, and persist bounded research
        start/completion/failure audit evidence.
    """
    _header(
        "Demonstrate FR-SIM-031. Responsibility: The system shall run an explicitly requested approximation only when enabled, mark every output `canonical=false`, disclose assumptions, prohibit canonical fills, promotion evidence, and reports, and persist bounded research start/completion/failure audit evidence."
    )
    request_id = generate_id("req")
    dataset = _dataset(request_id)
    request = _build_request(
        dataset,
        runtime_profile="fast_research",
        canonical=False,
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        dependencies = FakeDependencies(Path(tmp_dir), dataset)
        result = unwrap_simulation_response(
            run_fast_research(request, _auth(request), dependencies),
            operation="usage.run_fast_research",
        )
        print(f"Fast research canonical: {result.canonical}")


def main() -> None:
    """Run Simulator run usage example."""
    fr_sim_029()
    fr_sim_032()
    fr_sim_030()
    fr_sim_034()
    fr_sim_031()


if __name__ == "__main__":
    main()
