"""Unit tests and fixtures for official Simulation orchestration."""
# ruff: noqa: INP001

from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

import pytest
from app.services.data.contracts import (
    DataQualityReport,
    MarketDataset,
    TickRecord,
)
from app.services.data.evidence.fx_contracts import (
    FXConversionEvidence,
    FXRateLeg,
)
from app.services.simulator.accounting import ExecutionCostModel, SymbolSpecification
from app.services.simulator.errors import SimulationError
from app.services.simulator.execution import ExecutionProfile, SessionInterval
from app.services.simulator.run import SimulationBacktestRequestV1, run_backtest
from app.services.trading import OrderIntent, TradingRoute
from app.utils import AuthContext, canonical_json
from tests.simulator._fixtures.sqlite_store import SqliteSimulationStateStore


def _dataset(request_id: str) -> MarketDataset:
    """Build a two-tick official Data dataset."""
    start = datetime(2025, 1, 6, 12, tzinfo=UTC)
    records = tuple(
        TickRecord(
            timestamp=start + timedelta(seconds=index),
            source="fixture",
            source_symbol="EURUSD",
            available_at=start + timedelta(seconds=index),
            bid=Decimal("1.10000") + Decimal(index) / Decimal(100_000),
            ask=Decimal("1.10002") + Decimal(index) / Decimal(100_000),
            last=None,
            volume=Decimal(10),
            price_unit="quote",
            volume_unit="lot",
        )
        for index in range(2)
    )
    quality = DataQualityReport(
        quality_status="passed",
        quality_score=Decimal(1),
        record_count=2,
        checked_count=2,
        truncated=False,
        sample_limit=2,
        schema_version="v1",
        generated_at=records[-1].available_at,
    )
    return MarketDataset(
        normalization_version="v1",
        data_kind="ticks",
        symbol="EURUSD",
        timeframe="M1",
        records=records,
        start=records[0].timestamp,
        end=records[-1].timestamp,
        available_at=records[-1].available_at,
        record_count=2,
        quality_report=quality,
        source_metadata={"tick_generation_model": "real"},
        license_metadata={"license": "test"},
        cache_status="not_used",
        workflow_context="backtest",
        precision_policy="decimal_string",
        request_id=request_id,
    )


def _data_hash(dataset: MarketDataset) -> str:
    """Hash a dataset with the official validation convention."""
    return sha256(
        canonical_json(dataset.model_dump(mode="python", warnings=False)).encode(
            "utf-8"
        )
    ).hexdigest()


def _request(
    dataset: MarketDataset,
    *,
    runtime_profile: str = "simulation",
    canonical: bool = True,
    suffix: str = "5",
    seed: int = 7,
) -> SimulationBacktestRequestV1:
    """Build a correctly hashed exact backtest request.

    ``seed`` varies the hashed request material while leaving ``request_id``
    unchanged, which is what an identity-conflict test requires.
    """
    payload: dict[str, object] = {
        "request_id": f"req-{suffix * 8}-{suffix * 4}-4{suffix * 3}-8{suffix * 3}-{suffix * 12}",
        "workflow_id": f"wf-{suffix * 8}-{suffix * 4}-4{suffix * 3}-8{suffix * 3}-{suffix * 12}",
        "correlation_id": f"cor-{suffix * 8}-{suffix * 4}-4{suffix * 3}-8{suffix * 3}-{suffix * 12}",
        "strategy_id": f"strategy-{suffix}",
        "strategy_version": "v1",
        "strategy_config_ref": "strategy-config",
        "strategy_config_hash": "a" * 64,
        "data_ref": "dataset",
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
        "symbol": "EURUSD",
        "timeframe": "M1",
        "start": dataset.start,
        "end": dataset.end,
        "parameters": {"period": 14},
        "initial_balance": Decimal(10_000),
        "account_currency": "USD",
        "asset_class": "FX",
        "seed": seed,
        "runtime_profile": runtime_profile,
        "execution_route": "sim",
        "canonical": canonical,
    }
    payload["config_hash"] = SimulationBacktestRequestV1.calculate_config_hash(payload)
    return SimulationBacktestRequestV1.model_validate(payload)


def _auth(request: SimulationBacktestRequestV1) -> AuthContext:
    """Build matching authenticated run authority."""
    return AuthContext(
        contract_version="v1",
        schema_id="utils.auth_context.v1",
        principal_id="simulator-test",
        principal_type="SERVICE_ACCOUNT",
        roles=("builder",),
        permissions=("simulation:run",),
        scopes=("simulation:run",),
        tenant_or_environment="test",
        request_id=request.request_id,
        workflow_id=request.workflow_id,
        correlation_id=request.correlation_id,
        issued_at=request.start - timedelta(days=1),
    )


