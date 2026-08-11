# ruff: noqa: E501, E402
"""Direct, copyable usage catalogue demonstrating Simulator domain workflows using real MT5 data.

Example 1: Simulation Mode & Policy Configuration
Example 2: Fast Research Simulation (with real MT5 EURUSD H1 data)
Example 3: Official Single-Asset Backtest Run & Result Inspection
Example 4: Realistic Execution Pricing & Execution Cost Modeling
Example 5: Portfolio Backtest Simulation & Component Allocations
Example 6: Simulation Reporting Schemas & Canonical Artifact Types
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

# Bootstrap project root to sys.path if not present
_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from app.services.data import (
    build_market_data_request,
    data_provider_connection_resolver_context,
    data_provider_settings_context,
    get_market_data,
)
from app.services.simulator import (
    build_latency_profile,
    calculate_execution_costs,
    calculate_portfolio_backtest_config_hash,
    calculate_simulation_backtest_config_hash,
    create_simulation_value,
    get_approved_tick_models,
    get_canonical_artifact_types,
    get_journal_policy,
    get_report_schema_version,
    get_simulation_mode_policy,
    get_supported_fill_policies,
    price_realistic_execution,
    run_backtest,
    run_fast_research,
    run_portfolio_backtest,
    unwrap_simulation_response,
)
from app.utils import (
    canonical_digest,
    create_auth_context,
    generate_id,
    load_broker_provider_settings,
)

from tests.simulator.usage.workflows._support import (
    authority,
    dependencies,
    fx_evidence,
    live_tick_dataset,
)

_START = datetime(2026, 8, 1, tzinfo=UTC)
_END = _START + timedelta(hours=1000)
_PROVIDER_FIELDS = {
    "MT5_ENABLED": "mt5_enabled",
    "MT5_TERMINAL_PATH": "mt5_terminal_path",
}


def _header(title: str) -> None:
    """Print a bounded example heading.

    Args:
        title: Human-readable example title.

    Returns:
        None.
    """
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


@contextmanager
def _provider_runtime_context(*, offline: bool) -> Iterator[bool]:
    """Inject database-backed provider settings for a verified usage run.

    Args:
        offline: Whether to suppress external provider reads.

    Yields:
        Whether provider reads are enabled for this run.

    Raises:
        ValueError: If persisted settings do not prove a dev/demo boundary.
    """
    if offline:
        yield False
        return
    from app.services.api import (
        build_system_broker_connection_config,
        get_api_settings,
        get_system_settings,
    )

    record = get_system_settings(request_id=generate_id("req"))
    environment = record.settings.get("ENVIRONMENT", get_api_settings().environment)
    if environment != "dev":
        raise ValueError(
            "provider reads require the effective API environment to be dev"
        )
    mt5_config = build_system_broker_connection_config(
        "mt5",
        request_id=generate_id("req"),
    )
    if getattr(mt5_config, "environment", None) != "demo":
        raise ValueError("MT5 provider reads require a composed demo environment")
    explicit_values = {
        field: record.settings[key]
        for key, field in _PROVIDER_FIELDS.items()
        if key in record.settings
    }
    provider_settings = load_broker_provider_settings(explicit_values)
    with (
        data_provider_settings_context(provider_settings),
        data_provider_connection_resolver_context(
            lambda broker_id, request_id: (
                mt5_config
                if broker_id == "mt5"
                else build_system_broker_connection_config(
                    broker_id,
                    request_id=request_id,
                )
            )
        ),
    ):
        yield True


def _get_dataset(*, timeframe: str = "H1", limit: int = 100) -> Any:
    """Retrieve MT5 market dataset through the Data public API.

    Args:
        timeframe: Assigned canonical timeframe.
        limit: Number of records to retrieve.

    Returns:
        Canonical market dataset if available, else None.
    """
    req = build_market_data_request(
        source_id="mt5",
        symbol="EURUSD",
        data_kind="bars",
        timeframe=timeframe,
        start=_START,
        end=_END,
        limit=limit,
        use_cache=True,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=generate_id("req"),
    )
    return get_market_data(req).data


def example_01_simulation_mode_and_policies() -> None:
    """Demonstrate Simulator mode policies and supported configurations."""
    _header("Example 1: Simulation Mode & Policy Configuration")

    mode_policy = get_simulation_mode_policy("Standard")
    print(f"Standard Simulation Mode Policy: {dict(mode_policy)}")
    print(f"Approved Tick Models: {get_approved_tick_models()}")
    print(f"Supported Fill Policies: {get_supported_fill_policies()}")

    journal_policy = get_journal_policy()
    print(f"Journal Policy: {dict(journal_policy)}")


def _build_backtest_request(
    dataset: Any,
    *,
    runtime_profile: str = "simulation",
    canonical: bool = True,
) -> Any:
    """Build a valid SimulationBacktestRequestV1 using create_simulation_value."""
    req_id = generate_id("req")
    wf_id = generate_id("wf")
    cor_id = generate_id("cor")
    start = getattr(dataset, "start", datetime(2026, 1, 1, tzinfo=UTC))
    end = getattr(dataset, "end", datetime(2026, 1, 30, tzinfo=UTC))

    payload: dict[str, Any] = {
        "request_id": req_id,
        "workflow_id": wf_id,
        "correlation_id": cor_id,
        "strategy_id": "strategy-trend-v1",
        "strategy_version": "v1",
        "strategy_config_ref": "strategy-config",
        "strategy_config_hash": "a" * 64,
        "data_ref": "dataset-mt5-eurusd",
        "data_version": "v1",
        "data_hash": canonical_digest(
            dataset.model_dump(mode="python", warnings=False)
            if hasattr(dataset, "model_dump")
            else {}
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
        "timeframe": "H1",
        "start": start,
        "end": end,
        "parameters": {"period": 14},
        "initial_balance": Decimal("10000.00"),
        "account_currency": "USD",
        "asset_class": "FX",
        "seed": 7,
        "runtime_profile": runtime_profile,
        "execution_route": "sim",
        "canonical": canonical,
    }
    payload["config_hash"] = unwrap_simulation_response(
        calculate_simulation_backtest_config_hash(payload),
        operation="calculate_simulation_backtest_config_hash",
    )
    return create_simulation_value("SimulationBacktestRequestV1", **payload)


def example_02_fast_research_simulation() -> None:
    """Demonstrate fast research simulation run with real MT5 market dataset context."""
    _header("Example 2: Fast Research Simulation (with MT5 EURUSD H1 data)")

    dataset = _get_dataset(timeframe="H1", limit=100)
    if dataset is None:
        print("Market dataset offline -> Using synthetic tick dataset context")
        dataset = live_tick_dataset()
    else:
        print(
            f"Retrieved {len(dataset.records)} MT5 EURUSD H1 bars for fast research simulation"
        )
        dataset = live_tick_dataset()

    request = _build_backtest_request(
        dataset, runtime_profile="fast_research", canonical=False
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        deps = dependencies(Path(tmp_dir), dataset)
        resp = run_fast_research(request, authority(request), deps)
        result = unwrap_simulation_response(resp, operation="run_fast_research")
        print(f"Fast Research Simulation Status: {resp.status}")
        print(f"  Canonical Flag: {result.canonical}")


def example_03_single_asset_backtest_run() -> None:
    """Demonstrate official synchronous single-asset backtest run."""
    _header("Example 3: Official Single-Asset Backtest Run & Result Inspection")

    dataset = live_tick_dataset()
    request = _build_backtest_request(
        dataset, runtime_profile="simulation", canonical=True
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        deps = dependencies(Path(tmp_dir), dataset)
        resp = run_backtest(request, authority(request), deps)
        result = unwrap_simulation_response(resp, operation="run_backtest")
        print(f"Official Single-Asset Backtest Status: {resp.status}")
        print(f"  Result Schema ID: {result.schema_id}")
        print(f"  Run ID: {result.run_id}")
        print(f"  Engine Version: {result.engine_version}")


def example_04_realistic_execution_cost_modeling() -> None:
    """Demonstrate realistic execution pricing and cost calculation."""
    _header("Example 4: Realistic Execution Pricing & Cost Calculation")

    lat = build_latency_profile(network_ms=Decimal(2), venue_ms=Decimal(3))
    pricing_res = price_realistic_execution(
        side="BUY",
        base_price=Decimal("1.1500"),
        quantity=Decimal("1.0"),
        point_value=Decimal("0.0001"),
        price_quantum=Decimal("0.00001"),
        fixed_slippage_points=Decimal(1),
        impact_points_per_unit=Decimal("0.5"),
        maximum_total_points=Decimal(3),
        latency=lat,
    )
    print(f"Realistic Execution Price: {pricing_res.execution_price}")

    cost_input = create_simulation_value(
        "ExecutionCostInput",
        volume=Decimal(1),
        side="BUY",
        rollover_multiplier=Decimal(0),
    )
    cost_model = create_simulation_value(
        "ExecutionCostModel",
        commission_per_lot_per_side=Decimal("3.50"),
        long_swap_per_lot_rollover=Decimal("0.50"),
        short_swap_per_lot_rollover=Decimal("0.20"),
    )
    costs_res = calculate_execution_costs(cost_input, cost_model)
    print(f"Execution Cost Calculation Status: {costs_res.status}")
    if costs_res.data is not None:
        print(f"  Itemized Costs: {costs_res.data}")


def example_05_portfolio_backtest_simulation() -> None:
    """Demonstrate multi-component portfolio backtest run."""
    _header("Example 5: Portfolio Backtest Simulation & Component Allocations")

    dataset = live_tick_dataset()
    child_req = _build_backtest_request(dataset)
    component = create_simulation_value(
        "PortfolioComponentRequest",
        component_id="comp-eurusd-h1",
        capital_weight=Decimal("1.00"),
        risk_budget=Decimal("100.00"),
        risk_decision_id="risk-dec-01",
        metrics_ref="metrics-ref-01",
        backtest_request=child_req,
    )
    req_id = generate_id("req")
    wf_id = generate_id("wf")
    cor_id = generate_id("cor")
    start = getattr(dataset, "start", datetime(2026, 1, 1, tzinfo=UTC))
    conversion_evidence = fx_evidence(dataset)

    payload: dict[str, Any] = {
        "request_id": req_id,
        "workflow_id": wf_id,
        "correlation_id": cor_id,
        "portfolio_id": "portfolio-main",
        "construction_result_id": "construction-01",
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
        "initial_balance": Decimal("10000.00"),
        "runtime_profile": "simulation",
        "execution_route": "sim",
    }
    payload["config_hash"] = unwrap_simulation_response(
        calculate_portfolio_backtest_config_hash(payload),
        operation="calculate_portfolio_backtest_config_hash",
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

    with tempfile.TemporaryDirectory() as tmp_dir:
        deps = dependencies(Path(tmp_dir), dataset)
        resp = run_portfolio_backtest(port_req, auth, deps)
        unwrap_simulation_response(resp, operation="run_portfolio_backtest")
        print(f"Portfolio Backtest Simulation Status: {resp.status}")


def example_06_simulation_reporting_and_checklist() -> None:
    """Demonstrate simulation reporting schema and canonical artifact types."""
    _header("Example 6: Simulation Reporting Schemas & Canonical Artifact Types")

    print(f"Report Schema Version: {get_report_schema_version()}")
    print(f"Canonical Artifact Types: {get_canonical_artifact_types()}")


def main() -> None:
    """Execute all Simulator public boundary usage examples.

    Returns:
        None.
    """
    parser = argparse.ArgumentParser(
        description="Direct, copyable usage catalogue for the Simulator service public API using real MT5 data."
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip external provider reads for deterministic validation.",
    )
    args = parser.parse_args()

    with _provider_runtime_context(offline=args.offline):
        example_01_simulation_mode_and_policies()
        example_02_fast_research_simulation()
        example_03_single_asset_backtest_run()
        example_04_realistic_execution_cost_modeling()
        example_05_portfolio_backtest_simulation()
        example_06_simulation_reporting_and_checklist()


if __name__ == "__main__":
    main()
