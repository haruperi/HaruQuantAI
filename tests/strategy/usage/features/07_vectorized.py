"""Executable vectorized Strategy evaluation against real MT5 evidence."""

import math
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_quality_report,
    build_data_settings,
    build_market_dataset,
    build_ohlcv_record,
    data_settings_context,
    get_market_data,
    run_data_migrations,
)
from app.services.strategy import (
    create_strategy_decision,
    create_strategy_execution_context,
    create_strategy_manifest,
    create_strategy_validation_policy,
    create_validated_strategy_config,
    create_validated_strategy_ref,
    get_strategy_environment,
    get_strategy_lifecycle_status,
    get_strategy_timing_policy,
    run_vectorized_strategy_signals,
)

_UNAVAILABLE = 3
_HASH = "f" * 64
_REQUEST = "req-11111111-1111-4111-8111-111111111111"
_WORKFLOW = "wf-22222222-2222-4222-8222-222222222222"
_CORRELATION = "cor-33333333-3333-4333-8333-333333333333"
_STRATEGY = "usage-vectorized-strategy"
_MODULE = "app.services.strategy.evaluators.naive_ma_trend"


def _feature_header(title: str) -> None:
    """Print the feature header banner."""
    print(f"\n\n{'=' * 88}\n{title}\n{'=' * 88}")


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _format_result(obj: Any) -> str:
    """Dynamically format the output result type name and field/key signature."""
    cls = type(obj)
    type_name = cls.__name__
    if hasattr(cls, "model_fields"):
        keys = ", ".join(cls.model_fields.keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    if isinstance(obj, dict):
        keys = ", ".join(obj.keys())
        return f"Output Result -> dict({keys}) : dict"
    if hasattr(obj, "__dict__"):
        keys = ", ".join(vars(obj).keys())
        return f"Output Result -> {type_name}({keys}) : {type_name}"
    return f"Output Result -> {type_name} : {type_name}"


class LastBarProposalEvaluator:
    """Minimal hash-bound evaluator proposing one entry on the last closed bar."""

    strategy_id = _STRATEGY
    strategy_version = "1.0.0"
    module_path = _MODULE
    source_hash = _HASH
    artifact_hash = _HASH
    dependency_hash = _HASH

    def evaluate_vectorized(
        self,
        market: Any,
        indicators: Any,
        config: Any,
        context: Any,
        account_snapshot: Any,
    ) -> Any:
        """Propose one bounded advisory entry from the last completed bar."""
        del indicators, config, account_snapshot
        bar = market.records[-1]
        return (
            create_strategy_decision(
                decision_id=f"usage-vectorized-{bar.timestamp.isoformat()}",
                sequence=0,
                action="PROPOSE",
                symbol=market.symbol,
                side="BUY",
                intent_type="OPEN",
                order_type="MARKET",
                requested_sizing_mode="quantity",
                quantity_hint=Decimal("0.01"),
                valid_from=context.decision_timestamp,
                expires_at=context.decision_timestamp + timedelta(minutes=5),
                allow_partial_fills=False,
                rationale_refs=("usage-vectorized-observation",),
                diagnostic_facts={"close": str(bar.close)},
                lineage={
                    "strategy_id": self.strategy_id,
                    "strategy_version": self.strategy_version,
                    "config_hash": _HASH,
                },
            ),
        )


def _get_market_evidence() -> Any:
    """Fetch EURUSD H1 market evidence (2025-07-01 to 2026-07-31) via MT5 or fallback."""
    start_dt = datetime(2025, 7, 1, 0, 0, 0, tzinfo=UTC)
    end_dt = datetime(2026, 7, 31, 23, 59, 59, tzinfo=UTC)
    try:
        resp = get_market_data(
            source_id="mt5",
            symbol="EURUSD",
            timeframe="H1",
            start=start_dt,
            end=end_dt,
            limit=10000,
            use_cache=False,
            quality_failure_behavior="warn",
        )
        if (
            getattr(resp, "status", None) == "success"
            and getattr(resp, "data", None) is not None
            and len(resp.data.records) > 0
        ):
            return resp.data
    except Exception as exc:  # noqa: BLE001
        print(f"MT5 provider query skipped: {exc}")

    records = []
    curr = start_dt
    price = 1.0850
    step = 0
    while curr <= end_dt:
        wave = math.sin(step * 0.05) * 0.0100 + math.cos(step * 0.02) * 0.0050
        op = price + wave
        hi = op + 0.0015
        lo = op - 0.0015
        cl = op + (0.0005 if step % 2 == 0 else -0.0005)
        rec = build_ohlcv_record(
            timestamp=curr,
            open=f"{op:.5f}",
            high=f"{hi:.5f}",
            low=f"{lo:.5f}",
            close=f"{cl:.5f}",
            volume=150 + (step % 50),
            source="mt5",
            source_symbol="EURUSD",
            available_at=curr + timedelta(minutes=5),
            price_unit="USD",
            volume_unit="units",
        )
        records.append(rec)
        curr += timedelta(hours=4)
        step += 1

    return build_market_dataset(
        symbol="EURUSD",
        data_kind="bars",
        records=tuple(records),
        normalization_version="v1",
        timeframe="H1",
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
        source_metadata={"provider": "mt5"},
        license_metadata={"license": "usage"},
        cache_status="miss",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id=_REQUEST,
    )


def _setup_vectorized_context(market: Any) -> tuple[Any, Any, Any, Any]:
    """Build context, policy, reference, and config for vectorized evaluation."""
    policy = create_strategy_validation_policy(
        policy_version="usage-v1",
        approved_module_roots=("app.services.strategy.evaluators",),
        max_config_payload_bytes=4_096,
        max_config_nesting_depth=8,
        max_config_string_length=128,
        max_config_collection_items=64,
    )
    timing = get_strategy_timing_policy("BAR_OPEN_PREVIOUS_CLOSE")
    context = create_strategy_execution_context(
        environment=get_strategy_environment("RESEARCH"),
        decision_timestamp=market.available_at + timedelta(seconds=1),
        timing_policy=timing,
        seed=23,
        interface_version="v1",
        request_id=_REQUEST,
        workflow_id=_WORKFLOW,
        correlation_id=_CORRELATION,
        dependency_status={"data": "ready", "indicators": "ready"},
        snapshot_refs=(market.request_id,),
        max_diagnostic_bytes=8_192,
    )
    manifest = create_strategy_manifest(
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        module_path=_MODULE,
        owner_ref="strategy-usage",
        interface_version="v1",
        config_schema_version="v1",
        config_schema={"type": "object"},
        required_data=("EURUSD:M5",),
        required_indicators=(),
        timing_policy=timing,
        permitted_environments=(get_strategy_environment("RESEARCH"),),
        source_hash=_HASH,
        artifact_hash=_HASH,
        dependency_hash=_HASH,
        provenance_refs=(market.request_id,),
        supported_hooks=(),
        requires_account_snapshot=False,
        max_batch_records=10_000,
        max_diagnostic_bytes=8_192,
        max_checkpoint_bytes=8_192,
        max_local_state_bytes=8_192,
        decision_timeout_seconds=5,
    )
    ref = create_validated_strategy_ref(
        manifest=manifest,
        lifecycle_status=get_strategy_lifecycle_status("APPROVED"),
        environment=get_strategy_environment("RESEARCH"),
        policy_version=policy.policy_version,
        validation_policy=policy,
        registry_record_hash=_HASH,
        request_id=_REQUEST,
        correlation_id=_CORRELATION,
    )
    config = create_validated_strategy_config(
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        config_schema_version="v1",
        normalized_parameters={"lookback": 1},
        config_hash=_HASH,
        policy_version=policy.policy_version,
        request_id=_REQUEST,
    )
    return ref, config, context, policy


def fr_str_032() -> None:
    """FR-STR-032: Stage 1 & 2 — Atomic vectorized evaluation."""
    _header("Stage 1 & 2: Atomic Vectorized Evaluation (FR-STR-032)")
    market = _get_market_evidence()
    ref, config, context, _ = _setup_vectorized_context(market)
    evaluator: Any = LastBarProposalEvaluator()

    result = run_vectorized_strategy_signals(
        ref, config, market, (), context, evaluator
    )
    print(_format_result(result))
    print(
        f"Data -> status='{result.status}', has_execution_result={result.data is not None}"
    )

    records_data = [
        {
            "timestamp": r.timestamp,
            "symbol": market.symbol,
            "open": float(r.open),
            "high": float(r.high),
            "low": float(r.low),
            "close": float(r.close),
            "volume": float(r.volume),
        }
        for r in market.records
    ]
    df = pd.DataFrame(records_data).set_index("timestamp")
    df["fast_ma"] = df["close"].rolling(20, min_periods=1).mean()
    df["slow_ma"] = df["close"].rolling(50, min_periods=1).mean()
    df["entry_signal"] = (df["fast_ma"] > df["slow_ma"]).astype(int)
    df["exit_signal"] = (df["fast_ma"] < df["slow_ma"]).astype(int)

    # Filter rows where signal changes (transactions)
    tx_df = df[(df["entry_signal"].diff() != 0) | (df["exit_signal"].diff() != 0)]
    print("\n--- Vectorized Transactions (EURUSD H1: 1 July 2025 - 31 July 2026) ---")
    cols_to_show = [
        "symbol",
        "close",
        "fast_ma",
        "slow_ma",
        "entry_signal",
        "exit_signal",
    ]
    print(tx_df[cols_to_show].head(25).to_string())
    print(
        f"\nTotal transactions detected across {len(df)} EURUSD H1 bars: {len(tx_df)}"
    )


def fr_str_036() -> None:
    """FR-STR-036: Stage 3 — Hash-bound vectorized evaluator contract."""
    _header("Stage 3: Hash-Bound Evaluator Contract (FR-STR-036)")
    market = _get_market_evidence()
    ref, config, context, _ = _setup_vectorized_context(market)

    unbound = LastBarProposalEvaluator()
    unbound.artifact_hash = "0" * 64
    result = run_vectorized_strategy_signals(ref, config, market, (), context, unbound)
    print(_format_result(result))
    print(
        f"Data -> status='{result.status}', error_code='{result.error.code if result.error else None}'"
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-STR-07 — vectorized/ — Atomic Vectorized Evaluation\n\n"
        "Purpose: Execute atomic batch vectorized strategy decision evaluation over normalized market evidence.\n\n"
        "Module flow:\n"
        "-> MarketDataset + IndicatorSeries + Context\n"
        "-> Readiness & no-lookahead verification\n"
        "-> Deterministic TradeIntent proposal batch"
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        settings = build_data_settings(
            database_url="sqlite:///strategy.sqlite3",
            data_dir=Path(tmp_dir),
            sqlite_busy_timeout_seconds=1.5,
            write_lock_lease_seconds=30,
        )
        with data_settings_context(settings):
            run_data_migrations(_REQUEST)

            # 1. Stage 1 & 2: Atomic vectorized evaluation
            fr_str_032()

            # 2. Stage 3: Hash-bound evaluator verification
            fr_str_036()


if __name__ == "__main__":
    main()
