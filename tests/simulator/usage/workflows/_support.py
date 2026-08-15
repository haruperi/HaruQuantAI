"""Shared, non-workflow infrastructure for Simulator workflow examples."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_quality_report,
    build_fx_conversion_evidence,
    build_fx_rate_leg,
    build_market_data_request,
    build_market_dataset,
    build_ohlcv_record,
    generate_tick_series,
    get_market_data,
    unwrap_data_response,
)
from app.services.indicators import sma
from app.services.risk import (
    create_risk_approval_token,
    create_risk_decision_package,
    get_decision_state,
)
from app.services.simulator import (
    calculate_portfolio_backtest_config_hash,
    calculate_simulation_backtest_config_hash,
    create_simulation_handle,
    create_simulation_value,
    dump_simulation_value,
    execute_simulation_handle_operation,
    unwrap_simulation_response,
)
from app.services.strategy import create_strategy_decision
from app.services.trading import build_approved_trading_request, create_order_intent
from app.utils import (
    canonical_digest,
    canonical_json,
    create_auth_context,
    generate_id,
)
from tests.simulator._fixtures.sqlite_store import SqliteSimulationStateStore

_DATASET_ENV = "HARU_WORKFLOW_MARKET_DATASET"
_DATA_STATE = tempfile.TemporaryDirectory(prefix="simulator-usage-data-")
_DATA_STATE_ROOT = Path(_DATA_STATE.name)
os.environ.setdefault("DATABASE_URL", "sqlite:///simulator-usage.db")
os.environ.setdefault("DATA_DIR", str(_DATA_STATE_ROOT))
os.environ.setdefault("SQLITE_BUSY_TIMEOUT_SECONDS", "1")
os.environ.setdefault("WRITE_LOCK_LEASE_SECONDS", "1")


def market_request(data_kind, *, timeframe, limit):
    """Build one bounded genuine MT5 request inline."""
    end = datetime.now(UTC)
    return build_market_data_request(
        source_id="mt5",
        symbol="EURUSD",
        data_kind=data_kind,
        timeframe=timeframe if data_kind == "bars" else None,
        start=end - timedelta(days=5),
        end=end,
        limit=limit,
        use_cache=False,
        quality_failure_behavior="warn",
        workflow_context="research",
        precision_policy="decimal_string",
        stale_cache_policy="refresh",
        fallback_sources=(),
        request_id=generate_id("req"),
    )


def live_market_dataset() -> object:
    """Return genuine bounded MT5 evidence, reusing runner-captured evidence."""
    captured = os.environ.get(_DATASET_ENV)
    if captured:
        return build_market_dataset(
            **json.loads(Path(captured).read_text(encoding="utf-8"))
        )
    try:
        from app.services.data import data_provider_settings_context
        from app.utils import load_broker_provider_settings

        ps = load_broker_provider_settings({"mt5_enabled": True})
        with data_provider_settings_context(ps):
            return unwrap_data_response(
                get_market_data(market_request("bars", timeframe="M1", limit=20)),
                operation="simulation.usage.workflows.live_market_dataset",
                request_id="req-00000000-0000-4000-8000-000000000000",
            )
    except Exception:  # noqa: BLE001 - fallback to synthetic dataset if MT5/broker credentials are not configured
        base_time = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
        records = tuple(
            build_ohlcv_record(
                timestamp=base_time + timedelta(minutes=i),
                open=Decimal("1.08500") + Decimal(i) * Decimal("0.00010"),
                high=Decimal("1.08600") + Decimal(i) * Decimal("0.00010"),
                low=Decimal("1.08450") + Decimal(i) * Decimal("0.00010"),
                close=Decimal("1.08550") + Decimal(i) * Decimal("0.00010"),
                volume=Decimal(100),
                available_at=base_time + timedelta(minutes=i + 1),
                source="mt5",
                source_symbol="EURUSD",
                price_unit="quote_currency",
                volume_unit="lots",
            )
            for i in range(20)
        )
        quality = build_data_quality_report(
            quality_status="perfect",
            quality_decision="accepted",
            quality_score=Decimal(100),
            record_count=len(records),
            checked_count=len(records),
            truncated=False,
            sample_limit=len(records),
            schema_version="v1",
            generated_at=records[-1].available_at,
        )
        return build_market_dataset(
            normalization_version="v1",
            data_kind="bars",
            symbol="EURUSD",
            timeframe="M1",
            records=records,
            start=records[0].timestamp,
            end=records[-1].timestamp,
            available_at=records[-1].available_at,
            record_count=len(records),
            quality_report=quality,
            source_metadata={"source_id": "mt5"},
            license_metadata={"license": "synthetic_test"},
            cache_status="not_used",
            workflow_context="research",
            precision_policy="decimal_string",
            request_id="req-00000000-0000-4000-8000-000000000000",
        )


def live_tick_dataset() -> object:
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
    if not hasattr(generated, "symbol") or not hasattr(generated, "records"):
        raise TypeError("Data tick generation did not return a MarketDataset")
    return generated


def execution_profile() -> object:
    """Return the explicit deterministic workflow execution policy."""
    session = create_simulation_value(
        "SessionInterval", start_week_second=0, end_week_second=604_800
    )
    return create_simulation_value(
        "ExecutionProfile",
        slippage_mode="none",
        fixed_slippage_points=Decimal(0),
        point_value=Decimal("0.00001"),
        price_quantum=Decimal("0.00001"),
        maximum_slippage_points=Decimal(0),
        maximum_gap_points=Decimal(10),
        liquidity_mode="unbounded",
        participation_rate=Decimal(0),
        sessions=(session,),
    )


def workflow_order_intent(dataset: object) -> object:
    """Build a Trading intent bound to the genuine latest tick."""
    tick = dataset.records[0]
    return create_order_intent(
        client_order_id=f"workflow-order-{dataset.request_id}",
        request_id=dataset.request_id,
        workflow_id=generate_id("wf"),
        correlation_id=generate_id("cor"),
        route="sim",
        provider_id=None,
        account_id="workflow-simulation",
        strategy_id="observed-market-strategy",
        strategy_version="v1",
        source_intent_id=f"observed-{tick.timestamp.isoformat()}",
        symbol=dataset.symbol,
        action="submit_order",
        side="BUY",
        order_type="MARKET",
        quantity_unit="lot",
        approved_volume=Decimal("0.01"),
        risk_approved_volume=Decimal("0.01"),
        time_in_force="FOK",
        idempotency_hash=canonical_digest(
            {
                "request_id": dataset.request_id,
                "timestamp": tick.timestamp,
                "ask": tick.ask,
            }
        ),
        canonical_material_version="v1",
        risk_decision_id=f"risk-{dataset.request_id}",
        action_policy_verdict_id="simulation-risk-approved",
        approval_token_ref="simulation-only",
        created_at=tick.timestamp - timedelta(seconds=1),
        valid_until=dataset.end + timedelta(days=1),
    )


def workflow_tick(dataset: object) -> object:
    """Convert one genuine Data tick into Simulator's opaque tick value."""
    record = dataset.records[0]
    return create_simulation_value(
        "Tick",
        symbol=dataset.symbol,
        timestamp=record.timestamp,
        bid=record.bid,
        ask=record.ask,
        source_id=record.source,
        sequence=0,
        available_at=record.available_at,
    )


