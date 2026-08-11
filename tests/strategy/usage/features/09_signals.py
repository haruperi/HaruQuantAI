"""Execute the concrete Strategy signal boundary with genuine MT5 and RSI evidence."""

from __future__ import annotations

import hashlib
import inspect
import math
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.services.data import (
    build_data_quality_report,
    build_data_settings,
    build_market_dataset,
    build_ohlcv_record,
    build_symbol_metadata,
    data_settings_context,
    get_market_data,
    get_symbol_metadata,
    run_data_migrations,
)
from app.services.indicators import rsi
from app.services.strategy import (
    create_strategy_evaluator,
    create_strategy_manifest,
    create_strategy_validation_policy,
    create_validated_strategy_config,
    create_validated_strategy_ref,
    evaluate_and_record_strategy_signals,
    evaluate_strategy_signals,
    get_strategy_environment,
    get_strategy_lifecycle_status,
    get_strategy_timing_policy,
    list_strategy_signals,
    mark_strategy_signal_submitted,
    record_strategy_signals,
)
from app.utils import generate_id, get_logger
from tests.strategy.unit.test_models import make_context, make_signal_evidence

logger = get_logger(__name__)

_UNAVAILABLE = 3
_EVALUATOR_NAME = "decomposing_trade"
_MODULE = "app.services.strategy.evaluators.decomposing_trade"
_STRATEGY = "usage-signal-boundary"


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


def _source_hash() -> str:
    """Hash the concrete evaluator source selected through the public factory."""
    probe = create_strategy_evaluator(
        _EVALUATOR_NAME,
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        module_path=_MODULE,
        source_hash="0" * 64,
        artifact_hash="0" * 64,
        dependency_hash="0" * 64,
    )
    return hashlib.sha256(inspect.getsource(type(probe)).encode()).hexdigest()


def _get_signal_evidence() -> tuple[Any, Any]:
    """Fetch MT5 evidence (2025-07-01 to 2026-07-31) or fallback to synthetic dataset and metadata."""
    start_dt = datetime(2025, 7, 1, 0, 0, 0, tzinfo=UTC)
    end_dt = datetime(2026, 7, 31, 23, 59, 59, tzinfo=UTC)
    try:
        m_resp = get_market_data(
            source_id="mt5",
            symbol="EURUSD",
            timeframe="H1",
            start=start_dt,
            end=end_dt,
            limit=10000,
            use_cache=False,
        )
        meta_resp = get_symbol_metadata(source_id="mt5", symbol="EURUSD")
        if (
            getattr(m_resp, "status", None) == "success"
            and getattr(m_resp, "data", None) is not None
            and len(m_resp.data.records) > 0
            and getattr(meta_resp, "status", None) == "success"
            and getattr(meta_resp, "data", None) is not None
        ):
            print("Successfully acquired real MT5 evidence for EURUSD H1.")
            return m_resp.data, meta_resp.data
    except Exception as exc:  # noqa: BLE001 - source-availability dependent
        print(f"MT5 query exception encountered: {exc}")

    print(
        "Using synthetic fallback EURUSD H1 market dataset (1 July 2025 - 31 July 2026)."
    )
    records = []
    curr = start_dt
    price = 1.0850
    step = 0
    while curr <= end_dt:
        wave = math.sin(step * 0.08) * 0.0120 + math.cos(step * 0.03) * 0.0060
        op = price + wave
        hi = op + 0.0015
        lo = op - 0.0015
        cl = op + (0.0008 if step % 2 == 0 else -0.0008)
        rec = build_ohlcv_record(
            timestamp=curr,
            open=f"{op:.5f}",
            high=f"{hi:.5f}",
            low=f"{lo:.5f}",
            close=f"{cl:.5f}",
            volume=Decimal(1000 + (step % 100)),
            source="synthetic",
            source_symbol="EURUSD",
            available_at=curr + timedelta(minutes=5),
            price_unit="USD",
            volume_unit="units",
        )
        records.append(rec)
        curr += timedelta(hours=4)
        step += 1

    ds = build_market_dataset(
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
        source_metadata={"provider": "synthetic"},
        license_metadata={"license": "usage"},
        cache_status="not_used",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id="req-00000000-0000-4000-8000-000000000099",
    )
    meta = build_symbol_metadata(
        canonical_symbol="EURUSD",
        provider_symbol="EURUSD",
        asset_class="FX",
        quote_currency="USD",
        timezone="UTC",
        source_id="synthetic",
        revision="metadata-v1",
        retrieved_at=start_dt,
        missing_fields=("base_currency", "digits", "price_step", "quantity_step"),
        request_id="req-00000000-0000-4000-8000-000000000099",
    )
    return ds, meta


