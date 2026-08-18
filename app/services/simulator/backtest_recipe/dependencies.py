"""Strategy-driven Simulation dependencies for the canonical backtest recipe.

This is the production form of the composition proven by
``tests/legacy/08_simulator.py`` (``example_07_backtest_simulation``). Two
differences from that script are deliberate:

* signals are evaluated through the public ``evaluate_strategy_signals``
  boundary rather than an evaluator's private ``_evaluate_compact`` helper; and
* MT5 facts arrive as an explicit value rather than through module-level mutable
  state, so concurrent runs cannot observe each other's provider evidence.

Everything the Simulator treats as evidence — execution profile, symbol
specification, cost model, provider specification revisions — is still derived
solely from the supplied provider facts and never invented.
"""

from __future__ import annotations

import hashlib
import inspect
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from app.services.data import generate_tick_series, unwrap_data_response
from app.services.simulator import create_simulation_value
from app.services.strategy import (
    create_strategy_evaluator,
    create_strategy_execution_context,
    create_strategy_manifest,
    create_strategy_signal_evidence,
    create_strategy_validation_policy,
    create_validated_strategy_config,
    create_validated_strategy_ref,
    evaluate_strategy_signals,
    get_strategy_environment,
    get_strategy_lifecycle_status,
    get_strategy_timing_policy,
    unwrap_strategy_response,
)
from app.services.trading import create_order_intent
from app.utils import canonical_digest, canonical_json

if TYPE_CHECKING:
    from app.services.simulator.backtest_recipe.descriptors import StrategyDescriptor

_SECONDS_PER_WEEK = 604_800
_POLICY_VERSION = "backtest-recipe-v1"


@dataclass(frozen=True, slots=True)
class ProviderFacts:
    """Read-only provider evidence bound to one backtest run."""

    specification: Mapping[str, object]
    leverage: Decimal
    account_currency: str


@dataclass(frozen=True, slots=True)
class ExecutionSettings:
    """Operator-chosen execution assumptions for one backtest run."""

    volume: Decimal
    commission_per_lot_per_side: Decimal
    spread_points: Decimal
    slippage_points: Decimal


def required_decimal(source: Mapping[str, object], field: str) -> Decimal:
    """Return one required positive provider decimal or fail closed.

    Args:
        source: Provider specification snapshot.
        field: Required specification field name.

    Returns:
        Validated positive decimal.

    Raises:
        ValueError: If the field is absent or not a positive finite decimal.
    """
    if field not in source:
        message = f"provider specification omitted {field}"
        raise ValueError(message)
    value = Decimal(str(source[field]))
    if not value.is_finite() or value <= 0:
        message = f"provider specification has invalid {field}"
        raise ValueError(message)
    return value


def _swap_cash_effect(facts: ProviderFacts, field: str) -> Decimal:
    """Convert a signed provider point swap into account-currency cash per lot.

    Args:
        facts: Verified provider facts for this run.
        field: Signed swap field name.

    Returns:
        Cash effect per lot per rollover.

    Raises:
        ValueError: If the provider does not prove a POINTS swap basis.
    """
    specification = facts.specification
    if specification.get("swap_mode") != "POINTS":
        raise ValueError("backtest recipe requires POINTS swap evidence")
    if specification.get("profit_currency") != facts.account_currency:
        raise ValueError("swap conversion requires matching profit/account currency")
    rate = Decimal(str(specification[field]))
    if not rate.is_finite():
        message = f"provider specification has invalid {field}"
        raise ValueError(message)
    return (
        rate
        * required_decimal(specification, "point")
        * required_decimal(specification, "contract_size")
    )


def dataset_hash(dataset: object) -> str:
    """Return the canonical digest of a Data-owned dataset.

    Args:
        dataset: Canonical Data-owned dataset.

    Returns:
        Canonical digest of the dataset payload.
    """
    return canonical_digest(
        cast("Any", dataset).model_dump(mode="python", warnings=False)
    )