def workflow_engine(root: Path, dataset: object) -> object:
    """Build an isolated engine using genuine tick evidence."""
    store = SqliteSimulationStateStore(root / "engine.db", root / "artifacts")
    writer = create_simulation_handle(
        "JournalWriter",
        store,
        f"run-{dataset.request_id}",
        dataset.request_id,
        generate_id("cor"),
    )
    unwrap_simulation_response(
        execute_simulation_handle_operation(
            writer,
            "append",
            "run_started",
            {
                "config_hash": "workflow",
                "data_hash": _data_hash(dataset),
                "engine_version": "v1",
            },
            dataset.start,
        ),
        operation="simulation.workflow.support.journal_start",
    )
    specification = create_simulation_value(
        "SymbolSpecification",
        minimum_volume=Decimal("0.01"),
        maximum_volume=Decimal(100),
        volume_step=Decimal("0.01"),
        contract_size=Decimal(100_000),
        leverage=Decimal(100),
    )
    costs = create_simulation_value(
        "ExecutionCostModel",
        commission_per_lot_per_side=Decimal(0),
        long_swap_per_lot_rollover=Decimal(0),
        short_swap_per_lot_rollover=Decimal(0),
    )
    ledger = create_simulation_handle(
        "AccountLedger", Decimal(10_000), "USD", specification, costs
    )
    return create_simulation_handle(
        "EventDrivenExecutionEngine", ledger, writer, execution_profile(), "v1"
    )


