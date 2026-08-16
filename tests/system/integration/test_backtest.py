"""Genuine SYS-WF-001 Data-to-Analytics backtest workflow evidence."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.services.analytics import build_performance_report
from app.services.data import (
    build_data_quality_report,
    build_market_dataset,
    build_ohlcv_record,
    generate_tick_series,
    unwrap_data_response,
)
from app.services.indicators import get_indicator_result_metadata, sma
from app.services.risk import get_decision_state
from app.services.simulator import run_backtest_async, unwrap_simulation_response
from app.services.strategy import (
    build_trade_intent,
    create_strategy_decision,
    create_strategy_evaluator,
    create_strategy_execution_context,
    create_validated_strategy_ref,
    evaluate_strategy_signals,
    get_strategy_environment,
    get_strategy_timing_policy,
)
from app.services.trading import (
    build_execution_plan,
    create_readiness_assessment,
    create_trading_request,
)

from tests.analytics import _support as analytics_examples
from tests.indicators.helpers import unwrap_response
from tests.risk import _support as risk_examples
from tests.simulator.component.test_orchestrator import (
    FakeDependencies,
    _auth,
    _request,
)
from tests.strategy.unit.test_models import (
    HASH,
    make_ref,
    make_signal_config,
    make_signal_evidence,
)

OrderIntent = Any
MarketDataset = Any
PerformanceReport = Any
SimulationBacktestRequest = Any
SimulationResult = Any
StrategyTradeIntent = Any

# Private type-only aliases; Risk exposes functions, not contract classes.
ProposedTrade = object
RiskDecisionPackage = object


def _bar_dataset() -> MarketDataset:
    """Build real-bound OHLC evidence whose second bar crosses a stop.

    Returns:
        Canonical two-bar Data dataset.
    """
    start = risk_examples.NOW
    prices = (
        (
            Decimal("1.1000"),
            Decimal("1.1010"),
            Decimal("1.0990"),
            Decimal("1.1000"),
        ),
        (
            Decimal("1.1000"),
            Decimal("1.1005"),
            Decimal("1.0800"),
            Decimal("1.0850"),
        ),
    )
    records = tuple(
        build_ohlcv_record(
            timestamp=start + timedelta(seconds=index * 10),
            source="system-workflow-fixture",
            source_symbol="EURUSD",
            available_at=start + timedelta(seconds=index * 10),
            open=open_price,
            high=high,
            low=low,
            close=close,
            volume=Decimal(4),
            price_unit="quote",
            volume_unit="tick",
        )
        for index, (open_price, high, low, close) in enumerate(prices)
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
        source_metadata={"tick_generation_model": "trading_bar"},
        license_metadata={"license": "system-test"},
        cache_status="not_used",
        workflow_context="backtest",
        precision_policy="decimal_string",
        request_id="req-12121212-1212-4121-8121-121212121212",
    )


def _ticks(dataset: MarketDataset) -> MarketDataset:
    """Generate deterministic real-bound ticks through the Data public API.

    Args:
        dataset: Source OHLC evidence.

    Returns:
        Canonical Data-owned tick series.
    """
    return unwrap_data_response(
        generate_tick_series(
            dataset,
            model="trading_bar",
            trading_timeframe="M1",
            spread_model="fixed_spread",
            fixed_spread_points=Decimal(2),
            max_records=100,
            request_id=dataset.request_id,
        ),
        operation="generate_tick_series",
        request_id=dataset.request_id,
    )


def _unwrap_response(response: Any) -> Any:
    """Return data from one successful standard response."""
    assert response.status == "success", response.error
    assert response.data is not None
    return response.data


class _SystemBacktestDependencies(FakeDependencies):
    """Compose genuine domain operations behind Simulation's public seam."""

    def __init__(
        self,
        tmp_path: Path,
        bars: MarketDataset,
        ticks: MarketDataset,
    ) -> None:
        """Initialize isolated state and source evidence.

        Args:
            tmp_path: Isolated test root.
            bars: Source OHLC evidence.
            ticks: Expected Data-generated tick evidence.
        """
        super().__init__(tmp_path, ticks)
        self.bars = bars
        self.ticks = ticks
        self.calls: list[str] = []
        self.trade_intent: StrategyTradeIntent | None = None

    def load_market_data(self, request: SimulationBacktestRequest) -> MarketDataset:
        """Load the referenced Data evidence."""
        del request
        self.calls.append("data")
        return self.bars

    def generate_tick_series(
        self,
        dataset: MarketDataset,
        request: SimulationBacktestRequest,
    ) -> MarketDataset:
        """Invoke Data's genuine tick derivation operation."""
        del request
        self.calls.append("data.tick_derivation")
        generated = _ticks(dataset)
        assert generated == self.ticks
        return generated

    def calculate_indicators(
        self,
        dataset: MarketDataset,
        request: SimulationBacktestRequest,
    ) -> tuple[Any, ...]:
        """Invoke the Indicators package-root SMA operation."""
        del request
        self.calls.append("indicators")
        return (unwrap_response(sma(dataset, period=2)),)

    def evaluate_strategy(
        self,
        dataset: MarketDataset,
        indicators: tuple[Any, ...],
        request: SimulationBacktestRequest,
    ) -> tuple[StrategyTradeIntent, ...]:
        """Evaluate a registered Strategy and build its proposal intent."""
        self.calls.append("strategy")
        assert get_indicator_result_metadata(indicators[0])["indicator_id"] == "sma"
        base_ref = make_ref()
        manifest = base_ref.manifest.model_copy(
            update={"permitted_environments": (get_strategy_environment("SIMULATION"),)}
        )
        ref = create_validated_strategy_ref(
            manifest=manifest,
            lifecycle_status=base_ref.lifecycle_status,
            environment=get_strategy_environment("SIMULATION"),
            policy_version=base_ref.policy_version,
            validation_policy=base_ref.validation_policy,
            registry_record_hash=base_ref.registry_record_hash,
            request_id=base_ref.request_id,
            correlation_id=base_ref.correlation_id,
        )
        config = make_signal_config({"buy_magic_number": 10, "sell_magic_number": 20})
        context = create_strategy_execution_context(
            environment=get_strategy_environment("SIMULATION"),
            decision_timestamp=dataset.available_at,
            timing_policy=get_strategy_timing_policy("EVENT_DRIVEN"),
            seed=request.seed,
            interface_version="v1",
            request_id=risk_examples.REQUEST_ID,
            workflow_id=risk_examples.WORKFLOW_ID,
            correlation_id=risk_examples.CORRELATION_ID,
            dependency_status={"data": "ready", "indicators": "ready"},
            snapshot_refs=(request.data_ref,),
            max_diagnostic_bytes=8_192,
        )
        evaluator = create_strategy_evaluator(
            "random_walk",
            strategy_id=manifest.strategy_id,
            strategy_version=manifest.strategy_version,
            module_path=manifest.module_path,
            source_hash=HASH,
            artifact_hash=HASH,
            dependency_hash=HASH,
        )
        signal_outcome = evaluate_strategy_signals(
            ref,
            config,
            make_signal_evidence(dataset),
            (),
            context,
            evaluator,
        )
        assert signal_outcome.status == "success", signal_outcome.error
        assert signal_outcome.data is not None
        signal = next(
            item for item in signal_outcome.data if item.active and item.side == "BUY"
        )
        decision = create_strategy_decision(
            decision_id="sys-wf-001-decision",
            sequence=0,
            action="PROPOSE",
            symbol=signal.symbol,
            side=signal.side,
            intent_type="OPEN",
            order_type="MARKET",
            time_in_force="FOK",
            requested_sizing_mode="quantity",
            quantity_hint=Decimal("0.01"),
            valid_from=signal.timestamp,
            expires_at=request.end + timedelta(seconds=20),
            stop_loss=Decimal("1.0950"),
            allow_partial_fills=False,
            rationale_refs=(signal.signal_id, indicators[0].indicator_id),
            diagnostic_facts={
                "indicator_status": "ready",
                "strategy_signal": signal.signal_name,
            },
            lineage={
                "strategy_id": "sys-wf-001",
                "strategy_version": "v1",
                "config_hash": request.strategy_config_hash,
            },
        )
        outcome = build_trade_intent(decision, context, 0)
        assert outcome.status == "success", outcome.error
        assert outcome.data is not None
        self.trade_intent = outcome.data
        return (outcome.data,)

    def review_risk(
        self,
        intents: tuple[StrategyTradeIntent, ...],
        request: SimulationBacktestRequest,
    ) -> tuple[RiskDecisionPackage, ...]:
        """Review the exact Strategy proposal through RiskGovernor."""
        del request
        self.calls.append("risk")
        config = risk_examples._config()
        proposal = risk_examples._proposal(config).model_copy(
            update={
                "intent": intents[0],
                "requested_size": Decimal("0.01"),
                "current_price": Decimal("1.1000"),
                "stop_distance": Decimal("0.0050"),
            }
        )
        assert proposal.schema_id == "risk.proposed_trade.v1"
        governor, _, _ = risk_examples._services(config)
        decision = risk_examples.unwrap_risk_response(
            governor.review_trade_risk(
                proposal,
                risk_examples._snapshot_governor(config),
                risk_examples._market(),
                risk_examples._regime(),
                (risk_examples._inactive_state(),),
                risk_examples._auth(config),
                attestation=risk_examples._attestation(config),
                now=risk_examples.NOW,
            ),
            operation="review_trade_risk",
        )
        assert decision.state is get_decision_state("APPROVE")
        return (decision,)

    def build_order_intents(
        self,
        decisions: tuple[RiskDecisionPackage, ...],
        request: SimulationBacktestRequest,
    ) -> tuple[OrderIntent, ...]:
        """Package Risk-approved size through Trading's public API."""
        self.calls.append("trading")
        decision = decisions[0]
        intent = self.trade_intent
        assert intent is not None
        assert decision.approved_size is not None
        assert decision.token is not None
        trading_request = create_trading_request(
            request_id=decision.request_id,
            workflow_id=decision.workflow_id,
            correlation_id=decision.correlation_id,
            route="sim",
            action="submit_order",
            account_id="account-1",
            strategy_id=intent.strategy_id,
            strategy_version=intent.strategy_version,
            intent_id=intent.intent_id,
            symbol=intent.symbol,
            side=intent.side,
            order_type=intent.order_type,
            quantity_unit="lot",
            quantity=decision.approved_size,
            stop_loss=intent.stop_loss,
            time_in_force=intent.time_in_force,
            risk_decision_id=decision.decision_id,
            action_policy_verdict_id="sys-wf-001-policy",
            approval_token_ref=decision.token.token_id,
            idempotency_key=intent.idempotency_key,
            canonical_material_version="v1",
            system_time=request.start,
            valid_until=decision.expires_at,
            instrument_min_quantity=Decimal("0.01"),
            instrument_max_quantity=Decimal(100),
            instrument_quantity_step=Decimal("0.01"),
            instrument_price_tick=Decimal("0.00001"),
        )
        readiness = create_readiness_assessment(
            passed=True,
            failed_check_codes=(),
            evidence_refs={"risk": decision.decision_id},
            assessed_at=request.start,
        )
        return (_unwrap_response(build_execution_plan(trading_request, readiness)),)


