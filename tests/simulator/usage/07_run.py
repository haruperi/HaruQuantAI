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

from app.services.simulator.run import (
    PortfolioBacktestRequestV1,
    PortfolioComponentRequest,
    SimulationBacktestRequestV1,
    run_backtest,
    run_fast_research,
    run_portfolio_backtest,
)
from app.utils import AuthContext, generate_id
from tests.simulator.unit.test_orchestrator import (
    FakeDependencies,
    _auth,
    _data_hash,
    _dataset,
)


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
    payload["config_hash"] = SimulationBacktestRequestV1.calculate_config_hash(payload)
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
        "execution_profile_version": "v1",
        "risk_policy_version": "v1",
        "seed": 7,
        "initial_balance": Decimal(10_000),
        "runtime_profile": "simulation",
        "execution_route": "sim",
    }
    payload["config_hash"] = PortfolioBacktestRequestV1.calculate_config_hash(payload)
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
    print("=" * 80)
    print("Simulator Example 7: Backtest and Portfolio Orchestration")
    print("=" * 80)

    req_id = generate_id("req")
    dataset = _dataset(req_id)
    request = _build_request(dataset)

    print(f"Request type: {type(request).__name__}")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # 1. Run canonical backtest
        deps = FakeDependencies(tmp_path, dataset)  # type: ignore[arg-type]
        result = run_backtest(request, _auth(request), deps)
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
        fast_result = run_fast_research(fast_request, _auth(fast_request), fast_deps)
        print(f"Fast research canonical status: {fast_result.canonical}")

        # 3. Run portfolio backtest
        port_req_id = generate_id("req")
        port_dataset = _dataset(port_req_id)
        port_request, port_auth = _build_portfolio_request(port_dataset)
        port_deps = FakeDependencies(tmp_path, port_dataset)  # type: ignore[arg-type]
        port_result = run_portfolio_backtest(port_request, port_auth, port_deps)
        print(f"Portfolio backtest status: {port_result.status}")


def main() -> None:
    """Run Simulator run usage example."""
    example_run()


if __name__ == "__main__":
    main()