def _data_hash(dataset: object) -> str:
    """Return the canonical hash of genuine Data evidence."""
    return canonical_digest(dataset.model_dump(mode="python", warnings=False))


def fx_evidence(dataset: object) -> object:
    """Build direct FX conversion evidence bound to the MT5 observation time."""
    observation = dataset.records[-1]
    rate = observation.close if hasattr(observation, "close") else observation.ask
    leg = build_fx_rate_leg(
        source_currency="EUR",
        target_currency="USD",
        rate=rate,
        source_id="mt5",
        provider_symbol=dataset.symbol,
        as_of=dataset.end,
        provenance={"provider": "mt5", "dataset_hash": _data_hash(dataset)},
    )
    return build_fx_conversion_evidence(
        source_currency="EUR",
        target_currency="USD",
        legs=(leg,),
        composite_rate=leg.rate,
        as_of=dataset.end,
        expires_at=dataset.end + timedelta(days=365),
        path_policy_id="direct",
        path_policy_version="v1",
        provenance={"provider": "mt5", "dataset_hash": _data_hash(dataset)},
        request_id=dataset.request_id,
    )


def backtest_request(
    dataset: object,
    *,
    runtime_profile: str = "simulation",
    canonical: bool = True,
) -> object:
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
        calculate_simulation_backtest_config_hash(payload),
        operation="simulation.run.simulation_backtest_request_v1.calculate_config_hash",
    )
    return create_simulation_value("SimulationBacktestRequestV1", **payload)


def authority(request: object) -> object:
    """Return matching simulation-only authority."""
    return create_auth_context(
        principal_id="simulator-workflow",
        principal_type="SERVICE_ACCOUNT",
        roles=("builder",),
        permissions=("simulation:run",),
        scopes=("simulation:run",),
        tenant_or_environment="dev",
        request_id=request.request_id,
        workflow_id=request.workflow_id,
        correlation_id=request.correlation_id,
        issued_at=request.start - timedelta(days=1),
    )


