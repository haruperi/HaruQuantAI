"""Executable examples for every strategy in the Strategy signal library.

A strategy is catalogue content, not a Strategy feature. This single program is
the usage evidence for the whole ``services.strategy.evaluators`` library: each
``example_NN_*`` function evaluates one registered strategy against real MT5
evidence through the public ``evaluate_strategy_signals`` boundary.
"""

import asyncio
import hashlib
import inspect
import os
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import pandas as pd
from app.services.brokers import (
    create_connected_broker,
    disconnect_broker,
    get_broker_connection_environment,
    resolve_provider_connection_config,
)
from app.services.data import (
    build_account_snapshot_request,
    get_account_state_snapshot,
    get_market_data,
    get_symbol_metadata,
    to_ohlcv_dataframe,
    unwrap_data_response,
)
from app.services.indicators import (
    atr,
    get_indicator_result_metadata,
    get_indicator_result_values,
    rsi,
    sma,
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
from app.utils import canonical_json

_UNAVAILABLE = 3


def _unwrap_indicator(response: Any) -> Any:
    """Extract a successful indicator result for strategy evaluation."""
    if response.status != "success" or response.data is None:
        error = response.error
        message = error.code if error is not None else "indicator calculation failed"
        raise RuntimeError(message)
    return response.data


# Signal-audit tuning. Each audited bar re-evaluates the real boundary against
# history truncated at that bar, so cost is roughly O(bars x window). Override
# STRATEGY_AUDIT_BARS to widen or narrow the sample.
#
# The window is 260 for two reasons: the Naive MA Trend filter needs 200 closed
# bars, and an IndicatorResult is cryptographically bound to the dataset it was
# computed on (join_to raises IND_INPUT_MUTATION_DETECTED for a spliced frame),
# so indicators must be recomputed per window rather than sliced from a
# full-history result. 260 bars is ample warmup for period-14 Wilder smoothing
# to converge, keeping audited values equal to full-history values.
def _audit_bar_count() -> int:
    """Return a bounded explicit audit-bar count.

    Returns:
        Integer in the inclusive range 1..120.

    Raises:
        ValueError: If ``STRATEGY_AUDIT_BARS`` is not an integer.
    """
    raw = os.environ.get("STRATEGY_AUDIT_BARS", "120")
    count = int(raw)
    if not 1 <= count <= 120:
        raise ValueError("STRATEGY_AUDIT_BARS must be between 1 and 120")
    return count


_AUDIT_BARS = _audit_bar_count()
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


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _context(name: str) -> create_strategy_execution_context:
    """Build one fixed deterministic evaluation context.

    Args:
        name: Short example identifier used in trace identifiers.

    Returns:
        A complete immutable execution context.
    """
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
    context: create_strategy_execution_context,
    provenance_ref: str,
    required_indicators: tuple[str, ...],
) -> tuple[create_validated_strategy_ref, create_validated_strategy_config, Any]:
    """Build the exact registry reference, configuration, and bound evaluator.

    Args:
        evaluator_name: Stable name in the public evaluator registry.
        strategy_id: Registered strategy identifier.
        parameters: Declarative normalized parameters.
        context: Fixed deterministic evaluation context.
        provenance_ref: Real evidence reference recorded as provenance.
        required_indicators: Ordered required indicator identifiers.

    Returns:
        The validated reference, validated configuration, and hash-bound
        evaluator instance.
    """
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
) -> create_strategy_signal_evidence:
    """Build immutable point-in-time signal evidence.

    Args:
        market: Primary Data-owned market dataset.
        point: Explicit instrument point size.
        related: Named related datasets keyed by timeframe name.
        tags: Active owned-position tags.

    Returns:
        Complete immutable signal evidence.
    """
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
    """Return an immutable market slice ending at one exact bar.

    Args:
        market: Full Data-owned market dataset.
        start: Inclusive start record index.
        stop: Exclusive stop record index.

    Returns:
        A schema-valid dataset containing only the selected records.
    """
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


