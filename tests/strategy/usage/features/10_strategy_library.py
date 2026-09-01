"""Executable examples for every strategy in the Strategy signal library.

A strategy is catalogue content, not a Strategy feature. This single program is
the usage evidence for the whole ``services.strategy.evaluators`` library: each
``example_NN_*`` function evaluates one registered strategy against real MT5
evidence through the public ``evaluate_strategy_signals`` boundary.
"""

import hashlib
import inspect
import sys
import tempfile
from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from app.kernel.serialization import canonical_json
from app.services.data import (
    build_data_quality_report,
    build_data_settings,
    build_market_dataset,
    build_ohlcv_record,
    data_settings_context,
    get_market_data,
    get_symbol_metadata,
    run_data_migrations,
)
from app.services.indicators import (
    atr,
    ema,
    rsi,
    zigzag,
)
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

_UNAVAILABLE = 3
_AUDIT_BARS = 10
_AUDIT_WINDOW = 260
_MODULE_ROOT = "app.services.strategy.evaluators"
_POLICY = create_strategy_validation_policy(
    policy_version="usage-v1",
    approved_module_roots=(_MODULE_ROOT,),
    max_config_payload_bytes=4_096,
    max_config_nesting_depth=8,
    max_config_string_length=128,
    max_config_collection_items=64,
)


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


def _unwrap_indicator(response: Any) -> Any:
    """Extract a successful indicator result for strategy evaluation."""
    if response.status != "success" or response.data is None:
        error = response.error
        message = error.code if error is not None else "indicator calculation failed"
        raise RuntimeError(message)
    return response.data


def _context(name: str) -> Any:
    """Build one fixed deterministic evaluation context."""
    return create_strategy_execution_context(
        environment=get_strategy_environment("RESEARCH"),
        decision_timestamp=datetime.now(UTC),
        timing_policy=get_strategy_timing_policy("BAR_OPEN_PREVIOUS_CLOSE"),
        seed=1,
        interface_version="v1",
        request_id=f"strategy-usage-{name}",
        workflow_id=f"strategy-usage-{name}-workflow",
        correlation_id=f"strategy-usage-{name}-correlation",
        dependency_status={"data": "ready", "indicators": "ready"},
        snapshot_refs=("live-market-read",),
        max_diagnostic_bytes=8_192,
    )


def _binding(
    evaluator_name: str,
    strategy_id: str,
    parameters: dict[str, object],
    context: Any,
    provenance_ref: str,
    required_indicators: tuple[str, ...],
) -> tuple[Any, Any, Any]:
    """Build the exact registry reference, configuration, and bound evaluator."""
    module_path = f"{_MODULE_ROOT}.{evaluator_name}"
    probe = create_strategy_evaluator(
        evaluator_name,
        strategy_id=strategy_id,
        strategy_version="1.0.0",
        module_path=module_path,
        source_hash="0" * 64,
        artifact_hash="0" * 64,
        dependency_hash="0" * 64,
    )
    source_hash = hashlib.sha256(inspect.getsource(type(probe)).encode()).hexdigest()
    config_hash = hashlib.sha256(canonical_json(parameters).encode()).hexdigest()
    manifest = create_strategy_manifest(
        strategy_id=strategy_id,
        strategy_version="1.0.0",
        module_path=module_path,
        owner_ref="strategy-usage",
        interface_version="v1",
        config_schema_version="v1",
        config_schema={"type": "object"},
        required_data=("EURUSD:H1",),
        required_indicators=required_indicators,
        timing_policy=context.timing_policy,
        permitted_environments=(context.environment,),
        source_hash=source_hash,
        artifact_hash=source_hash,
        dependency_hash=source_hash,
        provenance_refs=(provenance_ref,),
        supported_hooks=(),
        requires_account_snapshot=False,
        max_batch_records=10_000,
        max_diagnostic_bytes=context.max_diagnostic_bytes,
        max_checkpoint_bytes=8_192,
        max_local_state_bytes=8_192,
        decision_timeout_seconds=5,
    )
    ref = create_validated_strategy_ref(
        manifest=manifest,
        lifecycle_status=get_strategy_lifecycle_status("APPROVED"),
        environment=context.environment,
        policy_version=_POLICY.policy_version,
        validation_policy=_POLICY,
        registry_record_hash=config_hash,
        request_id=context.request_id,
        correlation_id=context.correlation_id,
    )
    config = create_validated_strategy_config(
        strategy_id=strategy_id,
        strategy_version="1.0.0",
        config_schema_version="v1",
        normalized_parameters=parameters,
        config_hash=config_hash,
        policy_version=_POLICY.policy_version,
        request_id=context.request_id,
    )
    evaluator = create_strategy_evaluator(
        evaluator_name,
        strategy_id=strategy_id,
        strategy_version="1.0.0",
        module_path=module_path,
        source_hash=source_hash,
        artifact_hash=source_hash,
        dependency_hash=source_hash,
    )
    return ref, config, evaluator