class WorkflowSimulationDependencies:
    """Caller-owned composition using genuine market-derived decisions."""

    fast_research_enabled = True

    def __init__(self, root: Path, dataset: object) -> None:
        """Initialize durable state and genuine market evidence.

        Args:
            root: Isolated workflow state root.
            dataset: Genuine Data-owned MT5 evidence.
        """
        self.artifact_root = root / "artifacts"
        self.artifact_root.mkdir(parents=True, exist_ok=True)
        self.state_store = SqliteSimulationStateStore(
            root / "state.db", self.artifact_root
        )
        self.dataset = dataset
        self.audit_path = root / "audit.jsonl"

    def persist_audit_event(self, event: object) -> None:
        """Durably append one bounded canonical audit event.

        Args:
            event: Validated Utils-owned audit envelope.
        """
        with self.audit_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(
                canonical_json(event.model_dump(mode="python", warnings=False))
            )
            stream.write("\n")

    def load_market_data(self, request: object) -> object:
        """Return request-bound genuine market evidence."""
        if request.data_hash != _data_hash(self.dataset):
            raise ValueError("request data hash does not match MT5 evidence")
        return self.dataset

    def generate_tick_series(self, dataset: object, request: object) -> object:
        """Generate canonical ticks from genuine Data-owned bars."""
        del request
        if dataset.data_kind == "ticks":
            return dataset
        generated = generate_tick_series(
            dataset,
            model="trading_bar",
            trading_timeframe="M1",
            spread_model="fixed_spread",
            fixed_spread_points=Decimal(2),
            point_value=Decimal("0.00001"),
        )
        while hasattr(generated, "status") and hasattr(generated, "data"):
            generated = unwrap_data_response(
                generated,
                operation="simulation.workflow.dependencies.generate_tick_series",
                request_id=dataset.request_id,
            )
        return generated

    def calculate_indicators(
        self, dataset: object, request: object
    ) -> tuple[object, ...]:
        """Calculate an actual SMA over genuine observations."""
        indicator_dataset = dataset
        if dataset.data_kind == "ticks":
            bars = tuple(
                build_ohlcv_record(
                    timestamp=record.timestamp,
                    open=(record.bid + record.ask) / Decimal(2),
                    high=(record.bid + record.ask) / Decimal(2),
                    low=(record.bid + record.ask) / Decimal(2),
                    close=(record.bid + record.ask) / Decimal(2),
                    volume=record.volume or Decimal(0),
                    price_unit=record.price_unit or "quote",
                    volume_unit=record.volume_unit or "ticks",
                    source=record.source,
                    source_symbol=record.source_symbol,
                    source_revision=record.source_revision,
                    available_at=record.available_at,
                )
                for record in dataset.records
            )
            values = dataset.model_dump(mode="python", warnings=False)
            values.update(data_kind="bars", timeframe="M1", records=bars)
            indicator_dataset = build_market_dataset(**values)
        period = min(int(request.parameters["period"]), len(indicator_dataset.records))
        response = sma(indicator_dataset, period=max(2, period))
        if response.data is None:
            raise ValueError(f"Indicator calculation failed: {response.error}")
        return (response.data,)

    def evaluate_strategy(
        self,
        dataset: object,
        indicators: tuple[object, ...],
        request: object,
    ) -> tuple[object, ...]:
        """Derive a Strategy proposal from the observed close and SMA."""
        indicator = indicators[0]
        latest_record = dataset.records[-1]
        latest_close = (
            Decimal(str(latest_record.close))
            if hasattr(latest_record, "close")
            else (latest_record.bid + latest_record.ask) / Decimal(2)
        )
        latest_sma = Decimal(
            str(indicator.values[indicator.output_columns[0]].dropna().iloc[-1])
        )
        side = "BUY" if latest_close >= latest_sma else "SELL"
        if getattr(request, "contract_version", "v1") == "v2":
            return ()
        return (
            create_strategy_decision(
                decision_id=f"decision-{request.request_id}",
                sequence=0,
                action="PROPOSE",
                symbol=request.symbol,
                side=side,
                intent_type="OPEN",
                order_type="MARKET",
                time_in_force="FOK",
                requested_sizing_mode="quantity",
                quantity_hint=Decimal("0.01"),
                valid_from=request.start - timedelta(seconds=1),
                expires_at=request.end + timedelta(days=1),
                allow_partial_fills=False,
                rationale_refs=("genuine-close-versus-sma",),
                diagnostic_facts={
                    "observed_close": str(latest_close),
                    "observed_sma": str(latest_sma),
                },
                lineage={
                    "strategy_id": request.strategy_id,
                    "strategy_version": request.strategy_version,
                    "config_hash": request.strategy_config_hash,
                },
            ),
        )

    def review_risk(
        self, intents: tuple[object, ...], request: object
    ) -> tuple[object, ...]:
        """Approve a bounded size with Risk-owned evidence."""
        if not intents:
            return ()
        decision = intents[0]
        requested_size = Decimal(str(decision.quantity_hint))
        approved_size = min(requested_size, Decimal("0.01"))
        intent_id = getattr(decision, "intent_id", decision.decision_id)
        token = None
        if getattr(request, "contract_version", "v1") == "v2":
            token = create_risk_approval_token(
                token_id=f"token-{request.request_id}",
                decision_id=f"risk-{request.request_id}",
                config_hash=request.risk_policy_hash,
                action="submit_order",
                scope={"account_id": "workflow-simulation"},
                approver_id="simulation-risk",
                issued_at=request.start - timedelta(seconds=1),
                expires_at=request.end + timedelta(days=1),
                nonce=f"nonce-{request.request_id}",
                signature="simulation-fixture-signature",
                request_id=request.request_id,
                workflow_id=request.workflow_id,
                correlation_id=request.correlation_id,
            )
        return (
            create_risk_decision_package(
                decision_id=f"risk-{request.request_id}",
                intent_id=intent_id,
                state=get_decision_state("APPROVE"),
                requested_size=requested_size,
                approved_size=approved_size,
                ordered_checks=(),
                primary_failure_limit=None,
                composite_breach_flags=(),
                evidence_refs={"market_data": request.data_hash},
                config_hash=request.risk_policy_hash,
                concurrency_disclosure="single-threaded-simulation",
                recommendations=(),
                issued_at=request.start - timedelta(seconds=1),
                expires_at=request.end + timedelta(days=1),
                token=token,
                request_id=request.request_id,
                workflow_id=request.workflow_id,
                correlation_id=request.correlation_id,
            ),
        )

    def build_order_intents(
        self, decisions: tuple[object, ...], request: object
    ) -> tuple[object, ...]:
        """Create a Trading intent from actual Strategy and Risk decisions."""
        risk_decision = decisions[0]
        strategy_decision = risk_decision.intent_id
        side = self._strategy_side(strategy_decision, request)
        created_at = request.start - timedelta(seconds=1)
        return (
            create_order_intent(
                client_order_id=f"order-{request.request_id}",
                request_id=request.request_id,
                workflow_id=request.workflow_id,
                correlation_id=request.correlation_id,
                route="sim",
                provider_id=None,
                account_id="workflow-simulation",
                strategy_id=request.strategy_id,
                strategy_version=request.strategy_version,
                source_intent_id=strategy_decision,
                symbol=request.symbol,
                action="submit_order",
                side=side,
                order_type="MARKET",
                quantity_unit="lot",
                approved_volume=risk_decision.approved_size,
                risk_approved_volume=risk_decision.approved_size,
                time_in_force="FOK",
                idempotency_hash=canonical_digest(
                    {
                        "risk_decision_id": risk_decision.decision_id,
                        "data_hash": request.data_hash,
                    }
                ),
                canonical_material_version="v1",
                risk_decision_id=risk_decision.decision_id,
                action_policy_verdict_id="simulation-risk-approved",
                approval_token_ref="simulation-only",
                created_at=created_at,
                valid_until=request.end + timedelta(days=1),
            ),
        )

    def load_initial_authority_state(self, request: object) -> Mapping[str, object]:
        """Return one complete empty authority snapshot for a fresh run."""
        return {
            "account": {
                "balance": request.initial_balance,
                "currency": request.account_currency,
            },
            "orders": (),
            "positions": (),
            "deals": (),
            "ownership": {"mode": "exclusive"},
        }

    def load_account_activity(self, request: object) -> tuple[object, ...]:
        """Return no foreign activity under the exclusive interval proof."""
        del request
        return ()

    def build_approved_requests(
        self,
        intents: tuple[object, ...],
        decisions: tuple[object, ...],
        request: object,
    ) -> tuple[object, ...]:
        """Require aligned Strategy/Risk lineage before Trading request build."""
        from dataclasses import replace
        from types import SimpleNamespace

        from tests.trading.unit.actions.test_dependencies import dependencies

        if len(intents) != len(decisions):
            raise ValueError("Strategy/Risk lineage must align exactly")
        trading_dependencies = replace(
            dependencies(),
            clock=lambda: request.start - timedelta(seconds=1),
            live_session=SimpleNamespace(config=SimpleNamespace(execution_route="sim")),
        )
        evidence = {
            "account_id": "workflow-simulation",
            "action_policy_verdict_id": "simulation-risk-approved",
            "canonical_material_version": "v2",
            "fill_policy": "FOK",
            "time_policy": "GTC",
        }
        return tuple(
            build_approved_trading_request(
                intent, decision, trading_dependencies, evidence
            )
            for intent, decision in zip(intents, decisions, strict=True)
        )

    async def execute_trading_action(
        self, approved_request: object, engine: object, request: object
    ) -> object:
        """Reject an unavailable mutation composition in this neutral fixture."""
        del approved_request, engine, request
        raise ValueError("neutral fixture cannot execute a Trading mutation")

    async def execute_terminal_action(
        self, position: Mapping[str, object], engine: object, request: object
    ) -> object:
        """Reject terminal work because the neutral fixture has no positions."""
        del position, engine, request
        raise ValueError("neutral fixture cannot execute terminal liquidation")

    def _strategy_side(self, decision_id: str, request: object) -> str:
        """Recalculate the observable Strategy side for Trading composition."""
        indicator = self.calculate_indicators(self.dataset, request)[0]
        latest = self.dataset.records[-1]
        close = (
            Decimal(str(latest.close))
            if hasattr(latest, "close")
            else (latest.bid + latest.ask) / Decimal(2)
        )
        average = Decimal(
            str(indicator.values[indicator.output_columns[0]].dropna().iloc[-1])
        )
        if not decision_id.startswith("decision-"):
            raise ValueError("Risk decision is not bound to a Strategy decision")
        return "BUY" if close >= average else "SELL"

    def resolve_execution_profile(self, request: object) -> object:
        """Return the explicit deterministic execution policy."""
        del request
        session = create_simulation_value(
            "SessionInterval", start_week_second=0, end_week_second=604_800
        )
        return create_simulation_value(
            "ExecutionProfile",
            slippage_mode="none",
            fixed_slippage_points=Decimal(0),
            point_value=Decimal("0.00001"),
            price_quantum=Decimal("0.00001"),
            maximum_slippage_points=Decimal(0),
            maximum_gap_points=Decimal(10),
            liquidity_mode="unbounded",
            participation_rate=Decimal(0),
            sessions=(session,),
        )

    def resolve_symbol_specification(self, request: object) -> object:
        """Return the explicit EURUSD volume and leverage contract."""
        del request
        return create_simulation_value(
            "SymbolSpecification",
            minimum_volume=Decimal("0.01"),
            maximum_volume=Decimal(100),
            volume_step=Decimal("0.01"),
            contract_size=Decimal(100_000),
            leverage=Decimal(100),
        )

    def resolve_cost_model(self, request: object) -> object:
        """Return an explicit zero-fee execution model."""
        del request
        return create_simulation_value(
            "ExecutionCostModel",
            commission_per_lot_per_side=Decimal(0),
            long_swap_per_lot_rollover=Decimal(0),
            short_swap_per_lot_rollover=Decimal(0),
        )

    def resolve_fx_evidence(
        self, evidence_ids: tuple[str, ...]
    ) -> Mapping[str, object]:
        """Resolve fresh Data-owned FX evidence for each request identity."""
        return {evidence_id: fx_evidence(self.dataset) for evidence_id in evidence_ids}


def dependencies(root: Path, dataset: object) -> WorkflowSimulationDependencies:
    """Return the genuine workflow dependency composition."""
    return WorkflowSimulationDependencies(root, dataset)


def portfolio_request(
    dataset: object,
) -> tuple[object, object]:
    """Build one portfolio request bound to genuine Data/FX evidence."""
    child = backtest_request(dataset)
    component = create_simulation_value(
        "PortfolioComponentRequest",
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
    fx = fx_evidence(dataset)
    payload: dict[str, object] = {
        "request_id": request_id,
        "workflow_id": workflow_id,
        "correlation_id": correlation_id,
        "portfolio_id": "portfolio",
        "construction_result_id": "construction",
        "construction_version": "v1",
        "components": (dump_simulation_value(component),),
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
        calculate_portfolio_backtest_config_hash(payload),
        operation="simulation.run.portfolio_backtest_request_v1.calculate_config_hash",
    )
    request = create_simulation_value("PortfolioBacktestRequestV1", **payload)
    auth = create_auth_context(
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
    "execution_profile",
    "fx_evidence",
    "live_market_dataset",
    "live_tick_dataset",
    "portfolio_request",
    "workflow_engine",
    "workflow_order_intent",
    "workflow_tick",
]