def _analytics_report(
    result: SimulationResult,
    request: SimulationBacktestRequest,
) -> Any:
    """Build Analytics evidence from the completed Simulation ledger.

    Args:
        result: Completed Simulation result.
        request: Source Simulation request.

    Returns:
        Completed Analytics performance report.
    """
    source = {
        "contract_version": result.contract_version,
        "schema_id": result.schema_id,
        "source_id": result.run_id,
        "phase": "backtest",
        "window_start": request.start,
        "window_end": request.end,
        "strategy_id": request.strategy_id,
        "strategy_version": request.strategy_version,
        "symbols": (request.symbol,),
        "timeframe": request.timeframe,
        "closed_trades": tuple(
            item.model_dump(mode="python") for item in result.closed_trades
        ),
        "quality_metadata": {"status": "passed"},
        "source_metadata": {"request_hash": result.request_hash},
    }
    return build_performance_report(
        source,
        source_contract="simulation.result",
        request_id=request.request_id,
        correlation_id=request.correlation_id,
        created_at=request.end,
        initial_balance=result.initial_balance,
        account_currency=result.account_currency,
        config=analytics_examples._configured(),
        diagnostic_partial_mode=True,
    )


def test_sys_wf_001_neutral_backtest_reaches_analytics_fail_closed(
    tmp_path: Path,
) -> None:
    """Execute canonical neutral evidence without inventing Analytics trades."""
    bars = _bar_dataset()
    ticks = _ticks(bars)
    request = _request(ticks, suffix="2")
    dependencies = _SystemBacktestDependencies(tmp_path, bars, ticks)

    result = unwrap_simulation_response(
        asyncio.run(run_backtest_async(request, _auth(request), dependencies)),
        operation="run_backtest",
    )
    report = _analytics_report(result, request)

    assert result.status == "completed"
    assert not result.closed_trades
    assert report.status == "error"
    assert report.error is not None
    assert report.error.code == "ANALYTICS_VALIDATION_FAILED"
    assert dependencies.calls == ["data", "data.tick_derivation"]
