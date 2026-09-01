"""Direct, copyable usage catalogue demonstrating Simulator domain workflows using real MT5 data.

Example 1: Simulation Mode & Policy Configuration
Example 2: Fast Research Simulation (with real MT5 EURUSD H1 data)
Example 3: Official Single-Asset Backtest Run & Result Inspection
Example 4: Realistic Execution Pricing & Execution Cost Modeling
Example 5: Portfolio Backtest Simulation & Component Allocations
Example 6: Simulation Reporting Schemas & Canonical Artifact Types
Example 7: Full EURUSD H1 Naive MA Trend Backtest & Performance Report
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import inspect
import logging
import sys
import tempfile
import time
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

# Bootstrap project root to sys.path if not present
_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from app.composition.config import load_broker_provider_settings
from app.contracts.common.models import create_auth_context
from app.kernel.identity import generate_id
from app.kernel.serialization import canonical_digest, canonical_json
from app.services.analytics import (
    build_performance_report,
    create_analytics_value,
    get_analytics_value_field,
)
from app.services.brokers import (
    connect_broker,
    create_broker_adapter,
    disconnect_broker,
    dump_provider_specification_snapshot,
    get_broker_account_info,
    get_broker_provider_specification,
)
from app.services.data import (
    build_data_quality_report,
    build_fx_conversion_evidence,
    build_fx_rate_leg,
    build_market_data_request,
    build_market_dataset,
    build_ohlcv_record,
    data_provider_connection_resolver_context,
    data_provider_settings_context,
    generate_tick_series,
    get_market_data,
    unwrap_data_response,
)
from app.services.simulator import (
    build_latency_profile,
    calculate_execution_costs,
    calculate_fast_research_config_hash,
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
    run_backtest_async,
    run_fast_research,
    run_portfolio_backtest,
    unwrap_simulation_response,
)
from app.services.strategy import (
    create_strategy_evaluator,
    create_strategy_execution_context,
    create_strategy_manifest,
    create_strategy_validation_policy,
    create_validated_strategy_config,
    create_validated_strategy_ref,
    get_strategy_environment,
    get_strategy_lifecycle_status,
    get_strategy_timing_policy,
)
from app.services.trading import create_order_intent

from tests.simulator._fixtures.sqlite_store import SqliteSimulationStateStore

_START = datetime(2026, 8, 1, tzinfo=UTC)
_END = _START + timedelta(hours=1000)
SYMBOL = "EURUSD"
TIMEFRAME = "H1"
BAR_LIMIT = 100
BACKTEST_WARMUP_START = datetime(2024, 12, 1, tzinfo=UTC)
BACKTEST_START = datetime(2025, 1, 1, tzinfo=UTC)
BACKTEST_END = datetime(2025, 12, 31, 23, 59, 59, tzinfo=UTC)
BACKTEST_BAR_LIMIT = 10_000
BACKTEST_INITIAL_BALANCE = Decimal("10000.00")
BACKTEST_VOLUME = Decimal("0.1")
BACKTEST_FAST_MA = 20
BACKTEST_SLOW_MA = 50
BACKTEST_FILTER_MA = 200
_PROVIDER_FIELDS = {
    "MT5_ENABLED": "mt5_enabled",
    "MT5_TERMINAL_PATH": "mt5_terminal_path",
}
_NAIVE_TREND_MODULE = "app.services.strategy.evaluators.naive_ma_trend_incremental"
_NAIVE_TREND_EVALUATOR = "naive_ma_trend_incremental"


@dataclass(frozen=True, slots=True)
class _ProviderFacts:
    """Current read-only MT5 demo facts used by the simulation experiment."""

    specification: Mapping[str, object]
    leverage: Decimal
    account_currency: str


_ACTIVE_PROVIDER_FACTS: list[_ProviderFacts] = []


def _required_decimal(source: Mapping[str, object], field: str) -> Decimal:
    """Return one required positive provider decimal or fail closed."""
    if field not in source:
        raise RuntimeError(f"MT5 provider specification omitted {field}")
    value = Decimal(str(source[field]))
    if not value.is_finite() or value <= 0:
        raise RuntimeError(f"MT5 provider specification has invalid {field}")
    return value


def _provider_facts_from_responses(
    specification_response: object, account_response: object
) -> _ProviderFacts:
    """Validate provider responses and return fail-closed runtime facts."""
    if specification_response.error is not None or specification_response.data is None:
        raise RuntimeError("MT5 provider specification retrieval failed")
    if account_response.error is not None or account_response.data is None:
        raise RuntimeError("MT5 account specification retrieval failed")
    specification = dump_provider_specification_snapshot(specification_response.data)
    details = account_response.data.details
    if "leverage" not in details:
        raise RuntimeError("MT5 account information omitted leverage")
    leverage = Decimal(str(details["leverage"]))
    if not leverage.is_finite() or leverage <= 0:
        raise RuntimeError("MT5 account information has invalid leverage")
    return _ProviderFacts(specification, leverage, str(account_response.data.currency))


def _swap_cash_effect(facts: _ProviderFacts, field: str) -> Decimal:
    """Convert a signed MT5 point swap into account-currency cash per lot."""
    specification = facts.specification
    if specification.get("swap_mode") != "POINTS":
        raise RuntimeError("annual example requires MT5 POINTS swap evidence")
    if specification.get("profit_currency") != facts.account_currency:
        raise RuntimeError("swap conversion requires matching profit/account currency")
    rate = Decimal(str(specification[field]))
    if not rate.is_finite():
        raise RuntimeError(f"MT5 provider specification has invalid {field}")
    return (
        rate
        * _required_decimal(specification, "point")
        * _required_decimal(specification, "contract_size")
    )


def _dataset_hash(dataset: object) -> str:
    """Return the canonical digest of a Data-owned dataset."""
    return canonical_digest(dataset.model_dump(mode="python", warnings=False))


def authority(request: object) -> object:
    """Build simulation-only authority aligned with a request."""
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


def fx_evidence(dataset: object) -> object:
    """Build direct EUR/USD conversion evidence from observed market data."""
    observation = dataset.records[-1]
    rate = observation.close if hasattr(observation, "close") else observation.ask
    leg = build_fx_rate_leg(
        source_currency="EUR",
        target_currency="USD",
        rate=rate,
        source_id="mt5",
        provider_symbol=dataset.symbol,
        as_of=dataset.end,
        provenance={"provider": "mt5", "dataset_hash": _dataset_hash(dataset)},
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
        provenance={"provider": "mt5", "dataset_hash": _dataset_hash(dataset)},
        request_id=dataset.request_id,
    )


def live_tick_dataset() -> object:
    """Build a bounded canonical tick dataset for catalogue examples."""
    dataset = _get_dataset(timeframe="M1", limit=20)
    if dataset is None:
        base = datetime(2026, 1, 1, tzinfo=UTC)
        records = tuple(
            build_ohlcv_record(
                timestamp=base + timedelta(minutes=index),
                open=Decimal("1.085") + Decimal(index) * Decimal("0.0001"),
                high=Decimal("1.086") + Decimal(index) * Decimal("0.0001"),
                low=Decimal("1.0845") + Decimal(index) * Decimal("0.0001"),
                close=Decimal("1.0855") + Decimal(index) * Decimal("0.0001"),
                volume=Decimal(100),
                available_at=base + timedelta(minutes=index + 1),
                source="fixture",
                source_symbol=SYMBOL,
                price_unit="quote_currency",
                volume_unit="ticks",
            )
            for index in range(20)
        )
        dataset = build_market_dataset(
            normalization_version="v1",
            data_kind="bars",
            symbol=SYMBOL,
            timeframe="M1",
            records=records,
            start=records[0].timestamp,
            end=records[-1].timestamp,
            available_at=records[-1].available_at,
            record_count=len(records),
            quality_report=build_data_quality_report(
                quality_status="perfect",
                quality_decision="accepted",
                quality_score=Decimal(100),
                record_count=len(records),
                checked_count=len(records),
                truncated=False,
                sample_limit=len(records),
                schema_version="v1",
                generated_at=records[-1].available_at,
            ),
            source_metadata={"source_id": "fixture"},
            license_metadata={"license": "synthetic_test"},
            cache_status="not_used",
            workflow_context="research",
            precision_policy="decimal_string",
            request_id=generate_id("req"),
        )
    generated = generate_tick_series(
        dataset,
        model="trading_bar",
        trading_timeframe="M1",
        spread_model="fixed_spread",
        fixed_spread_points=Decimal(2),
        point_value=Decimal("0.00001"),
    )
    return unwrap_data_response(
        generated,
        operation="legacy.live_tick_dataset",
        request_id=dataset.request_id,
    )


class _SimulationDependencies:
    """Self-contained composition for the legacy Simulator catalogue."""

    fast_research_enabled = True

    def __init__(self, root: Path, dataset: object) -> None:
        self.artifact_root = root / "artifacts"
        self.artifact_root.mkdir(parents=True, exist_ok=True)
        self.state_store = SqliteSimulationStateStore(
            root / "state.db", self.artifact_root
        )
        self.dataset = dataset
        self.audit_path = root / "audit.jsonl"
        self._tick_dataset: object | None = None

    def persist_audit_event(self, event: object) -> None:
        """Append one canonical audit event to isolated state."""
        with self.audit_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(
                canonical_json(event.model_dump(mode="python", warnings=False))
            )
            stream.write("\n")

    def load_market_data(self, request: object) -> object:
        """Return the caller-supplied market evidence."""
        del request
        return self.dataset

    def generate_tick_series(self, dataset: object, request: object) -> object:
        """Generate or reuse the exact canonical tick stream."""
        if self._tick_dataset is None:
            if dataset.data_kind == "ticks":
                self._tick_dataset = dataset
            else:
                generated = generate_tick_series(
                    dataset,
                    model="trading_bar",
                    trading_timeframe=request.timeframe,
                    spread_model="fixed_spread",
                    fixed_spread_points=Decimal(10),
                    point_value=Decimal("0.00001"),
                )
                self._tick_dataset = unwrap_data_response(
                    generated,
                    operation="legacy.dependencies.generate_tick_series",
                    request_id=dataset.request_id,
                )
        return self._tick_dataset

    async def evaluate_point_in_time_cycle(
        self, dataset: object, decision_at: object, engine: object, request: object
    ) -> object:
        """Return a neutral point-in-time cycle for general examples."""
        del engine, request
        if any(record.available_at > decision_at for record in dataset.records):
            raise ValueError("future evidence reached the evaluation cycle")
        return {"mutation_performed": False}

    def load_initial_authority_state(self, request: object) -> Mapping[str, object]:
        """Return a complete empty initial authority snapshot."""
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
        """Return no foreign account activity."""
        del request
        return ()

    def load_provider_specification_revisions(
        self, request: object
    ) -> Mapping[str, object]:
        """Return complete request-bound demo specification evidence."""
        binding = request.provider_specification_revisions[0]
        return {
            "complete_coverage": True,
            "revisions": (
                {
                    "revision_id": binding.revision_id,
                    "broker": binding.provider,
                    "server": binding.server,
                    "environment": binding.environment,
                    "account_digest": binding.account_digest,
                    "provider_symbol": binding.symbol,
                    "snapshot_checksum": binding.checksum,
                    "effective_from": binding.effective_from,
                    "effective_to": binding.effective_to,
                    "payload": {
                        "filling_modes": ("FOK", "IOC", "RETURN"),
                        "execution_mode": "MARKET",
                        "trade_mode": "FULL",
                        "stops_level_points": 0,
                        "freeze_level_points": 0,
                        "directional_volume_limit": "100",
                        "point": "0.00001",
                        "weekly_sessions": {
                            str(day): (("00:00:00", "23:59:59.999999"),)
                            for day in range(7)
                        },
                        "dated_exceptions": {},
                        "exception_coverage": (),
                        "exception_coverage_required": False,
                    },
                },
            ),
        }

    def resolve_execution_profile(self, request: object) -> object:
        """Return fixed one-point adverse slippage execution."""
        del request
        session = create_simulation_value(
            "SessionInterval", start_week_second=0, end_week_second=604_800
        )
        return create_simulation_value(
            "ExecutionProfile",
            slippage_mode="fixed_points",
            fixed_slippage_points=Decimal(1),
            point_value=Decimal("0.00001"),
            price_quantum=Decimal("0.00001"),
            maximum_slippage_points=Decimal(1),
            maximum_gap_points=Decimal(10),
            liquidity_mode="unbounded",
            participation_rate=Decimal(0),
            sessions=(session,),
        )

    def resolve_symbol_specification(self, request: object) -> object:
        """Return the explicit EURUSD contract specification."""
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
        """Return the parity commission and zero swap model."""
        del request
        return create_simulation_value(
            "ExecutionCostModel",
            commission_per_lot_per_side=Decimal(7),
            long_swap_per_lot_rollover=Decimal(0),
            short_swap_per_lot_rollover=Decimal(0),
        )

    def resolve_fx_evidence(
        self, evidence_ids: tuple[str, ...]
    ) -> Mapping[str, object]:
        """Resolve direct conversion evidence for portfolio examples."""
        return {evidence_id: fx_evidence(self.dataset) for evidence_id in evidence_ids}

    async def execute_trading_action(
        self, approved_request: object, engine: object, request: object
    ) -> object:
        """Reject mutation from the neutral general-example composition."""
        del approved_request, engine, request
        raise ValueError("neutral example cannot execute a Trading mutation")

    async def execute_terminal_action(
        self, position: Mapping[str, object], engine: object, request: object
    ) -> object:
        """Reject impossible terminal work in the neutral composition."""
        del position, engine, request
        raise ValueError("neutral example has no positions")


def dependencies(root: Path, dataset: object) -> _SimulationDependencies:
    """Build the self-contained general-example composition."""
    return _SimulationDependencies(root, dataset)


class _NaiveTrendDependencies(_SimulationDependencies):
    """Evaluate the registered naive MA strategy through Simulation authority."""

    def __init__(self, root: Path, dataset: object, tick_dataset: object) -> None:
        super().__init__(root, dataset)
        self._tick_dataset = tick_dataset
        self._last_bar_available_at: datetime | None = None
        self._sequence = 0
        self._strategy_request_id: str | None = None
        self._strategy_ref: object | None = None
        self._strategy_config: object | None = None
        self._strategy_evaluator: object | None = None
        parameters = {
            "fast_ma_period": BACKTEST_FAST_MA,
            "slow_ma_period": BACKTEST_SLOW_MA,
            "filter_ma_period": BACKTEST_FILTER_MA,
        }
        probe = create_strategy_evaluator(
            _NAIVE_TREND_EVALUATOR,
            strategy_id="naive-ma-trend",
            strategy_version="1.0.0",
            module_path=_NAIVE_TREND_MODULE,
            source_hash="0" * 64,
            artifact_hash="0" * 64,
            dependency_hash="0" * 64,
        )
        self._source_hash = hashlib.sha256(
            inspect.getsource(type(probe)).encode()
        ).hexdigest()
        self._parameters = parameters
        self._config_hash = canonical_digest(parameters)
        self._policy = create_strategy_validation_policy(
            policy_version="legacy-backtest-v1",
            approved_module_roots=("app.services.strategy.evaluators",),
            max_config_payload_bytes=4_096,
            max_config_nesting_depth=8,
            max_config_string_length=128,
            max_config_collection_items=64,
        )

    @staticmethod
    def _provider_facts() -> _ProviderFacts:
        """Return verified MT5 facts bound by the runtime context."""
        if not _ACTIVE_PROVIDER_FACTS:
            raise RuntimeError("verified MT5 provider facts are unavailable")
        return _ACTIVE_PROVIDER_FACTS[0]

    def load_provider_specification_revisions(
        self, request: object
    ) -> Mapping[str, object]:
        """Return current MT5 facts with tick-evidence session provenance."""
        binding = request.provider_specification_revisions[0]
        specification = self._provider_facts().specification
        return {
            "complete_coverage": True,
            "revisions": (
                {
                    "revision_id": binding.revision_id,
                    "broker": binding.provider,
                    "server": binding.server,
                    "environment": binding.environment,
                    "account_digest": binding.account_digest,
                    "provider_symbol": binding.symbol,
                    "snapshot_checksum": specification["checksum"],
                    "effective_from": binding.effective_from,
                    "effective_to": binding.effective_to,
                    "payload": {
                        "filling_modes": tuple(specification["filling_modes"]),
                        "execution_mode": specification["execution_mode"],
                        "trade_mode": specification["trade_mode"],
                        "stops_level_points": specification["stops_level_points"],
                        "freeze_level_points": specification["freeze_level_points"],
                        "directional_volume_limit": specification[
                            "directional_volume_limit"
                        ],
                        "point": specification["point"],
                        # MT5 exposes no historical session API. Exact generated
                        # ticks are the executable-instant evidence for this run.
                        "weekly_sessions": {
                            str(day): (("00:00:00", "23:59:59.999999"),)
                            for day in range(7)
                        },
                        "dated_exceptions": {},
                        "exception_coverage": (),
                        "exception_coverage_required": False,
                        "session_evidence": "exact_generated_tick_dataset",
                    },
                },
            ),
        }

    def resolve_execution_profile(self, request: object) -> object:
        """Build experiment pricing from MT5 point and tick-size facts."""
        del request
        specification = self._provider_facts().specification
        session = create_simulation_value(
            "SessionInterval", start_week_second=0, end_week_second=604_800
        )
        return create_simulation_value(
            "ExecutionProfile",
            slippage_mode="fixed_points",
            fixed_slippage_points=Decimal(1),
            point_value=_required_decimal(specification, "point"),
            price_quantum=_required_decimal(specification, "tick_size"),
            maximum_slippage_points=Decimal(1),
            maximum_gap_points=Decimal(10),
            liquidity_mode="unbounded",
            participation_rate=Decimal(0),
            sessions=(session,),
        )

    def resolve_symbol_specification(self, request: object) -> object:
        """Build Simulation constraints solely from current MT5 facts."""
        del request
        facts = self._provider_facts()
        specification = facts.specification
        return create_simulation_value(
            "SymbolSpecification",
            minimum_volume=_required_decimal(specification, "volume_min"),
            maximum_volume=_required_decimal(specification, "volume_max"),
            volume_step=_required_decimal(specification, "volume_step"),
            contract_size=_required_decimal(specification, "contract_size"),
            leverage=facts.leverage,
        )

    def resolve_cost_model(self, request: object) -> object:
        """Build explicit experiment costs and provider-observed swap rates."""
        del request
        facts = self._provider_facts()
        return create_simulation_value(
            "ExecutionCostModel",
            commission_per_lot_per_side=Decimal(7),
            long_swap_per_lot_rollover=_swap_cash_effect(facts, "swap_long"),
            short_swap_per_lot_rollover=_swap_cash_effect(facts, "swap_short"),
        )

    def _strategy_binding(
        self, request: object, decision_at: datetime
    ) -> tuple[object, ...]:
        """Return cached validated strategy objects and current context."""
        context = create_strategy_execution_context(
            environment=get_strategy_environment("RESEARCH"),
            decision_timestamp=decision_at,
            timing_policy=get_strategy_timing_policy("BAR_OPEN_PREVIOUS_CLOSE"),
            seed=request.seed,
            interface_version="v1",
            request_id=request.request_id,
            workflow_id=request.workflow_id,
            correlation_id=request.correlation_id,
            dependency_status={"data": "ready", "indicators": "ready"},
            snapshot_refs=(request.data_hash,),
            max_diagnostic_bytes=8_192,
        )
        if self._strategy_request_id != request.request_id:
            manifest = create_strategy_manifest(
                strategy_id="naive-ma-trend",
                strategy_version="1.0.0",
                module_path=_NAIVE_TREND_MODULE,
                owner_ref="legacy-full-backtest",
                interface_version="v1",
                config_schema_version="v1",
                config_schema={"type": "object"},
                required_data=(f"{request.symbol}:{request.timeframe}",),
                required_indicators=(),
                timing_policy=context.timing_policy,
                permitted_environments=(context.environment,),
                source_hash=self._source_hash,
                artifact_hash=self._source_hash,
                dependency_hash=self._source_hash,
                provenance_refs=(request.data_hash,),
                supported_hooks=(),
                requires_account_snapshot=False,
                max_batch_records=10_000,
                max_diagnostic_bytes=8_192,
                max_checkpoint_bytes=8_192,
                max_local_state_bytes=8_192,
                decision_timeout_seconds=5,
            )
            self._strategy_ref = create_validated_strategy_ref(
                manifest=manifest,
                lifecycle_status=get_strategy_lifecycle_status("APPROVED"),
                environment=context.environment,
                policy_version=self._policy.policy_version,
                validation_policy=self._policy,
                registry_record_hash=self._config_hash,
                request_id=request.request_id,
                correlation_id=request.correlation_id,
            )
            self._strategy_config = create_validated_strategy_config(
                strategy_id="naive-ma-trend",
                strategy_version="1.0.0",
                config_schema_version="v1",
                normalized_parameters=self._parameters,
                config_hash=self._config_hash,
                policy_version=self._policy.policy_version,
                request_id=request.request_id,
            )
            self._strategy_evaluator = create_strategy_evaluator(
                _NAIVE_TREND_EVALUATOR,
                strategy_id="naive-ma-trend",
                strategy_version="1.0.0",
                module_path=_NAIVE_TREND_MODULE,
                source_hash=self._source_hash,
                artifact_hash=self._source_hash,
                dependency_hash=self._source_hash,
            )
            self._strategy_request_id = request.request_id
        if (
            self._strategy_ref is None
            or self._strategy_config is None
            or self._strategy_evaluator is None
        ):
            raise ValueError("strategy binding cache is incomplete")
        return (
            self._strategy_ref,
            self._strategy_config,
            self._strategy_evaluator,
            context,
        )

    def generate_tick_series(self, dataset: object, request: object) -> object:
        """Return the pre-generated request-bound annual tick stream."""
        del dataset
        if self._tick_dataset is None or request.data_hash != _dataset_hash(
            self._tick_dataset
        ):
            raise ValueError("request data hash does not match generated ticks")
        return self._tick_dataset

    async def evaluate_point_in_time_cycle(
        self, dataset: object, decision_at: object, engine: object, request: object
    ) -> object:
        """Evaluate every newly visible H1 close without lookahead."""
        latest = dataset.records[-1]
        if latest.available_at > decision_at:
            raise ValueError("future evidence reached the naive trend cycle")
        if (
            len(dataset.records) < BACKTEST_FILTER_MA
            or latest.available_at == self._last_bar_available_at
        ):
            return {"mutation_performed": False}
        self._last_bar_available_at = latest.available_at
        records = dataset.records[-BACKTEST_FILTER_MA:]
        if self._strategy_evaluator is None or self._strategy_config is None:
            self._strategy_binding(request, decision_at)
        evaluator = cast("Any", self._strategy_evaluator)
        config = cast("Any", self._strategy_config)
        active = evaluator._evaluate_compact(records, config)
        snapshot = engine.snapshot_internal()
        positions = snapshot["positions"]
        if positions:
            position = positions[0]
            exit_name = "LONG_EXIT" if position["side"] == "BUY" else "SHORT_EXIT"
            if exit_name in active:
                return await self.execute_trading_action(
                    {"position": position}, engine, request
                )
            return {"mutation_performed": False}
        side = (
            "BUY"
            if "LONG_ENTRY" in active
            else "SELL"
            if "SHORT_ENTRY" in active
            else None
        )
        if side is None:
            return {"mutation_performed": False}
        self._sequence += 1
        filling_modes = tuple(self._provider_facts().specification["filling_modes"])
        if not filling_modes:
            raise RuntimeError("MT5 provider specification has no filling mode")
        intent = create_order_intent(
            client_order_id=f"naive-trend-{self._sequence}",
            request_id=request.request_id,
            workflow_id=request.workflow_id,
            correlation_id=request.correlation_id,
            route="sim",
            provider_id=None,
            account_id="legacy-full-backtest",
            strategy_id="naive-ma-trend",
            strategy_version="1.0.0",
            source_intent_id=f"signal-{self._sequence}",
            symbol=request.symbol,
            action="submit_order",
            side=side,
            order_type="MARKET",
            quantity_unit="lot",
            approved_volume=BACKTEST_VOLUME,
            risk_approved_volume=BACKTEST_VOLUME,
            time_in_force=cast("Any", filling_modes[0]),
            idempotency_hash=canonical_digest(
                {"run": request.request_id, "sequence": self._sequence, "side": side}
            ),
            canonical_material_version="v1",
            risk_decision_id=f"risk-{self._sequence}",
            action_policy_verdict_id="simulation-risk-approved",
            approval_token_ref="simulation-only",
            created_at=decision_at,
            valid_until=request.end + timedelta(days=1),
        )
        return await self.execute_trading_action(intent, engine, request)

    async def execute_trading_action(
        self, approved_request: object, engine: object, request: object
    ) -> object:
        """Submit or close solely through Simulation authority."""
        del request
        if isinstance(approved_request, Mapping):
            position = approved_request["position"]
            return engine.close_position(position["position_id"], position["volume"])
        return engine.submit_order(approved_request)

    async def execute_terminal_action(
        self, position: Mapping[str, object], engine: object, request: object
    ) -> object:
        """Liquidate an open terminal position through Simulation authority."""
        return await self.execute_trading_action(
            {"position": position}, engine, request
        )


def naive_trend_dependencies(
    root: Path, dataset: object, tick_dataset: object
) -> _NaiveTrendDependencies:
    """Build the self-contained registered-strategy composition."""
    return _NaiveTrendDependencies(root, dataset, tick_dataset)


def _header(title: str) -> None:
    """Print a bounded example heading.

    Args:
        title: Human-readable example title.

    Returns:
        None.
    """
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


@contextmanager
def _bounded_backtest_logging() -> Iterator[None]:
    """Suppress high-frequency INFO rendering during the annual run.

    Yields:
        Control while warnings and failures remain visible.
    """
    application_logger = logging.getLogger("haruquant")
    previous_level = application_logger.level
    application_logger.setLevel(logging.WARNING)
    try:
        yield
    finally:
        application_logger.setLevel(previous_level)


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
    adapter_response = create_broker_adapter(mt5_config.broker_id, mt5_config)
    if adapter_response.error is not None or adapter_response.data is None:
        raise RuntimeError("MT5 demo adapter construction failed")
    adapter = adapter_response.data
    connection_response = asyncio.run(connect_broker(adapter))
    if connection_response.error is not None:
        raise RuntimeError("MT5 demo connection failed")
    try:
        specification_response = asyncio.run(
            get_broker_provider_specification(adapter, SYMBOL)
        )
        account_response = asyncio.run(get_broker_account_info(adapter))
        _ACTIVE_PROVIDER_FACTS.append(
            _provider_facts_from_responses(specification_response, account_response)
        )
    except Exception:
        asyncio.run(disconnect_broker(adapter))
        raise
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
        try:
            yield True
        finally:
            _ACTIVE_PROVIDER_FACTS.clear()
            asyncio.run(disconnect_broker(adapter))


def _get_dataset(
    *,
    timeframe: str = TIMEFRAME,
    limit: int = BAR_LIMIT,
    start: datetime = _START,
    end: datetime = _END,
    use_cache: bool = True,
) -> Any:
    """Retrieve MT5 market dataset through the Data public API.

    Args:
        timeframe: Assigned canonical timeframe.
        limit: Number of records to retrieve.
        start: Inclusive UTC request boundary.
        end: Inclusive UTC request boundary.
        use_cache: Whether to reuse compatible historical cache evidence.

    Returns:
        Canonical market dataset if available, else None.
    """
    req = build_market_data_request(
        source_id="mt5",
        symbol=SYMBOL,
        data_kind="bars",
        timeframe=timeframe,
        start=start,
        end=end,
        limit=limit,
        use_cache=use_cache,
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
    """Build a canonical official or explicitly non-canonical research request."""
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
        "data_ref": f"mt5:{dataset.symbol}:{dataset.timeframe}",
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
        "symbol": dataset.symbol,
        "timeframe": dataset.timeframe,
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
    value_type = "FastResearchRequest"
    hash_operation = calculate_fast_research_config_hash
    if canonical:
        payload.update(
            {
                "execution_model_ref": "execution-model-v1",
                "execution_model_hash": "e" * 64,
                "calculation_model_hash": "f" * 64,
                "calculation_artifact_checksum": "1" * 64,
                "calibration_artifact_checksum": "2" * 64,
                "realism_stream_identity_hash": "3" * 64,
                "source_lineage_hash": "4" * 64,
                "tick_lineage_hash": "5" * 64,
                "market_evidence_class": "genuine_bid_ask_ticks",
                "decision_instant_policy": "point_in_time_available_at",
                "provider_specification_revisions": (
                    {
                        "revision_id": "revision-1",
                        "checksum": "6" * 64,
                        "provider": "mt5",
                        "server": "demo-server",
                        "environment": "demo",
                        "account_digest": "7" * 64,
                        "symbol": dataset.symbol,
                        "observed_at": start,
                        "effective_from": start,
                        "effective_to": None,
                        "historical_provenance": None,
                    },
                ),
                "initial_authority_state_hash": canonical_digest(
                    {
                        "account": {
                            "balance": Decimal("10000.00"),
                            "currency": "USD",
                        },
                        "orders": (),
                        "positions": (),
                        "deals": (),
                        "ownership": {"mode": "exclusive"},
                    }
                ),
                "certification_target": "demo",
                "close_open_positions_at_end": True,
            }
        )
        value_type = "SimulationBacktestRequest"
        hash_operation = calculate_simulation_backtest_config_hash
    payload["config_hash"] = unwrap_simulation_response(
        hash_operation(payload),
        operation="calculate_backtest_config_hash",
    )
    return create_simulation_value(value_type, **payload)


def example_02_fast_research_simulation() -> None:
    """Demonstrate fast research simulation run with real MT5 market dataset context."""
    _header("Example 2: Fast Research Simulation (with MT5 EURUSD H1 data)")

    dataset = _get_dataset()
    if dataset is None:
        print("Market dataset offline -> Using bounded fixture tick dataset context")
        dataset = live_tick_dataset()
    else:
        print(
            f"Retrieved {len(dataset.records)} MT5 {SYMBOL} {TIMEFRAME} bars for fast research simulation"
        )

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
    """Demonstrate the canonical asynchronous single-asset backtest run."""
    _header("Example 3: Official Single-Asset Backtest Run & Result Inspection")

    dataset = live_tick_dataset()
    request = _build_backtest_request(
        dataset, runtime_profile="simulation", canonical=True
    )
    with tempfile.TemporaryDirectory() as tmp_dir:
        deps = dependencies(Path(tmp_dir), dataset)
        response = asyncio.run(run_backtest_async(request, authority(request), deps))
        result = unwrap_simulation_response(response, operation="run_backtest_async")
        print(f"Official Single-Asset Backtest Status: {response.status}")
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
    port_req = create_simulation_value("PortfolioBacktestRequest", **payload)

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
        response = asyncio.run(run_portfolio_backtest(port_req, auth, deps))
        unwrap_simulation_response(response, operation="run_portfolio_backtest")
        print(f"Portfolio Backtest Simulation Status: {response.status}")


def example_06_simulation_reporting_and_checklist() -> None:
    """Demonstrate simulation reporting schema and canonical artifact types."""
    _header("Example 6: Simulation Reporting Schemas & Canonical Artifact Types")

    print(f"Report Schema Version: {get_report_schema_version()}")
    print(f"Canonical Artifact Types: {get_canonical_artifact_types()}")


def _analytics_config(created_at: datetime) -> object:
    """Build bounded Analytics settings for the full backtest report.

    Args:
        created_at: UTC evidence timestamp used by the explicit zero-rate model.

    Returns:
        Opaque Analytics run configuration.
    """
    risk_free_rate = create_analytics_value(
        "RiskFreeRateEvidence",
        rate=Decimal(0),
        unit="annual_decimal",
        source="legacy-example-zero-rate-assumption",
        as_of=created_at,
    )
    statistics = create_analytics_value(
        "StatisticalValidationConfig",
        seed=7,
        bootstrap_iterations=100,
        permutation_iterations=100,
        confidence=0.95,
        alpha=0.05,
    )
    return create_analytics_value(
        "AnalyticsRunConfig",
        max_warning_detail_bytes=4_096,
        max_trades=10_000,
        max_equity_points=10_000,
        max_benchmark_points=10_000,
        max_statistical_observations=10_000,
        max_bootstrap_iterations=100,
        max_permutation_iterations=100,
        max_portfolio_components=10,
        max_response_bytes=2_000_000,
        risk_free_rate=risk_free_rate,
        statistics=statistics,
    )


def _print_performance_report(report: object, result: object) -> None:
    """Print calculated Analytics metrics and bounded Simulation evidence.

    Args:
        report: Canonical Analytics PerformanceReport.
        result: Canonical SimulationResult.

    Returns:
        None.
    """
    labels = {
        "starting_equity": "Equity Start [$]",
        "ending_equity": "Equity Final [$]",
        "net_pnl": "Net PnL [$]",
        "cagr": "CAGR",
        "volatility": "Volatility (Ann.)",
        "sharpe_ratio": "Sharpe Ratio",
        "sortino_ratio": "Sortino Ratio",
        "calmar_ratio": "Calmar Ratio",
        "max_drawdown": "Max. Drawdown",
        "max_drawdown_duration": "Max. Drawdown Duration",
        "trade_count": "# Trades",
        "win_rate": "Win Rate",
        "profit_factor": "Profit Factor",
        "payoff_ratio": "Payoff Ratio",
        "expectancy": "Expectancy [$]",
        "average_trade_duration": "Avg. Trade Duration",
        "total_commission": "Commission [$]",
        "total_swap": "Swap [$]",
        "total_cost_drag": "Total Cost Drag [$]",
        "benchmark_alpha": "Alpha",
        "benchmark_beta": "Beta",
        "benchmark_correlation": "Benchmark Correlation",
        "tracking_error": "Tracking Error",
        "information_ratio": "Information Ratio",
    }
    metrics: dict[str, object] = {}
    for section in get_analytics_value_field(report, "sections"):
        for metric in get_analytics_value_field(section, "metrics"):
            key = get_analytics_value_field(metric, "metric_key")
            if get_analytics_value_field(metric, "status") == "calculated":
                metrics[str(key)] = get_analytics_value_field(metric, "value")
    print(f"Start                     {BACKTEST_START}")
    print(f"End                       {BACKTEST_END}")
    print(f"Duration                  {BACKTEST_END - BACKTEST_START}")
    for key, label in labels.items():
        print(f"{label:<27} {metrics.get(key, 'not calculated')}")
    print(
        "Strategy                  "
        f"naive-ma-trend(fast={BACKTEST_FAST_MA}, slow={BACKTEST_SLOW_MA}, "
        f"filter={BACKTEST_FILTER_MA})"
    )
    print(
        f"Quality Flags             {get_analytics_value_field(report, 'quality_flags')}"
    )
    print(f"Caveats                   {get_analytics_value_field(report, 'caveats')}")
    print(f"Closed Trades             {result.closed_trades}")


def _print_data_quality(dataset: object) -> None:
    """Print accepted Data quality evidence and calendar provenance.

    Args:
        dataset: Canonical Data-owned market dataset used by Simulation.

    Returns:
        None.
    """
    report = cast("Any", dataset).quality_report
    flags = tuple(issue.code for issue in report.issues)
    calendar_provenance = tuple(
        sample
        for issue in report.issues
        if issue.code == "CALENDAR_SUPPORTED_CLOSURE"
        for sample in issue.samples
    )
    print(f"Data Quality Decision     {report.quality_decision}")
    print(f"Data Quality Score        {report.quality_score}")
    print(f"Data Quality Flags        {flags}")
    print(f"Data Quality Warnings     {report.warnings}")
    print(f"Calendar Gap Provenance   {calendar_provenance}")


def example_07_backtest_simulation() -> None:
    """Run a full 2025 EURUSD H1 naive-trend backtest and Analytics report."""
    total_started = time.perf_counter()
    timings: dict[str, float] = {}
    _header("Example 7: Full EURUSD H1 Naive MA Trend Backtest")
    stage_started = time.perf_counter()
    dataset = _get_dataset(
        timeframe=TIMEFRAME,
        limit=BACKTEST_BAR_LIMIT,
        start=BACKTEST_WARMUP_START,
        end=BACKTEST_END,
        use_cache=False,
    )
    timings["B06-B10 market retrieval and quality"] = (
        time.perf_counter() - stage_started
    )
    if dataset is None or len(dataset.records) < BACKTEST_FILTER_MA:
        raise RuntimeError("MT5 returned insufficient EURUSD H1 history with warmup")
    print(
        f"Retrieved {len(dataset.records)} genuine MT5 {SYMBOL} {TIMEFRAME} bars "
        f"from {dataset.start} through {dataset.end} (including warmup)"
    )
    _print_data_quality(dataset)
    measurement_records = tuple(
        record
        for record in dataset.records
        if BACKTEST_START <= record.timestamp <= BACKTEST_END
    )
    if not measurement_records:
        raise RuntimeError(
            "MT5 returned no EURUSD H1 records in the measurement period"
        )
    measurement_quality = dataset.quality_report.model_copy(
        update={
            "record_count": len(measurement_records),
            "checked_count": len(measurement_records),
        }
    )
    measurement_dataset = dataset.model_copy(
        update={
            "records": measurement_records,
            "record_count": len(measurement_records),
            "start": measurement_records[0].timestamp,
            "end": measurement_records[-1].timestamp,
            "available_at": measurement_records[-1].available_at,
            "quality_report": measurement_quality,
        }
    )
    stage_started = time.perf_counter()
    request = _build_backtest_request(measurement_dataset)
    request_values = request.model_dump(mode="python", warnings=False)
    tick_response = generate_tick_series(
        measurement_dataset,
        model="trading_bar",
        trading_timeframe=TIMEFRAME,
        spread_model="fixed_spread",
        fixed_spread_points=Decimal(10),
        point_value=Decimal("0.00001"),
    )
    tick_dataset = unwrap_data_response(
        tick_response,
        operation="legacy.full_backtest.generate_tick_series",
        request_id=dataset.request_id,
    )
    timings["B11-B15 request and tick generation"] = time.perf_counter() - stage_started
    request_values.update(
        strategy_id="naive-ma-trend",
        strategy_version="1.0.0",
        parameters={
            "fast_ma_period": BACKTEST_FAST_MA,
            "slow_ma_period": BACKTEST_SLOW_MA,
            "filter_ma_period": BACKTEST_FILTER_MA,
        },
        start=tick_dataset.start,
        end=tick_dataset.end,
        initial_balance=BACKTEST_INITIAL_BALANCE,
        data_hash=canonical_digest(
            tick_dataset.model_dump(mode="python", warnings=False)
        ),
    )
    provider_revision = dict(request_values["provider_specification_revisions"][0])
    if not _ACTIVE_PROVIDER_FACTS:
        raise RuntimeError("verified MT5 provider facts are unavailable")
    specification = _ACTIVE_PROVIDER_FACTS[0].specification
    provider_revision.update(
        revision_id=f"mt5-current-{specification['checksum']}",
        checksum=specification["checksum"],
        provider=specification["broker"],
        server=specification["server"],
        environment=specification["environment"],
        account_digest=specification["account_digest"],
        symbol=specification["provider_symbol"],
        observed_at=datetime.fromisoformat(str(specification["observed_at"])),
        effective_from=tick_dataset.start,
        historical_provenance={
            "specification_basis": "current_mt5_demo_snapshot",
            "session_basis": "exact_generated_tick_dataset",
            "historical_schedule_authority": False,
        },
    )
    request_values["provider_specification_revisions"] = (provider_revision,)
    request_values["config_hash"] = unwrap_simulation_response(
        calculate_simulation_backtest_config_hash(request_values),
        operation="calculate_simulation_backtest_config_hash",
    )
    request = create_simulation_value("SimulationBacktestRequest", **request_values)
    with tempfile.TemporaryDirectory() as tmp_dir:
        deps = naive_trend_dependencies(Path(tmp_dir), dataset, tick_dataset)
        stage_started = time.perf_counter()
        response = asyncio.run(run_backtest_async(request, authority(request), deps))
        result = unwrap_simulation_response(response, operation="run_backtest_async")
        timings["B16-B25 canonical simulation"] = time.perf_counter() - stage_started
        if not result.closed_trades:
            raise RuntimeError("naive trend backtest produced no closed-trade evidence")
        source = {
            "contract_version": result.contract_version,
            "schema_id": result.schema_id,
            "source_id": result.run_id,
            "phase": "backtest",
            "window_start": BACKTEST_START,
            "window_end": BACKTEST_END,
            "strategy_id": request.strategy_id,
            "strategy_version": request.strategy_version,
            "symbols": (request.symbol,),
            "timeframe": request.timeframe,
            "closed_trades": tuple(
                trade.model_dump(mode="python", warnings=False)
                for trade in result.closed_trades
            ),
            "quality_metadata": {
                "status": dataset.quality_report.quality_status,
                "decision": dataset.quality_report.quality_decision,
                "score": str(dataset.quality_report.quality_score),
                "flags": tuple(issue.code for issue in dataset.quality_report.issues),
                "warnings": dataset.quality_report.warnings,
                "calendar_closure_provenance": tuple(
                    sample
                    for issue in dataset.quality_report.issues
                    if issue.code == "CALENDAR_SUPPORTED_CLOSURE"
                    for sample in issue.samples
                ),
            },
            "source_metadata": {"provider": "mt5", "route": "sim"},
        }
        stage_started = time.perf_counter()
        report_response = build_performance_report(
            source,
            source_contract="simulation.result",
            request_id=generate_id("req"),
            correlation_id=request.correlation_id,
            created_at=measurement_dataset.end,
            initial_balance=request.initial_balance,
            account_currency=request.account_currency,
            config=_analytics_config(measurement_dataset.end),
            benchmark=measurement_dataset,
        )
        report = unwrap_simulation_response(
            report_response, operation="build_performance_report"
        )
        timings["B26-B27 analytics"] = time.perf_counter() - stage_started
        _print_performance_report(report, result)
    timings["B28 total example"] = time.perf_counter() - total_started
    print("Path Timings [seconds]")
    for path, elapsed in timings.items():
        print(f"  {path:<42} {elapsed:.6f}")


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
    parser.add_argument(
        "--example-07",
        action="store_true",
        help="Run only the genuine full-year MT5 demo backtest.",
    )
    args = parser.parse_args()
    if args.offline and args.example_07:
        parser.error("--example-07 requires the read-only MT5 demo provider")

    with _provider_runtime_context(offline=args.offline):
        if args.example_07:
            with _bounded_backtest_logging():
                example_07_backtest_simulation()
            return
        example_01_simulation_mode_and_policies()
        example_02_fast_research_simulation()
        example_03_single_asset_backtest_run()
        example_04_realistic_execution_cost_modeling()
        example_05_portfolio_backtest_simulation()
        example_06_simulation_reporting_and_checklist()
        if not args.offline:
            with _bounded_backtest_logging():
                example_07_backtest_simulation()
        else:
            print(
                "\nExample 7 skipped: full backtest requires read-only MT5 demo data."
            )


if __name__ == "__main__":
    main()