class FakeDependencies:
    """Complete deterministic cross-domain dependency fixture."""

    fast_research_enabled = True

    def __init__(self, tmp_path: Path, dataset: MarketDataset) -> None:
        """Initialize fixture state and evidence.

        Args:
            tmp_path: Isolated test root.
            dataset: Market evidence to return.
        """
        self.artifact_root = tmp_path / "artifacts"
        self.state_store = SqliteSimulationStateStore(
            tmp_path / "state.db", self.artifact_root
        )
        self.dataset = dataset

    def load_market_data(self, request: SimulationBacktestRequestV1) -> MarketDataset:
        """Return referenced market evidence."""
        del request
        return self.dataset

    def generate_tick_series(
        self, dataset: MarketDataset, request: SimulationBacktestRequestV1
    ) -> MarketDataset:
        """Return Data's already-real tick evidence."""
        del request
        return dataset

    def calculate_indicators(
        self, dataset: MarketDataset, request: SimulationBacktestRequestV1
    ) -> tuple[object, ...]:
        """Record an empty valid Indicator set for this fixture."""
        del dataset, request
        return ()

    def evaluate_strategy(
        self,
        dataset: MarketDataset,
        indicators: tuple[object, ...],
        request: SimulationBacktestRequestV1,
    ) -> tuple[object, ...]:
        """Record an empty Strategy proposal set for this fixture."""
        del dataset, indicators, request
        return ()

    def review_risk(
        self, intents: tuple[object, ...], request: SimulationBacktestRequestV1
    ) -> tuple[object, ...]:
        """Record an empty Risk package set for this fixture."""
        del intents, request
        return ()

    def build_order_intents(
        self, decisions: tuple[object, ...], request: SimulationBacktestRequestV1
    ) -> tuple[OrderIntent, ...]:
        """Return one Trading-owned approved sim intent."""
        del decisions
        created = request.start - timedelta(seconds=1)
        return (
            OrderIntent(
                client_order_id=f"order-{request.strategy_id}",
                request_id=request.request_id,
                workflow_id=request.workflow_id,
                correlation_id=request.correlation_id,
                route=TradingRoute.SIM,
                provider_id=None,
                account_id="account",
                strategy_id=request.strategy_id,
                strategy_version=request.strategy_version,
                source_intent_id=f"intent-{request.strategy_id}",
                symbol=request.symbol,
                action="submit_order",
                side="BUY",
                order_type="MARKET",
                quantity_unit="lot",
                approved_volume=Decimal(1),
                risk_approved_volume=Decimal(1),
                time_in_force="FOK",
                idempotency_hash="e" * 64,
                canonical_material_version="v1",
                risk_decision_id="risk",
                action_policy_verdict_id="verdict",
                approval_token_ref="approval",
                created_at=created,
                valid_until=request.end + timedelta(days=1),
            ),
        )

    def resolve_execution_profile(
        self, request: SimulationBacktestRequestV1
    ) -> ExecutionProfile:
        """Return an explicit full-week no-slippage profile."""
        del request
        return ExecutionProfile(
            slippage_mode="none",
            fixed_slippage_points=Decimal(0),
            point_value=Decimal("0.00001"),
            price_quantum=Decimal("0.00001"),
            maximum_slippage_points=Decimal(0),
            maximum_gap_points=Decimal(10),
            liquidity_mode="unbounded",
            participation_rate=Decimal(0),
            sessions=(SessionInterval(start_week_second=0, end_week_second=604_800),),
        )

    def resolve_symbol_specification(
        self, request: SimulationBacktestRequestV1
    ) -> SymbolSpecification:
        """Return approved FX volume and margin evidence."""
        del request
        return SymbolSpecification(
            minimum_volume=Decimal("0.01"),
            maximum_volume=Decimal(100),
            volume_step=Decimal("0.01"),
            contract_size=Decimal(100_000),
            leverage=Decimal(100),
        )

    def resolve_cost_model(
        self, request: SimulationBacktestRequestV1
    ) -> ExecutionCostModel:
        """Return a zero-cost explicit fixture model."""
        del request
        return ExecutionCostModel(
            commission_per_lot_per_side=Decimal(0),
            long_swap_per_lot_rollover=Decimal(0),
            short_swap_per_lot_rollover=Decimal(0),
        )

    def resolve_fx_evidence(
        self, evidence_ids: tuple[str, ...]
    ) -> Mapping[str, FXConversionEvidence]:
        """Return one fresh Data-owned FX evidence record per identifier."""
        instant = self.dataset.start
        leg = FXRateLeg(
            source_currency="EUR",
            target_currency="USD",
            rate=Decimal("1.10"),
            source_id="fixture",
            provider_symbol="EURUSD",
            as_of=instant,
            provenance={"provider": "fixture"},
        )
        return {
            evidence_id: FXConversionEvidence(
                source_currency="EUR",
                target_currency="USD",
                legs=(leg,),
                composite_rate=Decimal("1.10"),
                as_of=instant,
                expires_at=instant + timedelta(days=365),
                path_policy_id="direct",
                path_policy_version="v1",
                provenance={"provider": "fixture"},
                request_id=self.dataset.request_id,
            )
            for evidence_id in evidence_ids
        }