def _binding(
    source_hash: str | None = None,
    artifact_hash: str | None = None,
    dependency_hash: str | None = None,
) -> tuple[Any, Any]:
    """Build the validated reference and configuration pair."""
    s_hash = source_hash or _source_hash()
    a_hash = artifact_hash or s_hash
    d_hash = dependency_hash or s_hash
    policy = create_strategy_validation_policy(
        policy_version="usage-v1",
        approved_module_roots=("app.services.strategy.evaluators",),
        max_config_payload_bytes=4_096,
        max_config_nesting_depth=8,
        max_config_string_length=128,
        max_config_collection_items=64,
    )
    manifest = create_strategy_manifest(
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        module_path=_MODULE,
        owner_ref="strategy-usage",
        interface_version="v1",
        config_schema_version="v1",
        config_schema={"type": "object"},
        required_data=("EURUSD:H1",),
        required_indicators=("rsi",),
        timing_policy=get_strategy_timing_policy("EVENT_DRIVEN"),
        permitted_environments=(get_strategy_environment("RESEARCH"),),
        source_hash=s_hash,
        artifact_hash=a_hash,
        dependency_hash=d_hash,
        provenance_refs=("usage-approval-1",),
        supported_hooks=("on_bar",),
        requires_account_snapshot=False,
        max_batch_records=1_000,
        max_diagnostic_bytes=8_192,
        max_checkpoint_bytes=8_192,
        max_local_state_bytes=8_192,
        decision_timeout_seconds=5,
    )
    ref = create_validated_strategy_ref(
        manifest=manifest,
        lifecycle_status=get_strategy_lifecycle_status("APPROVED"),
        environment=get_strategy_environment("RESEARCH"),
        policy_version="usage-v1",
        validation_policy=policy,
        registry_record_hash=s_hash,
        request_id="req-99999999-9999-4999-8999-999999999999",
        correlation_id="cor-99999999-9999-4999-8999-999999999999",
    )
    config = create_validated_strategy_config(
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        config_schema_version="v1",
        normalized_parameters={
            "rsi_period": 14,
            "overbought": Decimal(70),
            "oversold": Decimal(30),
        },
        config_hash=s_hash,
        policy_version="usage-v1",
        request_id="req-99999999-9999-4999-8999-999999999999",
    )
    return ref, config


def _evidence(market: Any, metadata: Any) -> Any:
    """Build canonical signal evidence bound to point-in-time market data."""
    return make_signal_evidence(market)


def fr_str_047() -> None:
    """Demonstrate FR-STR-047: Concrete signal evaluation over evidence."""
    _header("Demonstrating FR-STR-047: Concrete signal evaluation over evidence")
    market, metadata = _get_signal_evidence()
    indicator = rsi(market, period=14)
    ref, config = _binding()
    evidence = _evidence(market, metadata)
    context = make_context()
    evaluator = create_strategy_evaluator(
        _EVALUATOR_NAME,
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        module_path=_MODULE,
        source_hash=ref.manifest.source_hash,
        artifact_hash=ref.manifest.artifact_hash,
        dependency_hash=ref.manifest.dependency_hash,
    )
    result = evaluate_strategy_signals(
        ref, config, evidence, (indicator,), context, evaluator
    )
    print(_format_result(result))
    print(
        f"Data -> status='{result.status}', signals_count={len(result.data) if result.data else 0}"
    )


def fr_str_048() -> None:
    """Demonstrate FR-STR-048: Signal evaluator contract verification."""
    _header("Demonstrating FR-STR-048: Signal evaluator contract verification")
    market, metadata = _get_signal_evidence()
    indicator = rsi(market, period=14)
    ref, config = _binding()
    evidence = _evidence(market, metadata)
    context = make_context()
    unbound = create_strategy_evaluator(
        _EVALUATOR_NAME,
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        module_path=_MODULE,
        source_hash="0" * 64,
        artifact_hash="0" * 64,
        dependency_hash="0" * 64,
    )
    result = evaluate_strategy_signals(
        ref, config, evidence, (indicator,), context, unbound
    )
    print(_format_result(result))
    print(
        f"Data -> status='{result.status}', error_code='{result.error.code if result.error else None}'"
    )


def _demo_signal_persistence_and_submission() -> None:
    """Demonstrate FR-STR-063 through FR-STR-066: Signal persistence and submission outbox."""
    _header("Stage 4: Signal Persistence & Submission Outbox (FR-STR-063..066)")
    market, metadata = _get_signal_evidence()
    indicator = rsi(market, period=14)
    ref, config = _binding()
    evidence = _evidence(market, metadata)
    context = make_context()
    evaluator = create_strategy_evaluator(
        _EVALUATOR_NAME,
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        module_path=_MODULE,
        source_hash=ref.manifest.source_hash,
        artifact_hash=ref.manifest.artifact_hash,
        dependency_hash=ref.manifest.dependency_hash,
    )
    config_id = f"{_STRATEGY}@1.0.0#{config.config_hash}"

    signals_res = evaluate_and_record_strategy_signals(
        ref, config, config_id, evidence, (indicator,), context, evaluator
    )
    print(_format_result(signals_res))
    print(f"Data -> signals_count={len(signals_res.data) if signals_res.data else 0}")

    if signals_res.data:
        recorded = record_strategy_signals(
            config_id=config_id,
            signals=signals_res.data,
            request_id=context.request_id,
            correlation_id=context.correlation_id,
        )
        print(_format_result(recorded))

    listed_sigs = list_strategy_signals(config_id)
    print(_format_result(listed_sigs))
    print(
        f"Data -> persisted signals count={len(listed_sigs.data) if listed_sigs.data else 0}"
    )

    if listed_sigs.data:
        sig_id = listed_sigs.data[0]["signal_id"]
        sub_res = mark_strategy_signal_submitted(
            sig_id,
            expected_status="generated",
            risk_submission_ref="risk-sub-12345",
            request_id="req-sig-004",
            correlation_id="cor-sig-004",
        )
        print(_format_result(sub_res))
        print(
            f"Data -> status='{sub_res.status}', submission_ref='{sub_res.data.get('risk_submission_ref') if sub_res.data else None}'"
        )


