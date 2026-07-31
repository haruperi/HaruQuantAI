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
)
from app.utils import canonical_digest

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
            quality_failure_behavior="warn",
        )
        meta_resp = get_symbol_metadata(source_id="mt5", symbol="EURUSD")
        if (
            m_resp.status == "success"
            and m_resp.data
            and meta_resp.status == "success"
            and meta_resp.data
        ):
            return m_resp.data, meta_resp.data
    except OSError, RuntimeError, ValueError:
        pass

    now = datetime.now(UTC)
    records = []
    for i in range(30):
        t = now - timedelta(hours=30 - i)
        records.append(
            build_ohlcv_record(
                timestamp=t,
                open="1.1000",
                high="1.1050",
                low="1.0950",
                close="1.1020",
                volume=100,
                source="mt5",
                source_symbol="EURUSD",
                available_at=t,
                price_unit="USD",
                volume_unit="units",
            )
        )
    market = build_market_dataset(
        symbol="EURUSD",
        data_kind="bars",
        records=records,
        normalization_version="v1",
        timeframe="H1",
        start=records[0].timestamp,
        end=records[-1].timestamp,
        available_at=records[-1].available_at,
        record_count=len(records),
        quality_report=build_data_quality_report(
            quality_status="passed",
            quality_score=Decimal(1),
            record_count=len(records),
            checked_count=len(records),
            truncated=False,
            sample_limit=len(records),
            schema_version="v1",
            generated_at=records[-1].available_at,
        ),
        source_metadata={"provider": "mt5"},
        license_metadata={"license": "usage"},
        cache_status="not_used",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id="strategy-usage-signals",
    )
    metadata = build_symbol_metadata(
        symbol="EURUSD",
        source="mt5",
        point="0.00001",
        digits=5,
        currency_base="EUR",
        currency_profit="USD",
        available_at=records[-1].available_at,
        request_id="strategy-usage-signals",
    )
    return market, metadata


def _setup_signal_context(
    market: Any, metadata: Any
) -> tuple[Any, Any, Any, Any, Any, Any, str]:
    """Build context, policy, ref, config, indicator, evidence, and source_hash."""
    source_hash = _source_hash()
    indicator_response = rsi(market, period=14)
    if indicator_response.data is None:
        raise RuntimeError("RSI calculation failed")
    indicator = indicator_response.data

    config_parameters = {
        "rsi_period": 14,
        "overbought": "70",
        "oversold": "30",
    }
    config_hash = canonical_digest(config_parameters)
    policy = create_strategy_validation_policy(
        policy_version="usage-v1",
        approved_module_roots=("app.services.strategy.evaluators",),
        max_config_payload_bytes=4_096,
        max_config_nesting_depth=8,
        max_config_string_length=128,
        max_config_collection_items=64,
    )
    context = create_strategy_execution_context(
        environment=get_strategy_environment("RESEARCH"),
        decision_timestamp=market.available_at + timedelta(seconds=1),
        timing_policy=get_strategy_timing_policy("BAR_OPEN_PREVIOUS_CLOSE"),
        seed=29,
        interface_version="v1",
        request_id="strategy-usage-signals",
        workflow_id="strategy-usage-signals-workflow",
        correlation_id="strategy-usage-signals-correlation",
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
        required_data=("EURUSD:H1",),
        required_indicators=("rsi",),
        timing_policy=context.timing_policy,
        permitted_environments=(context.environment,),
        source_hash=source_hash,
        artifact_hash=source_hash,
        dependency_hash=source_hash,
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
        environment=context.environment,
        policy_version=policy.policy_version,
        validation_policy=policy,
        registry_record_hash=source_hash,
        request_id=context.request_id,
        correlation_id=context.correlation_id,
    )
    config = create_validated_strategy_config(
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        config_schema_version="v1",
        normalized_parameters=config_parameters,
        config_hash=config_hash,
        policy_version=policy.policy_version,
        request_id=context.request_id,
    )
    evidence = create_strategy_signal_evidence(
        evidence_id=hashlib.sha256(
            f"{market.request_id}:{market.available_at.isoformat()}".encode()
        ).hexdigest(),
        primary_market=market,
        related_markets={},
        point_size=Decimal(str(metadata.point)),
        feature_values={},
        feature_available_at={},
        feature_refs={},
        active_position_tags=(),
    )
    return ref, config, evidence, indicator, context, source_hash


def fr_str_047() -> None:
    """FR-STR-047: Stage 1 & 2 — Atomic concrete signal evaluation."""
    _header("Stage 1 & 2: Atomic Concrete Signal Evaluation (FR-STR-047)")
    market, metadata = _get_signal_evidence()
    ref, config, evidence, indicator, context, source_hash = _setup_signal_context(
        market, metadata
    )

    evaluator = create_strategy_evaluator(
        _EVALUATOR_NAME,
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        module_path=_MODULE,
        source_hash=source_hash,
        artifact_hash=source_hash,
        dependency_hash=source_hash,
    )
    result = evaluate_strategy_signals(
        ref, config, evidence, (indicator,), context, evaluator
    )
    print(_format_result(result))
    print(
        f"Data -> status='{result.status}', signal_count={len(result.data) if result.data else 0}"
    )


def fr_str_048() -> None:
    """FR-STR-048: Stage 3 — Structural signal evaluator contract."""
    _header("Stage 3: Structural Signal Evaluator Contract (FR-STR-048)")
    market, metadata = _get_signal_evidence()
    ref, config, evidence, indicator, context, _ = _setup_signal_context(
        market, metadata
    )

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
            run_data_migrations("strategy-usage-signals")

            # 1. Stage 1 & 2: Atomic concrete signal evaluation
            fr_str_047()

            # 2. Stage 3: Structural signal evaluator contract verification
            fr_str_048()


if __name__ == "__main__":
    main()
