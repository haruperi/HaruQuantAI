"""Execute the concrete Strategy signal boundary with genuine MT5 and RSI evidence."""

from __future__ import annotations

import hashlib
import inspect
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
from tests.strategy.unit.test_models import make_context, make_signal_evidence

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
    """Fetch MT5 evidence or fallback to normalized synthetic dataset and metadata."""
    request_end = datetime.now(UTC) - timedelta(hours=2)
    try:
        m_resp = get_market_data(
            source_id="mt5",
            symbol="EURUSD",
            timeframe="H1",
            start=request_end - timedelta(days=30),
            end=request_end,
            limit=300,
            use_cache=False,
        )
        meta_resp = get_symbol_metadata(source_id="mt5", symbol="EURUSD")
        if (
            getattr(m_resp, "status", None) == "success"
            and getattr(m_resp, "data", None)
            and getattr(meta_resp, "status", None) == "success"
            and getattr(meta_resp, "data", None)
        ):
            print("Successfully acquired real MT5 evidence for EURUSD H1.")
            return m_resp.data, meta_resp.data
    except (RuntimeError, ValueError, KeyError, TypeError, AttributeError) as exc:
        print(f"MT5 query exception encountered: {exc}")

    print("Using synthetic fallback market dataset and symbol metadata.")
    start_time = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    records = []
    base_price = Decimal("1.1000")
    for i in range(100):
        records.append(
            build_ohlcv_record(
                timestamp=start_time + timedelta(hours=i),
                open_price=base_price,
                high_price=base_price + Decimal("0.0020"),
                low_price=base_price - Decimal("0.0020"),
                close_price=base_price + Decimal("0.0010"),
                volume=Decimal(1000),
            )
        )
    ds = build_market_dataset(
        symbol="EURUSD",
        timeframe="H1",
        records=tuple(records),
        quality_report=build_data_quality_report(
            total_records=100,
            missing_count=0,
            duplicate_count=0,
            out_of_order_count=0,
            is_valid=True,
        ),
    )
    meta = build_symbol_metadata(
        symbol="EURUSD",
        asset_class="FX",
        price_precision=5,
        tick_size=Decimal("0.00001"),
        contract_size=Decimal(100000),
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


if __name__ == "__main__":
    main()