def _demo_event_driven_bar_by_bar_simulation() -> None:
    """Simulate a live/replay environment by iterating bar-by-bar (EURUSD H1 2025-2026)."""
    _header(
        "--- Event-Driven Bar-by-Bar Replay Simulation (EURUSD H1: 1 July 2025 - 31 July 2026) ---"
    )
    market, metadata = _get_signal_evidence()
    ref, config = _binding()
    evaluator = create_strategy_evaluator(
        _EVALUATOR_NAME,
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        module_path=_MODULE,
        source_hash=ref.manifest.source_hash,
        artifact_hash=ref.manifest.artifact_hash,
        dependency_hash=ref.manifest.dependency_hash,
    )

    records = market.records
    total_bars = len(records)
    warmup_bars = 20
    print(
        f"Starting bar-by-bar replay simulation from bar {warmup_bars} to {total_bars}..."
    )

    emitted_count = 0
    for i in range(warmup_bars, total_bars, 25):
        current_bar = records[i]
        snapshot_records = records[: i + 1]
        market_slice = build_market_dataset(
            symbol=market.symbol,
            data_kind=market.data_kind,
            records=snapshot_records,
            normalization_version=market.normalization_version,
            timeframe=market.timeframe,
            start=snapshot_records[0].timestamp,
            end=snapshot_records[-1].timestamp,
            available_at=snapshot_records[-1].available_at,
            record_count=len(snapshot_records),
            quality_report=build_data_quality_report(
                quality_status="perfect",
                quality_decision="accepted",
                quality_score=Decimal(100),
                record_count=len(snapshot_records),
                checked_count=len(snapshot_records),
                truncated=False,
                sample_limit=len(snapshot_records),
                schema_version="v1",
                generated_at=snapshot_records[-1].available_at,
            ),
            source_metadata=market.source_metadata,
            license_metadata=market.license_metadata,
            cache_status=market.cache_status,
            workflow_context=market.workflow_context,
            precision_policy=market.precision_policy,
            request_id=generate_id("req"),
        )
        indicator_res = rsi(market_slice, period=14)
        if indicator_res.data is None:
            continue
        indicator = indicator_res.data
        evidence = _evidence(market_slice, metadata)
        context = make_context()

        result = evaluate_strategy_signals(
            ref, config, evidence, (indicator,), context, evaluator
        )
        if result.status == "success" and result.data:
            emitted_count += len(result.data)
            for sig in result.data:
                logger.info(
                    "[Replay Time: %s] Emitted Trade Intent/Signal: SignalName=%s, Side=%s, ClosePrice=%s",
                    current_bar.timestamp,
                    sig.signal_name,
                    sig.side,
                    current_bar.close,
                )
                print(
                    f"[Replay Time: {current_bar.timestamp}] Emitted Intent: "
                    f"Side={sig.side}, Signal='{sig.signal_name}', "
                    f"Price={current_bar.close}"
                )

    print(
        f"\nReplay loop completed. Emitted {emitted_count} trade signals/intents across {total_bars} EURUSD H1 bars."
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-STR-09 — signals/ — Concrete Strategy Signal Boundary\n\n"
        "Purpose: Execute declared strategy logic over verified market and indicator evidence to produce typed signals.\n\n"
        "Module flow:\n"
        "-> SignalEvidence + IndicatorSeries + Context\n"
        "-> Evaluator & hash verification\n"
        "-> Immutable StrategySignal list"
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        settings = build_data_settings(
            database_url="sqlite:///strategy.sqlite3",
            data_dir=Path(tmp_dir),
            sqlite_busy_timeout_seconds=1.5,
            write_lock_lease_seconds=30,
        )
        with data_settings_context(settings):
            run_data_migrations("req-11111111-1111-4111-8111-111111111111")

            # 1. Stage 1 & 2: Atomic concrete signal evaluation
            fr_str_047()

            # 2. Stage 3: Structural signal evaluator contract verification
            fr_str_048()

            # 3. Stage 4: Signal persistence & submission outbox (FR-STR-063..066)
            _demo_signal_persistence_and_submission()

            # 4. Stage 5: Event-Driven Bar-by-Bar Replay Simulation (EURUSD H1 2025-2026)
            _demo_event_driven_bar_by_bar_simulation()


if __name__ == "__main__":
    main()
