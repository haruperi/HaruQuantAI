# ruff: noqa: E501, E402
"""Direct, copyable usage catalogue demonstrating vectorized and event-driven strategy execution using real MT5 data.

Example 1 runs vectorized strategy evaluation via ``run_vectorized_strategy_signals``
on real MT5 EURUSD H1 market data and prints transaction rows with non-zero signals.
Example 2 simulates event-driven bar-by-bar evaluation using ``run_event_strategy_hook``.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd

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
from app.services.strategy import (
    build_development_strategy_validation_policy,
    create_strategy_decision,
    create_strategy_event,
    create_strategy_execution_context,
    create_strategy_manifest,
    create_validated_strategy_config,
    create_validated_strategy_ref,
    get_strategy_environment,
    get_strategy_lifecycle_status,
    get_strategy_timing_policy,
    run_event_strategy_hook,
    run_vectorized_strategy_signals,
)
from app.utils import generate_id, load_broker_provider_settings

_START = datetime(2026, 8, 1, tzinfo=UTC)
_END = _START + timedelta(hours=1000)
_HASH = "f" * 64
_STRATEGY = "legacy-trend-strategy"
_MODULE = "app.services.strategy.evaluators.naive_ma_trend"
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


class LegacyTrendStrategyEvaluator:
    """Sample Strategy evaluator conforming to Strategy domain boundaries."""

    strategy_id = _STRATEGY
    strategy_version = "1.0.0"
    module_path = _MODULE
    source_hash = _HASH
    artifact_hash = _HASH
    dependency_hash = _HASH
    supported_hooks = ("on_bar",)

    def evaluate_vectorized(
        self,
        market: Any,
        indicators: Any,
        config: Any,
        context: Any,
        account_snapshot: Any,
    ) -> Any:
        """Evaluate vectorized market dataset and propose decisions."""
        del indicators, config, account_snapshot
        df = pd.DataFrame(
            [
                {
                    "timestamp": r.timestamp,
                    "symbol": market.symbol,
                    "close": float(r.close),
                }
                for r in market.records
            ]
        )
        df["fast_ma"] = df["close"].rolling(10).mean()
        df["slow_ma"] = df["close"].rolling(20).mean()
        df["prev_fast"] = df["fast_ma"].shift(1)
        df["prev_slow"] = df["slow_ma"].shift(1)

        decisions = []
        for i, row in df.iterrows():
            if pd.isna(row["fast_ma"]) or pd.isna(row["slow_ma"]):
                continue
            if row["fast_ma"] > row["slow_ma"] and row["prev_fast"] <= row["prev_slow"]:
                decisions.append(
                    create_strategy_decision(
                        decision_id=f"usage-vec-buy-{i}",
                        sequence=i,
                        action="PROPOSE",
                        symbol=market.symbol,
                        side="BUY",
                        intent_type="OPEN",
                        order_type="MARKET",
                        requested_sizing_mode="quantity",
                        quantity_hint=Decimal("0.10"),
                        valid_from=context.decision_timestamp,
                        expires_at=context.decision_timestamp + timedelta(minutes=5),
                        allow_partial_fills=False,
                        rationale_refs=("fast_ma_crossed_above_slow_ma",),
                        diagnostic_facts={
                            "close": str(row["close"]),
                            "fast_ma": str(row["fast_ma"]),
                            "slow_ma": str(row["slow_ma"]),
                        },
                        lineage={
                            "strategy_id": self.strategy_id,
                            "strategy_version": self.strategy_version,
                            "config_hash": _HASH,
                        },
                    )
                )
            elif (
                row["fast_ma"] < row["slow_ma"] and row["prev_fast"] >= row["prev_slow"]
            ):
                decisions.append(
                    create_strategy_decision(
                        decision_id=f"usage-vec-sell-{i}",
                        sequence=i,
                        action="PROPOSE",
                        symbol=market.symbol,
                        side="SELL",
                        intent_type="OPEN",
                        order_type="MARKET",
                        requested_sizing_mode="quantity",
                        quantity_hint=Decimal("0.10"),
                        valid_from=context.decision_timestamp,
                        expires_at=context.decision_timestamp + timedelta(minutes=5),
                        allow_partial_fills=False,
                        rationale_refs=("fast_ma_crossed_below_slow_ma",),
                        diagnostic_facts={
                            "close": str(row["close"]),
                            "fast_ma": str(row["fast_ma"]),
                            "slow_ma": str(row["slow_ma"]),
                        },
                        lineage={
                            "strategy_id": self.strategy_id,
                            "strategy_version": self.strategy_version,
                            "config_hash": _HASH,
                        },
                    )
                )
        return tuple(decisions)

    def on_bar(
        self,
        ref: Any,
        config: Any,
        event: Any,
        context: Any,
        local_state: Any = None,
        account_snapshot: Any = None,
    ) -> Any:
        """Evaluate single bar event hook."""
        del ref, account_snapshot
        seq = event.sequence
        is_signal_bar = seq % 10 == 0
        if is_signal_bar:
            decision = create_strategy_decision(
                decision_id=f"evt-dec-{seq}",
                sequence=seq,
                action="PROPOSE",
                symbol=config.strategy_id,
                side="BUY",
                intent_type="OPEN",
                order_type="MARKET",
                requested_sizing_mode="quantity",
                quantity_hint=Decimal("0.10"),
                valid_from=context.decision_timestamp,
                expires_at=context.decision_timestamp + timedelta(minutes=5),
                allow_partial_fills=False,
                rationale_refs=("event-bar-observation",),
                diagnostic_facts={"sequence": str(seq)},
                lineage={
                    "strategy_id": self.strategy_id,
                    "strategy_version": self.strategy_version,
                    "config_hash": _HASH,
                },
            )
        else:
            decision = create_strategy_decision(
                decision_id=f"evt-dec-{seq}",
                sequence=seq,
                action="NEUTRAL",
                symbol=None,
                side=None,
                intent_type=None,
                order_type=None,
                requested_sizing_mode=None,
                quantity_hint=None,
                valid_from=context.decision_timestamp,
                expires_at=context.decision_timestamp + timedelta(minutes=5),
                allow_partial_fills=False,
                rationale_refs=("event-bar-observation",),
                diagnostic_facts={"sequence": str(seq)},
                lineage={
                    "strategy_id": self.strategy_id,
                    "strategy_version": self.strategy_version,
                    "config_hash": _HASH,
                },
            )
        updated_state = dict(local_state or {})
        updated_state["bars_seen"] = int(updated_state.get("bars_seen", 0)) + 1
        return decision, updated_state


def _build_strategy_setup(market: Any, timing_key: str) -> tuple[Any, Any, Any]:
    """Construct canonical strategy reference, config, and context for evaluation.

    Args:
        market: Input market dataset.
        timing_key: Timing policy identifier ("BAR_OPEN_PREVIOUS_CLOSE" or "EVENT_DRIVEN").

    Returns:
        Tuple of (ValidatedStrategyRef, ValidatedStrategyConfig, StrategyExecutionContext).
    """
    request_id = generate_id("req")
    workflow_id = generate_id("wf")
    correlation_id = generate_id("cor")

    policy = build_development_strategy_validation_policy()
    timing = get_strategy_timing_policy(timing_key)
    environment = get_strategy_environment("RESEARCH")
    lifecycle = get_strategy_lifecycle_status("APPROVED")

    context = create_strategy_execution_context(
        environment=environment,
        decision_timestamp=market.available_at,
        timing_policy=timing,
        seed=42,
        interface_version="v1",
        request_id=request_id,
        workflow_id=workflow_id,
        correlation_id=correlation_id,
        dependency_status={"data": "ready", "indicators": "ready"},
        snapshot_refs=(market.request_id,),
        max_diagnostic_bytes=8_192,
    )
    manifest = create_strategy_manifest(
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        module_path=_MODULE,
        owner_ref="legacy-strategy-usage",
        interface_version="v1",
        config_schema_version="v1",
        config_schema={"type": "object"},
        required_data=("EURUSD:H1",),
        required_indicators=(),
        timing_policy=timing,
        permitted_environments=(environment,),
        source_hash=_HASH,
        artifact_hash=_HASH,
        dependency_hash=_HASH,
        provenance_refs=(market.request_id,),
        supported_hooks=("on_bar",),
        requires_account_snapshot=False,
        max_batch_records=10_000,
        max_diagnostic_bytes=8_192,
        max_checkpoint_bytes=8_192,
        max_local_state_bytes=8_192,
        decision_timeout_seconds=5,
    )
    ref = create_validated_strategy_ref(
        manifest=manifest,
        lifecycle_status=lifecycle,
        environment=environment,
        policy_version=policy.policy_version,
        validation_policy=policy,
        registry_record_hash=_HASH,
        request_id=request_id,
        correlation_id=correlation_id,
    )
    config = create_validated_strategy_config(
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        config_schema_version="v1",
        normalized_parameters={
            "fast_period": 10,
            "slow_period": 20,
            "symbol": "EURUSD",
        },
        config_hash=_HASH,
        policy_version=policy.policy_version,
        request_id=request_id,
    )
    return ref, config, context


def example_01_vectorized_execution() -> None:
    """Run vectorized strategy evaluation on real MT5 EURUSD H1 data."""
    _header("Example 1: Vectorized Strategy Execution (MT5 EURUSD H1)")
    dataset = _get_dataset(timeframe="H1", limit=100)
    if dataset is None:
        print("\nUnavailable -> MT5 EURUSD H1 bars offline or disabled")
        return

    ref, config, context = _build_strategy_setup(dataset, "BAR_OPEN_PREVIOUS_CLOSE")
    evaluator = LegacyTrendStrategyEvaluator()

    result = run_vectorized_strategy_signals(
        ref=ref,
        config=config,
        market=dataset,
        indicators=(),
        context=context,
        evaluator=evaluator,
    )

    print(f"\nVectorized Execution Status: {result.status}")

    if result.data is not None:
        exec_res = result.data
        print(f"\nTotal Decisions Generated: {len(exec_res.decisions)}")
        print(f"Total TradeIntents Emitted: {len(exec_res.intents)}")

        decisions_df = pd.DataFrame(
            [
                {
                    "decision_id": d.decision_id,
                    "sequence": d.sequence,
                    "symbol": d.symbol,
                    "side": d.side,
                    "intent_type": d.intent_type,
                    "qty_hint": float(d.quantity_hint)
                    if d.quantity_hint is not None
                    else None,
                    "rationale": ", ".join(d.rationale_refs),
                    "close": d.diagnostic_facts.get("close"),
                    "fast_ma": d.diagnostic_facts.get("fast_ma"),
                    "slow_ma": d.diagnostic_facts.get("slow_ma"),
                }
                for d in exec_res.decisions
            ]
        )

        print(
            f"\nStrategy Decisions DataFrame (non-zero entry/exit signals):\n{decisions_df.to_string()}\n"
        )

        for i, intent in enumerate(exec_res.intents, 1):
            print(
                f"  Intent #{i}: {intent.side} {intent.intent_type} symbol={intent.symbol} "
                f"qty_hint={intent.quantity_hint} intent_id={intent.intent_id}"
            )


def example_02_event_driven_simulation() -> None:
    """Run event-driven bar-by-bar replay simulation using real MT5 EURUSD H1 data."""
    _header("Example 2: Event-Driven Bar Replay Simulation (MT5 EURUSD H1)")
    dataset = _get_dataset(timeframe="H1", limit=100)
    if dataset is None:
        print("\nUnavailable -> MT5 EURUSD H1 bars offline or disabled")
        return

    ref, config, context = _build_strategy_setup(dataset, "EVENT_DRIVEN")
    evaluator = LegacyTrendStrategyEvaluator()

    total_events = 0
    total_decisions = 0
    local_state: dict[str, Any] = {"bars_seen": 0}

    for i, record in enumerate(dataset.records):
        event = create_strategy_event(
            event_type="BAR_CLOSED",
            hook="on_bar",
            occurred_at=record.timestamp,
            sequence=i,
            source_owner="data",
            source_contract_version=dataset.contract_version,
            source_schema_id=dataset.schema_id,
            source_snapshot_ref=dataset.request_id,
            source_checksum=_HASH,
            source_as_of=record.timestamp,
            facts={"symbol": dataset.symbol, "close": str(record.close)},
            request_id=context.request_id,
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )
        result = run_event_strategy_hook(
            ref=ref,
            config=config,
            event=event,
            context=context,
            evaluator=evaluator,
            local_state=local_state,
        )
        total_events += 1
        if result.data is not None:
            decision, local_state = result.data
            if decision.side != "NEUTRAL":
                total_decisions += 1
                print(
                    f"  [Bar {i} - {record.timestamp}] Proposed Decision: {decision.side} {decision.intent_type} "
                    f"qty_hint={decision.quantity_hint} decision_id={decision.decision_id}"
                )

    print("\nEvent-Driven Simulation Completed:")
    print(f"  Processed Bars: {total_events}")
    print(f"  Signals Generated: {total_decisions}")
    print(f"  Final Strategy State: {local_state}")


def main() -> None:
    """Execute all Strategy public boundary usage examples.

    Returns:
        None.
    """
    parser = argparse.ArgumentParser(
        description="Direct, copyable usage catalogue for the Strategy service public API using real MT5 data."
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip external provider reads for deterministic validation.",
    )
    args = parser.parse_args()

    with _provider_runtime_context(offline=args.offline):
        example_01_vectorized_execution()
        example_02_event_driven_simulation()


if __name__ == "__main__":
    main()
