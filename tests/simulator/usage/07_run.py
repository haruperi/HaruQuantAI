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
    calculate_portfolio_backtest_config_hash,
    calculate_simulation_backtest_config_hash,
    create_simulation_value,
    dump_simulation_value,
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


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


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
        "components": (dump_simulation_value(component),),
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


def example_run() -> None:
    """Demonstrate backtest, fast research, and portfolio backtest execution."""
    _header("Demonstrate backtest, fast research, and portfolio backtest execution.")
    print("Simulator Example 7: Backtest and Portfolio Orchestration")

    dataset = live_tick_dataset()
    request = _build_request(dataset)

    print(f"Request type: {type(request).__name__}")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # 1. Run canonical backtest
        deps = dependencies(tmp_path, dataset)
        result = unwrap_simulation_response(
            run_backtest(request, authority(request), deps),
            operation="usage.run_backtest",
        )
        print("Canonical backtest result:", dump_simulation_value(result))

        # 2. Run fast research
        fast_dataset = live_tick_dataset()
        fast_request = _build_request(
            fast_dataset,
            runtime_profile="fast_research",
            canonical=False,
        )
        fast_deps = dependencies(tmp_path, fast_dataset)
        fast_result = unwrap_simulation_response(
            run_fast_research(fast_request, authority(fast_request), fast_deps),
            operation="usage.run_fast_research",
        )
        print("Fast-research result:", dump_simulation_value(fast_result))

        # 3. Run portfolio backtest
        port_dataset = live_tick_dataset()
        port_request, port_auth = _build_portfolio_request(port_dataset)
        port_deps = dependencies(tmp_path, port_dataset)
        port_result = unwrap_simulation_response(
            run_portfolio_backtest(port_request, port_auth, port_deps),
            operation="usage.run_portfolio_backtest",
        )
        print("Portfolio result:", dump_simulation_value(port_result))


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
    request = _build_request(live_tick_dataset())
    print("Backtest request evidence:", dump_simulation_value(request))


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
    request, _ = _build_portfolio_request(live_tick_dataset())
    print("Portfolio request evidence:", dump_simulation_value(request))


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
    dataset = live_tick_dataset()
    request = _build_request(dataset)
    with tempfile.TemporaryDirectory() as tmp_dir:
        run_dependencies = dependencies(Path(tmp_dir), dataset)
        result = unwrap_simulation_response(
            run_backtest(request, authority(request), run_dependencies),
            operation="usage.run_backtest",
        )
        print("Canonical result evidence:", dump_simulation_value(result))


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
    dataset = live_tick_dataset()
    request, auth = _build_portfolio_request(dataset)
    with tempfile.TemporaryDirectory() as tmp_dir:
        run_dependencies = dependencies(Path(tmp_dir), dataset)
        result = unwrap_simulation_response(
            run_portfolio_backtest(request, auth, run_dependencies),
            operation="usage.run_portfolio_backtest",
        )
        print("Portfolio result evidence:", dump_simulation_value(result))


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
    dataset = live_tick_dataset()
    request = _build_request(
        dataset,
        runtime_profile="fast_research",
        canonical=False,
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        run_dependencies = dependencies(Path(tmp_dir), dataset)
        result = unwrap_simulation_response(
            run_fast_research(request, authority(request), run_dependencies),
            operation="usage.run_fast_research",
        )
        print("Fast-research evidence:", dump_simulation_value(result))


def main() -> None:
    """Run Simulator run usage example."""
    fr_sim_029()
    fr_sim_032()
    fr_sim_030()
    fr_sim_034()
    fr_sim_031()


if __name__ == "__main__":
    main()