class CostBearingDependencies(FakeDependencies):
    """Fixture whose cost model charges a non-zero commission and swap."""

    def resolve_cost_model(
        self, request: SimulationBacktestRequestV1
    ) -> ExecutionCostModel:
        """Return an explicit non-zero cost model.

        Args:
            request: Canonical run request.

        Returns:
            Cost model charging commission and swap.
        """
        del request
        return ExecutionCostModel(
            commission_per_lot_per_side=Decimal("7.5"),
            long_swap_per_lot_rollover=Decimal("2.5"),
            short_swap_per_lot_rollover=Decimal("3.5"),
        )


def test_run_backtest_maps_internal_failure(tmp_path: Path) -> None:
    """Map an unexpected dependency failure to SIM_INTERNAL_ERROR."""
    dataset = _dataset("req-55555555-5555-4555-8555-555555555555")
    request = _request(dataset)
    dependencies = FakeDependencies(tmp_path, dataset)

    def fail_load(request_value: SimulationBacktestRequestV1) -> MarketDataset:
        """Inject an unexpected read failure."""
        del request_value
        raise RuntimeError("provider secret")

    dependencies.load_market_data = fail_load  # type: ignore[method-assign]
    with pytest.raises(SimulationError) as captured:
        run_backtest(request, _auth(request), dependencies)  # type: ignore[arg-type]
    assert captured.value.code == "SIM_INTERNAL_ERROR"


def test_run_backtest_publishes_completed_result(tmp_path: Path) -> None:
    """Execute the complete official dependency path and publish artifacts."""
    dataset = _dataset("req-55555555-5555-4555-8555-555555555555")
    request = _request(dataset)
    dependencies = FakeDependencies(tmp_path, dataset)
    result = run_backtest(request, _auth(request), dependencies)  # type: ignore[arg-type]
    assert result.status == "completed"
    assert (dependencies.artifact_root / result.run_id / "manifest.json").is_file()


def test_result_accounting_matches_ledger_totals(tmp_path: Path) -> None:
    """Publish commission and swap measured by the ledger, never constants."""
    dataset = _dataset("req-88888888-8888-4888-8888-888888888888")
    request = _request(dataset, suffix="8")
    dependencies = CostBearingDependencies(tmp_path, dataset)
    result = run_backtest(request, _auth(request), dependencies)  # type: ignore[arg-type]
    accounting = result.accounting
    assert accounting.commission != Decimal(0)
    assert accounting.commission < Decimal(0)
    assert (
        accounting.net_profit
        == accounting.gross_profit + accounting.commission + accounting.swap
    )
    assert accounting.net_profit == accounting.final_balance - request.initial_balance


def test_repeat_request_returns_the_stored_completed_result(tmp_path: Path) -> None:
    """Resolve idempotency through `resolve_idempotent_run`, not inline logic."""
    dataset = _dataset("req-aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
    request = _request(dataset, suffix="a")
    dependencies = FakeDependencies(tmp_path, dataset)
    first = run_backtest(request, _auth(request), dependencies)  # type: ignore[arg-type]
    second = run_backtest(request, _auth(request), dependencies)  # type: ignore[arg-type]
    assert first.run_id == second.run_id
    assert first.request_hash == second.request_hash


def test_repeat_request_with_different_hash_conflicts(tmp_path: Path) -> None:
    """Reject one request identifier bound to different material."""
    dataset = _dataset("req-bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
    request = _request(dataset, suffix="b")
    dependencies = FakeDependencies(tmp_path, dataset)
    first = run_backtest(request, _auth(request), dependencies)  # type: ignore[arg-type]
    conflicting = _request(dataset, suffix="b", seed=11)
    assert conflicting.request_id == request.request_id
    assert conflicting.config_hash != request.config_hash
    with pytest.raises(SimulationError) as captured:
        run_backtest(  # type: ignore[arg-type]
            conflicting, _auth(conflicting), dependencies
        )
    assert captured.value.code == "SIM_RUN_ID_CONFLICT"
    stored = dependencies.state_store.load_run(request.request_id)
    assert stored is not None
    assert stored["run_id"] == first.run_id


def test_markdown_report_states_measured_costs(tmp_path: Path) -> None:
    """Prove the canonical report renders the measured, non-zero cost totals."""
    dataset = _dataset("req-99999999-9999-4999-8999-999999999999")
    request = _request(dataset, suffix="9")
    dependencies = CostBearingDependencies(tmp_path, dataset)
    result = run_backtest(request, _auth(request), dependencies)  # type: ignore[arg-type]
    report = (dependencies.artifact_root / result.run_id / "report.md").read_text(
        encoding="utf-8"
    )
    assert f"- Commission: {result.accounting.commission}" in report
    assert "- Commission: 0\n" not in report
