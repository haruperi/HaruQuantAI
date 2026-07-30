"""Execute the concrete Strategy signal boundary with genuine MT5 and RSI evidence."""

from __future__ import annotations

import hashlib
import inspect
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import get_market_data, get_symbol_metadata, to_ohlcv_dataframe
from app.services.indicators import get_indicator_result_values, rsi
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


def _header(title: str) -> None:
    """Print one example heading.

    Args:
        title: Reader-facing heading.
    """
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def fr_str_047() -> None:
    """Demonstrate atomic concrete signal evaluation."""
    _header("Demonstrate atomic concrete signal evaluation.")
    assert callable(evaluate_strategy_signals)


def fr_str_048() -> None:
    """Demonstrate the structural signal evaluator contract."""
    _header("Demonstrate the structural signal evaluator contract.")
    assert callable(create_strategy_evaluator)


def _source_hash() -> str:
    """Hash the concrete evaluator source selected through the public factory.

    Returns:
        SHA-256 hash of the actual registered evaluator source.
    """
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


def main() -> int:  # noqa: PLR0911
    """Evaluate real RSI evidence and show the hash-binding failure path.

    Returns:
        ``0`` on success, ``3`` when genuine provider evidence is unavailable,
        otherwise ``1`` for a Strategy functional failure.
    """
    fr_str_047()
    fr_str_048()
    print("\nCONCRETE SIGNAL EVALUATION — GENUINE MT5 EURUSD H1 + RSI")
    request_end = datetime.now(UTC) - timedelta(hours=2)
    try:
        market_response = get_market_data(
            source_id="mt5",
            symbol="EURUSD",
            timeframe="H1",
            start=request_end - timedelta(days=30),
            end=request_end,
            limit=300,
            use_cache=False,
            quality_failure_behavior="warn",
        )
        metadata_response = get_symbol_metadata(source_id="mt5", symbol="EURUSD")
    except (OSError, RuntimeError, ValueError) as error:
        print("Genuine MT5 evidence unavailable:", type(error).__name__)
        return _UNAVAILABLE
    if market_response.data is None or metadata_response.data is None:
        print(
            "Genuine MT5 evidence unavailable:",
            market_response.error or metadata_response.error,
        )
        return _UNAVAILABLE
    market = market_response.data
    metadata = metadata_response.data
    frame_response = to_ohlcv_dataframe(market)
    if frame_response.data is None:
        print("MT5 frame projection failed:", frame_response.error)
        return 1
    print("\nGenuine input bars:")
    print(frame_response.data.tail(10).to_string())

    indicator_response = rsi(market, period=14)
    if indicator_response.data is None:
        print("Official RSI calculation failed:", indicator_response.error)
        return 1
    indicator = indicator_response.data
    print("\nOfficial RSI evidence:")
    print(
        get_indicator_result_values(indicator)[["rsi_14", "available_at"]]
        .tail(10)
        .to_string()
    )

    source_hash = _source_hash()
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
    evaluator = create_strategy_evaluator(
        _EVALUATOR_NAME,
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        module_path=_MODULE,
        source_hash=source_hash,
        artifact_hash=source_hash,
        dependency_hash=source_hash,
    )

    print("\n-- Registry-bound concrete execution --")
    outcome = evaluate_strategy_signals(
        ref,
        config,
        evidence,
        (indicator,),
        context,
        evaluator,
    )
    if outcome.data is None:
        print("Boundary rejected genuine evidence:", outcome.error)
        return 1
    for signal in outcome.data:
        print(signal.model_dump(mode="json"))

    print("\n-- Hash binding fails closed --")
    unbound = create_strategy_evaluator(
        _EVALUATOR_NAME,
        strategy_id=_STRATEGY,
        strategy_version="1.0.0",
        module_path=_MODULE,
        source_hash="0" * 64,
        artifact_hash="0" * 64,
        dependency_hash="0" * 64,
    )
    rejected = evaluate_strategy_signals(
        ref,
        config,
        evidence,
        (indicator,),
        context,
        unbound,
    )
    print(
        "Rejected:",
        rejected.status,
        rejected.error.code if rejected.error else None,
    )
    if (
        rejected.error is None
        or rejected.error.code != "STRATEGY_ARTIFACT_HASH_MISMATCH"
    ):
        return 1
    print("\nSignals are evidence only; they authorize no execution.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
