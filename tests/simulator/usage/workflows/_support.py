"""Shared, non-workflow infrastructure for Simulator workflow examples."""

from __future__ import annotations

import os
import sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    MarketDataset,
    generate_tick_series,
    get_market_data,
    unwrap_data_response,
)
from app.services.simulator import (
    PortfolioBacktestRequestV1,
    PortfolioComponentRequest,
    SimulationBacktestRequestV1,
    unwrap_simulation_response,
)
from app.utils import AuthContext, canonical_digest, generate_id
from tests.data.usage.workflows._support import market_request
from tests.simulator.unit.test_orchestrator import (
    FakeDependencies,
    _auth,
    _data_hash,
    _fx_evidence,
)

_DATASET_ENV = "HARU_WORKFLOW_MARKET_DATASET"


def live_market_dataset() -> MarketDataset:
    """Return genuine bounded MT5 evidence, reusing runner-captured evidence."""
    captured = os.environ.get(_DATASET_ENV)
    if captured:
        return MarketDataset.model_validate_json(
            Path(captured).read_text(encoding="utf-8")
        )
    return unwrap_data_response(
        get_market_data(market_request("bars", timeframe="M1", limit=20)),
        operation="simulation.usage.workflows.live_market_dataset",
        request_id="req-00000000-0000-4000-8000-000000000000",
    )


def live_tick_dataset() -> MarketDataset:
    """Return canonical ticks deterministically derived from genuine MT5 bars."""
    dataset = live_market_dataset()
    generated: object = generate_tick_series(
        dataset,
        model="trading_bar",
        trading_timeframe="M1",
        spread_model="fixed_spread",
        fixed_spread_points=Decimal(2),
        point_value=Decimal("0.00001"),
    )
    while hasattr(generated, "status") and hasattr(generated, "data"):
        generated = unwrap_data_response(
            generated,  # type: ignore[arg-type]
            operation="simulation.usage.workflows.live_tick_dataset",
            request_id=dataset.request_id,
        )
    if not isinstance(generated, MarketDataset):
        raise TypeError("Data tick generation did not return a MarketDataset")
    return generated


def backtest_request(
    dataset: MarketDataset,
    *,
    runtime_profile: str = "simulation",
    canonical: bool = True,
) -> SimulationBacktestRequestV1:
    """Build one canonical request bound to genuine Data evidence."""
    payload: dict[str, object] = {
        "request_id": generate_id("req"),
        "workflow_id": generate_id("wf"),
        "correlation_id": generate_id("cor"),
        "strategy_id": "strategy-1",
        "strategy_version": "v1",
        "strategy_config_ref": "strategy-config",
        "strategy_config_hash": "a" * 64,
        "data_ref": f"mt5:{dataset.symbol}:{dataset.timeframe}",
        "data_version": "v1",
        "data_hash": _data_hash(dataset),
        "tick_generation_ref": "tick-profile",
        "tick_generation_version": "v1",
        "tick_generation_hash": "b" * 64,
        "execution_profile_ref": "execution-profile",
        "execution_profile_version": "v1",
        "execution_profile_hash": "c" * 64,
        "risk_policy_ref": "risk-policy",
        "risk_policy_version": "v1",
        "risk_policy_hash": "d" * 64,
        "symbol": dataset.symbol,
        "timeframe": dataset.timeframe,
        "start": dataset.start,
        "end": dataset.end,
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


def authority(request: SimulationBacktestRequestV1) -> AuthContext:
    """Return matching simulation-only authority."""
    return _auth(request)


def dependencies(root: Path, dataset: MarketDataset) -> FakeDependencies:
    """Return deterministic non-broker Simulation collaborators."""
    return FakeDependencies(root, dataset)


def portfolio_request(
    dataset: MarketDataset,
) -> tuple[PortfolioBacktestRequestV1, AuthContext]:
    """Build one portfolio request bound to genuine Data/FX evidence."""
    child = backtest_request(dataset)
    component = PortfolioComponentRequest(
        component_id="component-1",
        capital_weight=Decimal(1),
        risk_budget=Decimal(100),
        risk_decision_id="risk-1",
        metrics_ref="metrics-1",
        backtest_request=child,
    )
    request_id = generate_id("req")
    workflow_id = generate_id("wf")
    correlation_id = generate_id("cor")
    fx = _fx_evidence(dataset)
    payload: dict[str, object] = {
        "request_id": request_id,
        "workflow_id": workflow_id,
        "correlation_id": correlation_id,
        "portfolio_id": "portfolio",
        "construction_result_id": "construction",
        "construction_version": "v1",
        "components": (component.model_dump(mode="python", warnings=False),),
        "measurement_start": dataset.start,
        "measurement_end": dataset.start + timedelta(days=30),
        "base_currency": "USD",
        "fx_evidence_ids": ("fx-1",),
        "fx_evidence_versions": (fx.contract_version,),
        "fx_evidence_hashes": (
            canonical_digest(fx.model_dump(mode="python", warnings=False)),
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
    request = PortfolioBacktestRequestV1.model_validate(payload)
    auth = AuthContext(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="simulator-workflow",
        principal_type="SERVICE_ACCOUNT",
        roles=("builder",),
        permissions=("simulation:run",),
        scopes=("simulation:run",),
        tenant_or_environment="dev",
        request_id=request_id,
        workflow_id=workflow_id,
        correlation_id=correlation_id,
        issued_at=dataset.start - timedelta(days=1),
    )
    return request, auth


__all__ = [
    "_DATASET_ENV",
    "authority",
    "backtest_request",
    "dependencies",
    "live_market_dataset",
    "live_tick_dataset",
    "portfolio_request",
]