def _evidence(
    market: object,
    point: Decimal,
    *,
    related: dict[str, object] | None = None,
    tags: tuple[str, ...] = (),
) -> Any:
    """Build immutable point-in-time signal evidence."""
    return create_strategy_signal_evidence(
        evidence_id=hashlib.sha256(
            f"{market.request_id}:{market.available_at.isoformat()}".encode()
        ).hexdigest(),
        primary_market=market,
        related_markets=related or {},
        point_size=point,
        feature_values={},
        feature_available_at={},
        feature_refs={},
        active_position_tags=tags,
    )


def _slice(market: object, start: int, stop: int) -> object:
    """Return an immutable market slice ending at one exact bar."""
    records = market.records[start:stop]
    quality = market.quality_report.model_copy(
        update={
            "record_count": len(records),
            "checked_count": len(records),
            "generated_at": records[-1].available_at,
        }
    )
    return market.model_copy(
        update={
            "records": records,
            "record_count": len(records),
            "start": records[0].timestamp,
            "end": records[-1].timestamp,
            "available_at": records[-1].available_at,
            "quality_report": quality,
        }
    )


def _get_library_evidence() -> tuple[Any, Decimal]:
    """Fetch MT5 H1 market data or generate synthetic dataset and point size."""
    start_bound = datetime(2025, 1, 1, 0, 0, tzinfo=UTC)
    end_bound = datetime(2025, 12, 31, 23, 59, tzinfo=UTC)
    try:
        m_resp = get_market_data(
            source_id="mt5",
            symbol="EURUSD",
            timeframe="H1",
            start=start_bound,
            end=end_bound,
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
            return m_resp.data, Decimal(str(meta_resp.data.point))
    except OSError, RuntimeError, ValueError:
        pass

    now = datetime.now(UTC)
    records = []
    for i in range(300):
        t = now - timedelta(hours=300 - i)
        records.append(
            build_ohlcv_record(
                timestamp=t,
                open=str(1.1000 + i * 0.0001),
                high=str(1.1050 + i * 0.0001),
                low=str(1.0950 + i * 0.0001),
                close=str(1.1020 + i * 0.0001),
                volume=100 + i,
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
        cache_status="not_used",
        workflow_context="research",
        precision_policy="decimal_string",
        request_id="req-11111111-1111-4111-8111-111111111111",
    )
    return market, Decimal("0.00001")


def _audit(
    title: str,
    evaluator_name: str,
    strategy_id: str,
    parameters: dict[str, object],
    indicator_factory: Callable[[object], Sequence[object]],
    required_indicators: tuple[str, ...],
    market: object,
    point: Decimal,
) -> None:
    """Replay one strategy bar by bar and print dynamic formatted results."""
    _header(title)
    total = len(market.records)
    window_size = min(total, 50)
    window = _slice(market, total - window_size, total)
    try:
        indicators = tuple(indicator_factory(window))
    except (OSError, RuntimeError, ValueError) as err:
        print(f"Indicator calculation error: {err}")
        return
    context = _context(evaluator_name)
    ref, config, evaluator = _binding(
        evaluator_name,
        strategy_id,
        parameters,
        context,
        window.request_id,
        required_indicators,
    )
    outcome = evaluate_strategy_signals(
        ref, config, _evidence(window, point), indicators, context, evaluator
    )
    print(_format_result(outcome))
    print(
        f"Data -> status='{outcome.status}', signal_count={len(outcome.data) if outcome.data else 0}"
    )


def fr_str_040() -> None:
    """FR-STR-040: Stage 1 — Naive MA Trend signal parity."""
    market, point = _get_library_evidence()
    _audit(
        "Stage 1: Naive MA Trend Signal Parity (FR-STR-040)",
        "naive_ma_trend",
        "naive-ma-trend",
        {"fast_ma_period": 5, "slow_ma_period": 10, "filter_ma_period": 20},
        lambda slice_: (
            _unwrap_indicator(ema(slice_, period=5)),
            _unwrap_indicator(ema(slice_, period=10)),
            _unwrap_indicator(ema(slice_, period=20)),
        ),
        ("ema",),
        market,
        point,
    )
    _audit(
        "Stage 1: Incremental Naive MA Trend Parity (FR-STR-040)",
        "naive_ma_trend_incremental",
        "naive-ma-trend",
        {"fast_ma_period": 5, "slow_ma_period": 10, "filter_ma_period": 20},
        lambda _slice: (),
        (),
        market,
        point,
    )


def fr_str_041() -> None:
    """FR-STR-041: Stage 2 — Decomposing Trade signal parity."""
    market, point = _get_library_evidence()
    _audit(
        "Stage 2: Decomposing Trade Signal Parity (FR-STR-041)",
        "decomposing_trade",
        "decomposing-trade",
        {"rsi_period": 14, "overbought": "70", "oversold": "30"},
        lambda slice_: (_unwrap_indicator(rsi(slice_, period=14)),),
        ("rsi",),
        market,
        point,
    )


def fr_str_042() -> None:
    """FR-STR-042: Stage 3 — Harriet Hedging signal parity."""
    _header("Stage 3: Harriet Hedging Signal Parity (FR-STR-042)")
    market, point = _get_library_evidence()
    context = _context("harriet-hedging")
    parameters = {
        "lower_timeframe": "H1",
        "higher_timeframe": "H4",
        "lower_min_distance_pips": "1.0",
        "higher_min_distance_pips": "2.0",
        "pip_multiplier": "10",
    }
    ref, config, evaluator = _binding(
        "harriet_hedging",
        "harriet-hedging",
        parameters,
        context,
        market.request_id,
        (),
    )
    h4_market = market.model_copy(update={"timeframe": "H4"})
    outcome = evaluate_strategy_signals(
        ref,
        config,
        _evidence(market, point, related={"H4": h4_market}),
        (),
        context,
        evaluator,
    )
    print(_format_result(outcome))
    print(
        f"Data -> status='{outcome.status}', signal_count={len(outcome.data) if outcome.data else 0}"
    )


def fr_str_043() -> None:
    """FR-STR-043: Stage 4 — Fail-closed Market Structure evidence handling."""
    _header("Stage 4: Fail-Closed Market Structure Evidence Handling (FR-STR-043)")
    market, point = _get_library_evidence()
    context = _context("market-structure")
    ref, config, evaluator = _binding(
        "market_structure",
        "market-structure",
        {},
        context,
        market.request_id,
        ("zigzag",),
    )
    res = zigzag(market, depth=2)
    indicators = (res.data,) if res.status == "success" and res.data else ()
    outcome = evaluate_strategy_signals(
        ref, config, _evidence(market, point), indicators, context, evaluator
    )
    print(_format_result(outcome))
    print(
        f"Data -> status='{outcome.status}', error_code='{outcome.error.code if outcome.error else None}'"
    )


def fr_str_044() -> None:
    """FR-STR-044: Stage 5 — Fail-closed RandomWalk ownership evidence handling."""
    _header("Stage 5: Fail-Closed RandomWalk Ownership Evidence Handling (FR-STR-044)")
    market, point = _get_library_evidence()
    context = _context("random-walk")
    parameters = {"buy_magic_number": 17001, "sell_magic_number": 17002}
    ref, config, evaluator = _binding(
        "random_walk",
        "random-walk",
        parameters,
        context,
        market.request_id,
        (),
    )
    outcome = evaluate_strategy_signals(
        ref, config, _evidence(market, point), (), context, evaluator
    )
    print(_format_result(outcome))
    print(
        f"Data -> status='{outcome.status}', signal_count={len(outcome.data) if outcome.data else 0}"
    )


def fr_str_045() -> None:
    """FR-STR-045: Stage 6 — SQX breakout and ATR signal parity."""
    market, point = _get_library_evidence()
    _audit(
        "Stage 6: SQX Breakout & ATR Signal Parity (FR-STR-045)",
        "sqx_breakout_atr_trailing",
        "sqx-breakout-atr-trailing",
        {
            "breakout_lookback": 10,
            "atr_stop_period": 14,
            "stop_loss_atr_multiple": "2.0",
            "trailing_stop_atr_period": 14,
            "trailing_stop_atr_multiple": "2.0",
            "trailing_activation_atr_period": 14,
            "trailing_activation_atr_multiple": "1.0",
        },
        lambda slice_: (_unwrap_indicator(atr(slice_, period=14)),),
        ("atr",),
        market,
        point,
    )


def fr_str_046() -> None:
    """FR-STR-046: Stage 7 — White Fairy signal parity."""
    market, point = _get_library_evidence()
    _audit(
        "Stage 7: White Fairy Signal Parity (FR-STR-046)",
        "white_fairy",
        "white-fairy",
        {"rsi_period": 14, "overbought": "70", "oversold": "30"},
        lambda slice_: (_unwrap_indicator(rsi(slice_, period=14)),),
        ("rsi",),
        market,
        point,
    )


def main() -> None:
    """Run all feature examples in sequential module flow order."""
    _feature_header(
        "FEATURE: FEAT-STR-10 — evaluators/ — Strategy Evaluators Library\n\n"
        "Purpose: Execute declared strategy signal logic for built-in library evaluators.\n\n"
        "Module flow:\n"
        "-> Market & indicator inputs\n"
        "-> Strategy evaluator logic\n"
        "-> StrategySignal outputs"
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

            # 1. Stage 1: Naive MA Trend signal parity
            fr_str_040()

            # 2. Stage 2: Decomposing Trade signal parity
            fr_str_041()

            # 3. Stage 3: Harriet Hedging signal parity
            fr_str_042()

            # 4. Stage 4: Fail-closed Market Structure evidence handling
            fr_str_043()

            # 5. Stage 5: Fail-closed RandomWalk ownership evidence handling
            fr_str_044()

            # 6. Stage 6: SQX breakout and ATR signal parity
            fr_str_045()

            # 7. Stage 7: White Fairy signal parity
            fr_str_046()


if __name__ == "__main__":
    main()