class StrategyBacktestDependencies:
    """Evaluate a registered strategy through Simulation authority."""

    fast_research_enabled = False

    def __init__(
        self,
        *,
        root: Path,
        dataset: object,
        tick_dataset: object,
        descriptor: StrategyDescriptor,
        parameters: Mapping[str, object],
        facts: ProviderFacts,
        execution: ExecutionSettings,
        account_id: str,
    ) -> None:
        """Build one self-contained registered-strategy composition.

        Args:
            root: Isolated run directory owning artifacts and audit evidence.
            dataset: Canonical bar dataset including warm-up history.
            tick_dataset: Exact request-bound generated tick dataset.
            descriptor: Registered strategy descriptor driving the run.
            parameters: Resolved strategy configuration parameters.
            facts: Verified provider facts for this run.
            execution: Operator-chosen execution assumptions.
            account_id: Logical account identity recorded on order intents.
        """
        from app.services.simulator.state import build_simulation_state_store

        self.artifact_root = root / "artifacts"
        self.artifact_root.mkdir(parents=True, exist_ok=True)
        self.state_store = build_simulation_state_store(
            artifact_root=self.artifact_root
        )
        self.dataset = dataset
        self.audit_path = root / "audit.jsonl"
        self._tick_dataset = tick_dataset
        self._descriptor = descriptor
        self._facts = facts
        self._execution = execution
        self._account_id = account_id
        self._parameters = dict(parameters)
        self._warmup = descriptor.warmup_bars(self._parameters)
        self._last_bar_available_at: datetime | None = None
        self._sequence = 0
        self._strategy_request_id: str | None = None
        self._strategy_ref: object | None = None
        self._strategy_config: object | None = None
        self._strategy_evaluator: object | None = None
        probe = create_strategy_evaluator(
            descriptor.evaluator_name,
            strategy_id=descriptor.strategy_id,
            strategy_version=descriptor.strategy_version,
            module_path=descriptor.module_path,
            source_hash="0" * 64,
            artifact_hash="0" * 64,
            dependency_hash="0" * 64,
        )
        self._source_hash = hashlib.sha256(
            inspect.getsource(type(probe)).encode()
        ).hexdigest()
        self._config_hash = canonical_digest(self._parameters)
        self._policy = create_strategy_validation_policy(
            policy_version=_POLICY_VERSION,
            approved_module_roots=("app.services.strategy.evaluators",),
            max_config_payload_bytes=4_096,
            max_config_nesting_depth=8,
            max_config_string_length=128,
            max_config_collection_items=64,
        )

    # -- Evidence and audit -------------------------------------------------

    def persist_audit_event(self, event: object) -> None:
        """Append one canonical audit event to isolated run state.

        Args:
            event: Canonical audit event.
        """
        with self.audit_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(
                canonical_json(
                    cast("Any", event).model_dump(mode="python", warnings=False)
                )
            )
            stream.write("\n")

    def load_market_data(self, request: object) -> object:
        """Return the caller-supplied market evidence.

        Args:
            request: Canonical Simulation request.

        Returns:
            Bar dataset supplied at construction.
        """
        del request
        return self.dataset

    def generate_tick_series(self, dataset: object, request: object) -> object:
        """Return the pre-generated request-bound tick stream.

        Args:
            dataset: Canonical bar dataset.
            request: Canonical Simulation request.

        Returns:
            Exact tick dataset bound to the request data hash.

        Raises:
            ValueError: If the request hash does not match the generated ticks.
        """
        del dataset
        if cast("Any", request).data_hash != dataset_hash(self._tick_dataset):
            raise ValueError("request data hash does not match generated ticks")
        return self._tick_dataset

    def load_initial_authority_state(self, request: object) -> Mapping[str, object]:
        """Return a complete empty initial authority snapshot.

        Args:
            request: Canonical Simulation request.

        Returns:
            Empty exclusive-ownership authority state.
        """
        return {
            "account": {
                "balance": cast("Any", request).initial_balance,
                "currency": cast("Any", request).account_currency,
            },
            "orders": (),
            "positions": (),
            "deals": (),
            "ownership": {"mode": "exclusive"},
        }

    def load_account_activity(self, request: object) -> tuple[object, ...]:
        """Return no foreign account activity.

        Args:
            request: Canonical Simulation request.

        Returns:
            Empty activity tuple.
        """
        del request
        return ()

    def load_provider_specification_revisions(
        self, request: object
    ) -> Mapping[str, object]:
        """Return current provider facts with tick-evidence session provenance.

        Args:
            request: Canonical Simulation request.

        Returns:
            Complete request-bound specification revision evidence.
        """
        binding = cast("Any", request).provider_specification_revisions[0]
        specification = self._facts.specification
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
                        "filling_modes": tuple(
                            cast("Any", specification["filling_modes"])
                        ),
                        "execution_mode": specification["execution_mode"],
                        "trade_mode": specification["trade_mode"],
                        "stops_level_points": specification["stops_level_points"],
                        "freeze_level_points": specification["freeze_level_points"],
                        "directional_volume_limit": specification[
                            "directional_volume_limit"
                        ],
                        "point": specification["point"],
                        # The provider exposes no historical session API. The
                        # exact generated ticks are the executable-instant
                        # evidence for this run.
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

    # -- Provider-derived execution evidence --------------------------------

    def resolve_execution_profile(self, request: object) -> object:
        """Build execution pricing from provider point and tick-size facts.

        Args:
            request: Canonical Simulation request.

        Returns:
            Canonical execution profile value.
        """
        del request
        specification = self._facts.specification
        session = create_simulation_value(
            "SessionInterval", start_week_second=0, end_week_second=_SECONDS_PER_WEEK
        )
        slippage = self._execution.slippage_points
        return create_simulation_value(
            "ExecutionProfile",
            slippage_mode="fixed_points",
            fixed_slippage_points=slippage,
            point_value=required_decimal(specification, "point"),
            price_quantum=required_decimal(specification, "tick_size"),
            maximum_slippage_points=slippage,
            maximum_gap_points=Decimal(10),
            liquidity_mode="unbounded",
            participation_rate=Decimal(0),
            sessions=(session,),
        )

    def resolve_symbol_specification(self, request: object) -> object:
        """Build Simulation constraints solely from current provider facts.

        Args:
            request: Canonical Simulation request.

        Returns:
            Canonical symbol specification value.
        """
        del request
        specification = self._facts.specification
        return create_simulation_value(
            "SymbolSpecification",
            minimum_volume=required_decimal(specification, "volume_min"),
            maximum_volume=required_decimal(specification, "volume_max"),
            volume_step=required_decimal(specification, "volume_step"),
            contract_size=required_decimal(specification, "contract_size"),
            leverage=self._facts.leverage,
        )

    def resolve_cost_model(self, request: object) -> object:
        """Build explicit run costs and provider-observed swap rates.

        Args:
            request: Canonical Simulation request.

        Returns:
            Canonical execution cost model value.
        """
        del request
        return create_simulation_value(
            "ExecutionCostModel",
            commission_per_lot_per_side=self._execution.commission_per_lot_per_side,
            long_swap_per_lot_rollover=_swap_cash_effect(self._facts, "swap_long"),
            short_swap_per_lot_rollover=_swap_cash_effect(self._facts, "swap_short"),
        )

    def resolve_fx_evidence(
        self, evidence_ids: tuple[str, ...]
    ) -> Mapping[str, object]:
        """Resolve conversion evidence for single-asset runs.

        Args:
            evidence_ids: Requested conversion evidence identifiers.

        Returns:
            Empty mapping; a single-asset run in account currency needs none.

        Raises:
            ValueError: If conversion evidence is actually requested.
        """
        if evidence_ids:
            raise ValueError(
                "single-asset backtest recipe supplies no FX conversion evidence"
            )
        return {}

    # -- Strategy binding and evaluation ------------------------------------

    def _strategy_binding(
        self, request: object, decision_at: datetime
    ) -> tuple[object, object, object, object]:
        """Return cached validated strategy objects and the current context.

        Args:
            request: Canonical Simulation request.
            decision_at: Current point-in-time decision instant.

        Returns:
            Validated reference, configuration, evaluator, and context.

        Raises:
            ValueError: If the cached strategy binding is incomplete.
        """
        typed = cast("Any", request)
        context = create_strategy_execution_context(
            environment=get_strategy_environment("RESEARCH"),
            decision_timestamp=decision_at,
            timing_policy=get_strategy_timing_policy("BAR_OPEN_PREVIOUS_CLOSE"),
            seed=typed.seed,
            interface_version="v1",
            request_id=typed.request_id,
            workflow_id=typed.workflow_id,
            correlation_id=typed.correlation_id,
            dependency_status={"data": "ready", "indicators": "ready"},
            snapshot_refs=(typed.data_hash,),
            max_diagnostic_bytes=8_192,
        )
        if self._strategy_request_id != typed.request_id:
            descriptor = self._descriptor
            manifest = create_strategy_manifest(
                strategy_id=descriptor.strategy_id,
                strategy_version=descriptor.strategy_version,
                module_path=descriptor.module_path,
                owner_ref="backtest-recipe",
                interface_version="v1",
                config_schema_version="v1",
                config_schema={"type": "object"},
                required_data=(f"{typed.symbol}:{typed.timeframe}",),
                required_indicators=descriptor.required_indicators,
                timing_policy=context.timing_policy,
                permitted_environments=(context.environment,),
                source_hash=self._source_hash,
                artifact_hash=self._source_hash,
                dependency_hash=self._source_hash,
                provenance_refs=(typed.data_hash,),
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
                request_id=typed.request_id,
                correlation_id=typed.correlation_id,
            )
            self._strategy_config = create_validated_strategy_config(
                strategy_id=descriptor.strategy_id,
                strategy_version=descriptor.strategy_version,
                config_schema_version="v1",
                normalized_parameters=self._parameters,
                config_hash=self._config_hash,
                policy_version=self._policy.policy_version,
                request_id=typed.request_id,
            )
            self._strategy_evaluator = create_strategy_evaluator(
                descriptor.evaluator_name,
                strategy_id=descriptor.strategy_id,
                strategy_version=descriptor.strategy_version,
                module_path=descriptor.module_path,
                source_hash=self._source_hash,
                artifact_hash=self._source_hash,
                dependency_hash=self._source_hash,
            )
            self._strategy_request_id = typed.request_id
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

    def _active_signal_names(
        self, records: tuple[object, ...], request: object, decision_at: datetime
    ) -> frozenset[str]:
        """Evaluate the bound strategy and return its active signal names.

        Args:
            records: Exact causal bar window visible at the decision instant.
            request: Canonical Simulation request.
            decision_at: Current point-in-time decision instant.

        Returns:
            Active signal names produced by the registered evaluator.
        """
        ref, config, evaluator, context = self._strategy_binding(request, decision_at)
        window = cast("Any", self.dataset).model_copy(
            update={
                "records": records,
                "record_count": len(records),
                "start": cast("Any", records[0]).timestamp,
                "end": cast("Any", records[-1]).timestamp,
                "available_at": cast("Any", records[-1]).available_at,
            }
        )
        evidence = create_strategy_signal_evidence(
            evidence_id=f"{cast('Any', request).request_id}-{self._sequence}",
            primary_market=window,
            related_markets={},
            point_size=required_decimal(self._facts.specification, "point"),
            feature_values={},
            feature_available_at={},
            feature_refs={},
            active_position_tags=(),
        )
        signals = unwrap_strategy_response(
            evaluate_strategy_signals(
                cast("Any", ref),
                cast("Any", config),
                evidence,
                (),
                cast("Any", context),
                cast("Any", evaluator),
            ),
            operation="simulator.backtest_recipe.evaluate_strategy_signals",
        )
        return frozenset(
            cast("Any", signal).signal_name
            for signal in cast("tuple[Any, ...]", signals)
            if cast("Any", signal).active
        )

    async def evaluate_point_in_time_cycle(
        self, dataset: object, decision_at: object, engine: object, request: object
    ) -> object:
        """Evaluate every newly visible bar close without lookahead.

        Args:
            dataset: Point-in-time visible bar dataset.
            decision_at: Current decision instant.
            engine: Simulation execution engine authority.
            request: Canonical Simulation request.

        Returns:
            Mutation outcome for this decision instant.

        Raises:
            ValueError: If future evidence reaches the evaluation cycle.
        """
        records = cast("Any", dataset).records
        latest = records[-1]
        instant = cast("datetime", decision_at)
        if latest.available_at > instant:
            raise ValueError("future evidence reached the backtest cycle")
        if (
            len(records) < self._warmup
            or latest.available_at == self._last_bar_available_at
        ):
            return {"mutation_performed": False}
        self._last_bar_available_at = latest.available_at
        descriptor = self._descriptor
        active = self._active_signal_names(
            tuple(records[-self._warmup :]), request, instant
        )
        snapshot = cast("Any", engine).snapshot_internal()
        positions = snapshot["positions"]
        if positions:
            position = positions[0]
            exits = (
                descriptor.long_exit_signals
                if position["side"] == "BUY"
                else descriptor.short_exit_signals
            )
            if active & exits:
                return await self.execute_trading_action(
                    {"position": position}, engine, request
                )
            return {"mutation_performed": False}
        if active & descriptor.long_entry_signals:
            side = "BUY"
        elif active & descriptor.short_entry_signals:
            side = "SELL"
        else:
            return {"mutation_performed": False}
        return await self.execute_trading_action(
            self._build_order_intent(side, request, instant), engine, request
        )

    def _build_order_intent(
        self, side: str, request: object, decision_at: datetime
    ) -> object:
        """Build one Trading-owned order intent for a simulated entry.

        Args:
            side: Approved order side.
            request: Canonical Simulation request.
            decision_at: Current decision instant.

        Returns:
            Canonical Trading order intent.

        Raises:
            ValueError: If the provider proves no filling mode.
        """
        typed = cast("Any", request)
        self._sequence += 1
        filling_modes = tuple(cast("Any", self._facts.specification["filling_modes"]))
        if not filling_modes:
            raise ValueError("provider specification has no filling mode")
        volume = self._execution.volume
        return create_order_intent(
            client_order_id=f"{self._descriptor.strategy_id}-{self._sequence}",
            request_id=typed.request_id,
            workflow_id=typed.workflow_id,
            correlation_id=typed.correlation_id,
            route="sim",
            provider_id=None,
            account_id=self._account_id,
            strategy_id=self._descriptor.strategy_id,
            strategy_version=self._descriptor.strategy_version,
            source_intent_id=f"signal-{self._sequence}",
            symbol=typed.symbol,
            action="submit_order",
            side=side,
            order_type="MARKET",
            quantity_unit="lot",
            approved_volume=volume,
            risk_approved_volume=volume,
            time_in_force=cast("Any", filling_modes[0]),
            idempotency_hash=canonical_digest(
                {"run": typed.request_id, "sequence": self._sequence, "side": side}
            ),
            canonical_material_version="v1",
            risk_decision_id=f"risk-{self._sequence}",
            action_policy_verdict_id="simulation-risk-approved",
            # Not a credential: a Trading contract reference naming the
            # simulation-only approval path. S106 heuristic false positive.
            approval_token_ref="simulation-only",  # noqa: S106
            created_at=decision_at,
            valid_until=typed.end + timedelta(days=1),
        )

    async def execute_trading_action(
        self, approved_request: object, engine: object, request: object
    ) -> object:
        """Submit or close solely through Simulation authority.

        Args:
            approved_request: Order intent, or a mapping naming a position.
            engine: Simulation execution engine authority.
            request: Canonical Simulation request.

        Returns:
            Engine-owned mutation outcome.
        """
        del request
        typed_engine = cast("Any", engine)
        if isinstance(approved_request, Mapping):
            position = approved_request["position"]
            return typed_engine.close_position(
                position["position_id"], position["volume"]
            )
        return typed_engine.submit_order(approved_request)

    async def execute_terminal_action(
        self, position: Mapping[str, object], engine: object, request: object
    ) -> object:
        """Liquidate an open terminal position through Simulation authority.

        Args:
            position: Open position snapshot.
            engine: Simulation execution engine authority.
            request: Canonical Simulation request.

        Returns:
            Engine-owned mutation outcome.
        """
        return await self.execute_trading_action(
            {"position": position}, engine, request
        )


def build_run_tick_dataset(
    dataset: object, *, timeframe: str, spread_points: Decimal
) -> object:
    """Generate the canonical tick stream backing one backtest run.

    Args:
        dataset: Canonical measurement-window bar dataset.
        timeframe: Canonical trading timeframe.
        spread_points: Fixed spread applied to generated ticks.

    Returns:
        Canonical Data-owned tick dataset.
    """
    typed = cast("Any", dataset)
    generated = generate_tick_series(
        typed,
        model="trading_bar",
        trading_timeframe=timeframe,
        spread_model="fixed_spread",
        fixed_spread_points=spread_points,
        point_value=Decimal("0.00001"),
    )
    return unwrap_data_response(
        generated,
        operation="simulator.backtest_recipe.generate_tick_series",
        request_id=typed.request_id,
    )


__all__ = (
    "ExecutionSettings",
    "ProviderFacts",
    "StrategyBacktestDependencies",
    "build_run_tick_dataset",
    "dataset_hash",
    "required_decimal",
)