def _audit(  # noqa: C901
    title: str,
    evaluator_name: str,
    strategy_id: str,
    parameters: dict[str, object],
    indicator_factory: Callable[[object], Sequence[object]],
    required_indicators: tuple[str, ...],
    market: object,
    point: Decimal,
) -> int:
    """Replay one strategy bar by bar and emit its full signal frame.

    Each audited bar is evaluated through the real
    ``evaluate_strategy_signals`` boundary against history truncated at that
    bar, so the frame contains no lookahead.

    Args:
        title: Human-readable strategy name.
        evaluator_name: Stable public evaluator-registry name.
        strategy_id: Registered strategy identifier.
        parameters: Declarative normalized parameters.
        indicator_factory: Builds the ordered indicator tuple for one slice.
        required_indicators: Ordered required indicator identifiers.
        market: Real MT5 market evidence.
        point: Instrument point size.

    Returns:
        ``0`` when the frame was produced, or ``3`` when evidence is missing.
    """
    total = len(market.records)
    if total < _AUDIT_WINDOW + 1:
        print(f"{title}: need at least {_AUDIT_WINDOW + 1} bars, have {total}.")
        return _UNAVAILABLE
    first = max(_AUDIT_WINDOW, total - _AUDIT_BARS)
    rows: list[dict[str, object]] = []
    failures: dict[str, int] = {}
    for index in range(first, total):
        window = _slice(market, index - _AUDIT_WINDOW + 1, index + 1)
        try:
            indicators = tuple(indicator_factory(window))
        except RuntimeError as error:
            failures[type(error).__name__] = failures.get(type(error).__name__, 0) + 1
            continue
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
        if outcome.data is None:
            code = outcome.error.code if outcome.error else "UNKNOWN"
            failures[code] = failures.get(code, 0) + 1
            continue
        bar = window.records[-1]
        row: dict[str, object] = {
            "timestamp": bar.timestamp,
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
        }
        for result in indicators:
            for column in result.output_columns:
                series = get_indicator_result_values(result)[column]
                row[column] = series.iloc[-1]
                # The evaluators compare the current value against the previous
                # one, so both are needed to verify a crossing from one row.
                row[f"prev_{column}"] = series.iloc[-2] if len(series) > 1 else None
        for signal in outcome.data:
            row[f"{signal.signal_name}"] = signal.active
            if signal.side is not None:
                row[f"{signal.signal_name}__side"] = signal.side
            for key, value in signal.facts.items():
                row[f"{signal.signal_name}__{key}"] = value
        rows.append(row)

    print(f"\n{title}")
    print("-" * 88)
    if not rows:
        print("No bar produced signals. Failure codes:", failures or "none")
        return _UNAVAILABLE
    frame = pd.DataFrame(rows).set_index("timestamp")
    signal_columns = [
        column
        for column in frame.columns
        if frame[column].dtype == bool
        or set(frame[column].dropna().unique()) <= {True, False}
    ]
    print(f"Audited bars: {len(frame)}  (window {_AUDIT_WINDOW}, no lookahead)")
    if failures:
        print("Skipped bars by reason:", failures)
    print("Active signal counts:")
    for column in signal_columns:
        print(f"  {column}: {int(frame[column].sum())} active of {len(frame)}")
    with pd.option_context(
        "display.max_columns", None, "display.width", 220, "display.max_rows", 20
    ):
        print(frame.tail(10).to_string())
    return 0


def example_01_naive_ma_trend(market: object, point: Decimal) -> int:
    """Audit Naive MA Trend crossover, trend-filter, and exit signals.

    Args:
        market: Real MT5 market evidence.
        point: Instrument point size.

    Returns:
        ``0`` on success or ``3`` when real evidence is unavailable.
    """
    return _audit(
        "01 NAIVE MA TREND",
        "naive_ma_trend",
        "naive-ma-trend",
        {"fast_ma_period": 20, "slow_ma_period": 50, "filter_ma_period": 200},
        lambda slice_: (
            _unwrap_indicator(sma(slice_, period=20)),
            _unwrap_indicator(sma(slice_, period=50)),
            _unwrap_indicator(sma(slice_, period=200)),
        ),
        ("sma",),
        market,
        point,
    )


def example_02_decomposing_trade(market: object, point: Decimal) -> int:
    """Audit Decomposing Trade RSI entry and opposing-cross signals.

    Args:
        market: Real MT5 market evidence.
        point: Instrument point size.

    Returns:
        ``0`` on success or ``3`` when real evidence is unavailable.
    """
    return _audit(
        "02 DECOMPOSING TRADE",
        "decomposing_trade",
        "decomposing-trade",
        {"rsi_period": 14, "overbought": "70", "oversold": "30"},
        lambda slice_: (_unwrap_indicator(rsi(slice_, period=14)),),
        ("rsi",),
        market,
        point,
    )


def example_03_white_fairy(market: object, point: Decimal) -> int:
    """Audit White Fairy RSI long and short entry crossings.

    Args:
        market: Real MT5 market evidence.
        point: Instrument point size.

    Returns:
        ``0`` on success or ``3`` when real evidence is unavailable.
    """
    return _audit(
        "03 WHITE FAIRY",
        "white_fairy",
        "white-fairy",
        {"rsi_period": 14, "overbought": "70", "oversold": "30"},
        lambda slice_: (_unwrap_indicator(rsi(slice_, period=14)),),
        ("rsi",),
        market,
        point,
    )


def example_04_sqx_breakout_atr_trailing(market: object, point: Decimal) -> int:
    """Audit SQX channel-breakout signals and supplied ATR protection facts.

    Args:
        market: Real MT5 market evidence.
        point: Instrument point size.

    Returns:
        ``0`` on success or ``3`` when real evidence is unavailable.
    """
    return _audit(
        "04 SQX BREAKOUT ATR TRAILING",
        "sqx_breakout_atr_trailing",
        "sqx-breakout-atr-trailing",
        {
            "breakout_lookback": 20,
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


def example_05_harriet_hedging(  # noqa: C901
    market: Any, point: Decimal
) -> int:
    """Audit Harriet Hedging multi-timeframe structure confirmations.

    Args:
        market: Real MT5 lower-timeframe market evidence.
        point: Instrument point size.

    Returns:
        ``0`` on success or ``3`` when higher-timeframe evidence is unavailable.
    """
    print("\n05 HARRIET HEDGING")
    print("-" * 88)
    try:
        higher_response = get_market_data(
            source_id="mt5",
            symbol="EURUSD",
            timeframe="H4",
            start=market.start,
            end=market.end,
            limit=500,
            use_cache=False,
            quality_failure_behavior="warn",
        )
    except Exception as error:  # noqa: BLE001 - bounded standalone evidence path.
        print("Higher-timeframe evidence unavailable:", type(error).__name__)
        return _UNAVAILABLE
    if higher_response.status != "success" or higher_response.data is None:
        print("Higher-timeframe evidence unavailable:", higher_response.error)
        return _UNAVAILABLE
    higher = higher_response.data
    parameters: dict[str, object] = {
        "lower_timeframe": "H1",
        "higher_timeframe": "H4",
        "lower_min_distance_pips": "1.0",
        "higher_min_distance_pips": "2.0",
        "pip_multiplier": "10",
    }
    total = len(market.records)
    if total < _AUDIT_WINDOW + 1:
        print(f"Need at least {_AUDIT_WINDOW + 1} bars, have {total}.")
        return _UNAVAILABLE
    rows: list[dict[str, object]] = []
    failures: dict[str, int] = {}
    for index in range(max(_AUDIT_WINDOW, total - _AUDIT_BARS), total):
        window = _slice(market, index - _AUDIT_WINDOW + 1, index + 1)
        signal_time = window.records[-1].timestamp
        closed = [
            position
            for position, record in enumerate(higher.records)
            if record.timestamp + timedelta(hours=4) <= signal_time
        ]
        if len(closed) < 3:
            failures["HIGHER_TIMEFRAME_NOT_READY"] = (
                failures.get("HIGHER_TIMEFRAME_NOT_READY", 0) + 1
            )
            continue
        higher_window = _slice(higher, max(0, closed[-1] - 59), closed[-1] + 1)
        context = _context("harriet-hedging")
        ref, config, evaluator = _binding(
            "harriet_hedging",
            "harriet-hedging",
            parameters,
            context,
            window.request_id,
            (),
        )
        evidence = _evidence(window, point, related={"H4": higher_window})
        outcome = evaluate_strategy_signals(
            ref, config, evidence, (), context, evaluator
        )
        if outcome.data is None:
            code = outcome.error.code if outcome.error else "UNKNOWN"
            failures[code] = failures.get(code, 0) + 1
            continue
        bar = window.records[-1]
        row: dict[str, object] = {
            "timestamp": bar.timestamp,
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "higher_bar": higher_window.records[-1].timestamp,
        }
        for signal in outcome.data:
            row[signal.signal_name] = signal.active
            if signal.side is not None:
                row[f"{signal.signal_name}__side"] = signal.side
            for key, value in signal.facts.items():
                row[f"{signal.signal_name}__{key}"] = value
        rows.append(row)
    if not rows:
        print("No bar produced signals. Failure codes:", failures or "none")
        return _UNAVAILABLE
    frame = pd.DataFrame(rows).set_index("timestamp")
    print(f"Audited bars: {len(frame)}  (window {_AUDIT_WINDOW}, no lookahead)")
    if failures:
        print("Skipped bars by reason:", failures)
    with pd.option_context(
        "display.max_columns", None, "display.width", 220, "display.max_rows", 20
    ):
        print(frame.tail(10).to_string())
    return 0


def example_06_market_structure(market: object, point: Decimal) -> int:
    """Evaluate Market Structure with official causal ZigZag evidence.

    Args:
        market: Real MT5 market evidence.
        point: Instrument point size.

    Returns:
        ``0`` on success or ``3`` when eight confirmed pivots are unavailable.
    """
    print("\n06 MARKET STRUCTURE")
    print("-" * 88)
    result = _unwrap_indicator(zigzag(market, depth=2))
    if get_indicator_result_values(result)["zigzag_value_2"].count() < 8:
        print("Fewer than eight causal confirmed ZigZag pivots are available.")
        return _UNAVAILABLE
    context = _context("market-structure")
    ref, config, evaluator = _binding(
        "market_structure",
        "market-structure",
        {},
        context,
        market.request_id,
        ("zigzag",),
    )
    evidence = _evidence(market, point)
    outcome = evaluate_strategy_signals(
        ref,
        config,
        evidence,
        (result,),
        context,
        evaluator,
    )
    if outcome.data is None:
        print("Market Structure evaluation failed:", outcome.error)
        return _UNAVAILABLE
    print(
        "ZigZag manifest:",
        get_indicator_result_metadata(result)["manifest"]["output_checksum"],
    )
    for signal in outcome.data:
        print(signal.signal_name, "active=", signal.active)
    return 0


def _real_mt5_account_snapshot() -> Any | None:
    """Read a verified demo MT5 account snapshot through public contracts.

    Returns:
        Fresh immutable account snapshot, or ``None`` when demo evidence is
        unavailable.
    """
    if os.environ.get("ENVIRONMENT", "").lower() not in {"dev", "test"}:
        print("Account evidence blocked outside dev/test.")
        return None
    connection = resolve_provider_connection_config("mt5")
    environment = get_broker_connection_environment(connection)
    if environment != "demo":
        print("Account evidence blocked for non-demo broker environment:", environment)
        return None
    try:
        adapter = asyncio.run(create_connected_broker("mt5"))
    except ValueError as error:
        print("MT5 demo connection unavailable:", type(error).__name__)
        return None
    try:
        account_result = asyncio.run(adapter.get_account_info())
        if account_result.data is None:
            print("MT5 demo account identity unavailable:", account_result.error)
            return None
        request = build_account_snapshot_request(
            source_id="mt5",
            account_id=account_result.data.account_id,
            max_age_seconds=300,
            request_id=account_result.metadata.request_id,
        )
        response = get_account_state_snapshot(request, adapter)
        return unwrap_data_response(
            response,
            operation="strategy.usage.get_account_state_snapshot",
            request_id=response.metadata.request_id,
        )
    finally:
        disconnected = asyncio.run(disconnect_broker(adapter))
        if disconnected.status != "success":
            print("MT5 demo disconnect warning:", disconnected.error)


def example_07_random_walk(market: object, point: Decimal) -> int:
    """Evaluate RandomWalk with a fresh Data-owned demo account snapshot.

    Args:
        market: Real MT5 market evidence.
        point: Instrument point size.

    Returns:
        ``0`` on success or ``3`` when verified demo evidence is unavailable.
    """
    print("\n07 RANDOM WALK")
    print("-" * 88)
    snapshot = _real_mt5_account_snapshot()
    if snapshot is None:
        print("Fresh verified MT5 demo account evidence is unavailable.")
        return _UNAVAILABLE
    observed_tags = tuple(
        f"{position.ownership_ref}:{'BUY' if position.side == 'LONG' else 'SELL'}"
        for position in snapshot.positions
        if position.ownership_ref is not None
    )
    # Multiple broker positions may share one strategy ownership reference and
    # side. Strategy evidence represents active ownership membership, so retain
    # the first observed occurrence rather than inventing position identities.
    tags = tuple(dict.fromkeys(observed_tags))
    context = _context("random-walk")
    parameters = {"buy_magic_number": 17001, "sell_magic_number": 17002}
    ref, config, evaluator = _binding(
        "random_walk",
        "random-walk",
        parameters,
        context,
        snapshot.request_id,
        (),
    )
    outcome = evaluate_strategy_signals(
        ref,
        config,
        _evidence(market, point, tags=tags),
        (),
        context,
        evaluator,
    )
    if outcome.data is None:
        print("RandomWalk evaluation failed:", outcome.error)
        return _UNAVAILABLE
    print(
        "Account snapshot:",
        {
            "request_id": snapshot.request_id,
            "provider_positions": len(snapshot.positions),
            "owned_position_tags": len(observed_tags),
            "unique_position_tags": len(tags),
            "duplicate_position_tags": len(observed_tags) - len(tags),
            "active_tags": tags,
        },
    )
    for signal in outcome.data:
        print(signal.signal_name, "active=", signal.active)
    return 0


def fr_str_040(market: object, point: Decimal) -> int:
    """Demonstrate Naive MA Trend signal parity."""
    return example_01_naive_ma_trend(market, point)


def fr_str_041(market: object, point: Decimal) -> int:
    """Demonstrate Decomposing Trade signal parity."""
    return example_02_decomposing_trade(market, point)


def fr_str_042(market: object, point: Decimal) -> int:
    """Demonstrate Harriet Hedging signal parity."""
    return example_05_harriet_hedging(market, point)


def fr_str_043(market: object, point: Decimal) -> int:
    """Demonstrate fail-closed Market Structure evidence handling."""
    return example_06_market_structure(market, point)


def fr_str_044(market: object, point: Decimal) -> int:
    """Demonstrate fail-closed RandomWalk ownership evidence handling."""
    return example_07_random_walk(market, point)


def fr_str_045(market: object, point: Decimal) -> int:
    """Demonstrate SQX breakout and ATR signal parity."""
    return example_04_sqx_breakout_atr_trailing(market, point)


def fr_str_046(market: object, point: Decimal) -> int:
    """Demonstrate White Fairy signal parity."""
    return example_03_white_fairy(market, point)


def main() -> int:
    """Run every strategy example in the library against real MT5 evidence.

    Returns:
        ``0`` when at least one strategy evaluated, or ``3`` when the real MT5
        connection or required receiver-owned evidence is unavailable.
    """
    print("\nSTRATEGY SIGNAL LIBRARY — REAL MT5 EURUSD EVALUATION")

    start_bound = datetime(2025, 1, 1, 0, 0, tzinfo=UTC)
    end_bound = datetime(2025, 12, 31, 23, 59, tzinfo=UTC)

    try:
        # 500 bars comfortably covers the audit window (260) plus the audited
        # sample (120) with headroom for the 200-period trend filter.
        market_response = get_market_data(
            source_id="mt5",
            symbol="EURUSD",
            timeframe="H1",
            start=start_bound,
            end=end_bound,
            limit=500,
            use_cache=False,
            quality_failure_behavior="warn",
        )
        metadata_response = get_symbol_metadata(source_id="mt5", symbol="EURUSD")
    except Exception as error:  # noqa: BLE001 - bounded standalone evidence path.
        print("Live MT5 evidence unavailable:", type(error).__name__)
        return _UNAVAILABLE
    if market_response.status != "success" or market_response.data is None:
        print("Live MT5 evidence unavailable:", market_response.error)
        return _UNAVAILABLE
    market = market_response.data
    if metadata_response.status != "success" or metadata_response.data is None:
        print("Live MT5 metadata unavailable:", metadata_response.error)
        return _UNAVAILABLE
    metadata = metadata_response.data
    if not isinstance(metadata.point, int | float):
        print("MT5 point-size evidence unavailable:", metadata.point)
        return _UNAVAILABLE
    point = Decimal(str(metadata.point))
    frame_response = to_ohlcv_dataframe(market)
    if frame_response.data is None:
        print("Genuine MT5 frame projection failed:", frame_response.error)
        return 1
    print("\nGenuine MT5 input frame (latest 12 bounded rows):")
    print(frame_response.data.tail(12).to_string())
    print(
        "Input evidence:",
        {
            "request_id": market.request_id,
            "record_count": market.record_count,
            "start": market.start,
            "end": market.end,
            "available_at": market.available_at,
            "point_size": point,
        },
    )
    examples = (
        fr_str_040,
        fr_str_041,
        fr_str_042,
        fr_str_043,
        fr_str_044,
        fr_str_045,
        fr_str_046,
    )
    evaluated = 0
    for example in examples:
        if example(market, point) == 0:
            evaluated += 1
    print("\n" + "=" * 88)
    print(f"Evaluated strategies with real evidence: {evaluated}/{len(examples)}")
    print("Signals are proposals only; Risk has approved nothing.")
    return 0 if evaluated == len(examples) else _UNAVAILABLE


if __name__ == "__main__":
    raise SystemExit(main())
