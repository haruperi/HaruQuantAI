"""Executable examples for every strategy in the Strategy signal library.

A strategy is catalogue content, not a Strategy feature. This single program is
the usage evidence for the whole ``services.strategy.evaluators`` library: each
``example_NN_*`` function evaluates one registered strategy against real MT5
evidence through the public ``evaluate_strategy_signals`` boundary.
"""

import hashlib
import inspect
import os
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import pandas as pd
from app.services.data import get_market_data, get_symbol_metadata
from app.services.data.contracts import DataError
from app.services.indicators import IndicatorError, atr, rsi, sma
from app.services.strategy import (
    DecomposingTradeEvaluator,
    HarrietHedgingEvaluator,
    MarketStructureEvaluator,
    NaiveMATrendEvaluator,
    RandomWalkEvaluator,
    SignalEvaluator,
    SQXBreakoutAtrTrailingEvaluator,
    StrategyEnvironment,
    StrategyExecutionContext,
    StrategyLifecycleStatus,
    StrategyManifest,
    StrategySignalEvidence,
    StrategyTimingPolicy,
    StrategyValidationPolicy,
    ValidatedStrategyConfig,
    ValidatedStrategyRef,
    WhiteFairyEvaluator,
    evaluate_strategy_signals,
)
from app.utils import canonical_json

_UNAVAILABLE = 3
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
_AUDIT_BARS = int(os.getenv("STRATEGY_AUDIT_BARS", "120"))
_AUDIT_WINDOW = 260
_AUDIT_DIR = Path(__file__).resolve().parent / "signal_audit"
_MODULE_ROOT = "app.services.strategy.evaluators"
_POLICY = StrategyValidationPolicy(
    policy_version="usage-v1",
    approved_module_roots=(_MODULE_ROOT,),
    max_config_payload_bytes=4_096,
    max_config_nesting_depth=8,
    max_config_string_length=128,
    max_config_collection_items=64,
)


def _context(name: str) -> StrategyExecutionContext:
    """Build one fixed deterministic evaluation context.

    Args:
        name: Short example identifier used in trace identifiers.

    Returns:
        A complete immutable execution context.
    """
    return StrategyExecutionContext(
        environment=StrategyEnvironment.RESEARCH,
        decision_timestamp=datetime.now(UTC),
        timing_policy=StrategyTimingPolicy.BAR_OPEN_PREVIOUS_CLOSE,
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
    evaluator_type: type,
    strategy_id: str,
    parameters: dict[str, object],
    context: StrategyExecutionContext,
    provenance_ref: str,
    required_indicators: tuple[str, ...],
) -> tuple[ValidatedStrategyRef, ValidatedStrategyConfig, SignalEvaluator]:
    """Build the exact registry reference, configuration, and bound evaluator.

    Args:
        evaluator_type: Concrete evaluator class from the library.
        strategy_id: Registered strategy identifier.
        parameters: Declarative normalized parameters.
        context: Fixed deterministic evaluation context.
        provenance_ref: Real evidence reference recorded as provenance.
        required_indicators: Ordered required indicator identifiers.

    Returns:
        The validated reference, validated configuration, and hash-bound
        evaluator instance.
    """
    source_hash = hashlib.sha256(inspect.getsource(evaluator_type).encode()).hexdigest()
    config_hash = hashlib.sha256(canonical_json(parameters).encode()).hexdigest()
    module_path = f"{_MODULE_ROOT}.{evaluator_type.__module__.rsplit('.', 1)[-1]}"
    manifest = StrategyManifest(
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
    ref = ValidatedStrategyRef(
        manifest=manifest,
        lifecycle_status=StrategyLifecycleStatus.APPROVED,
        environment=context.environment,
        policy_version=_POLICY.policy_version,
        validation_policy=_POLICY,
        registry_record_hash=config_hash,
        request_id=context.request_id,
        correlation_id=context.correlation_id,
    )
    config = ValidatedStrategyConfig(
        strategy_id=strategy_id,
        strategy_version="1.0.0",
        config_schema_version="v1",
        normalized_parameters=parameters,
        config_hash=config_hash,
        policy_version=_POLICY.policy_version,
        request_id=context.request_id,
    )
    evaluator = evaluator_type(
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
) -> StrategySignalEvidence:
    """Build immutable point-in-time signal evidence.

    Args:
        market: Primary Data-owned market dataset.
        point: Explicit instrument point size.
        related: Named related datasets keyed by timeframe name.
        tags: Active owned-position tags.

    Returns:
        Complete immutable signal evidence.
    """
    return StrategySignalEvidence(
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
    slug: str,
    evaluator_type: type,
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
        slug: Filename-safe strategy identifier.
        evaluator_type: Concrete evaluator class from the library.
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
        except IndicatorError as error:
            failures[type(error).__name__] = failures.get(type(error).__name__, 0) + 1
            continue
        context = _context(slug)
        ref, config, evaluator = _binding(
            evaluator_type,
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
                series = result.values[column]  # noqa: PD011
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
    _AUDIT_DIR.mkdir(exist_ok=True)
    csv_path = _AUDIT_DIR / f"{slug}.csv"
    frame.to_csv(csv_path)
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
    print("Full frame written to:", csv_path)
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
        NaiveMATrendEvaluator,
        "naive-ma-trend",
        {"fast_ma_period": 20, "slow_ma_period": 50, "filter_ma_period": 200},
        lambda slice_: (
            sma(slice_, period=20),
            sma(slice_, period=50),
            sma(slice_, period=200),
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
        DecomposingTradeEvaluator,
        "decomposing-trade",
        {"rsi_period": 14, "overbought": "70", "oversold": "30"},
        lambda slice_: (rsi(slice_, period=14),),
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
        WhiteFairyEvaluator,
        "white-fairy",
        {"rsi_period": 14, "overbought": "70", "oversold": "30"},
        lambda slice_: (rsi(slice_, period=14),),
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
        SQXBreakoutAtrTrailingEvaluator,
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
        lambda slice_: (atr(slice_, period=14),),
        ("atr",),
        market,
        point,
    )


def example_05_harriet_hedging(  # noqa: C901
    market: object, point: Decimal
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
        higher = get_market_data(
            source_id="mt5",
            symbol="EURUSD",
            timeframe="H4",
            limit=500,
            use_cache=False,
            quality_failure_behavior="warn",
        )
    except DataError as error:
        print("Higher-timeframe evidence unavailable:", error.code)
        return _UNAVAILABLE
    parameters: dict[str, object] = {
        "lower_timeframe": "lower",
        "higher_timeframe": "higher",
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
            if record.available_at <= signal_time
        ]
        if len(closed) < 3:
            failures["HIGHER_TIMEFRAME_NOT_READY"] = (
                failures.get("HIGHER_TIMEFRAME_NOT_READY", 0) + 1
            )
            continue
        higher_window = _slice(higher, max(0, closed[-1] - 59), closed[-1] + 1)
        context = _context("harriet-hedging")
        ref, config, evaluator = _binding(
            HarrietHedgingEvaluator,
            "harriet-hedging",
            parameters,
            context,
            window.request_id,
            (),
        )
        evidence = _evidence(
            window, point, related={"lower": window, "higher": higher_window}
        )
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
    _AUDIT_DIR.mkdir(exist_ok=True)
    csv_path = _AUDIT_DIR / "harriet_hedging.csv"
    frame.to_csv(csv_path)
    print(f"Audited bars: {len(frame)}  (window {_AUDIT_WINDOW}, no lookahead)")
    if failures:
        print("Skipped bars by reason:", failures)
    with pd.option_context(
        "display.max_columns", None, "display.width", 220, "display.max_rows", 20
    ):
        print(frame.tail(10).to_string())
    print("Full frame written to:", csv_path)
    return 0


def example_06_market_structure(market: object, point: Decimal) -> int:
    """Report why Market Structure fails closed without real ZigZag evidence.

    Args:
        market: Real MT5 market evidence.
        point: Instrument point size.

    Returns:
        Always ``3``: no exported provenance-bound ZigZag provider exists yet.
    """
    del market, point
    print("\n06 MARKET STRUCTURE")
    print("-" * 88)
    print(
        f"{MarketStructureEvaluator.__name__} requires exactly eight externally "
        "supplied, provenance-bound ZigZag extremes. No exported real ZigZag "
        "evidence provider exists, so this strategy fails closed rather than "
        "substituting synthetic extremes. No signal frame can be produced."
    )
    return _UNAVAILABLE


def example_07_random_walk(market: object, point: Decimal) -> int:
    """Report why RandomWalk fails closed without real owned-position tags.

    Args:
        market: Real MT5 market evidence.
        point: Instrument point size.

    Returns:
        Always ``3``: no exported Data-owned position-tag source exists yet.
    """
    del market, point
    print("\n07 RANDOM WALK")
    print("-" * 88)
    print(
        f"{RandomWalkEvaluator.__name__} requires real owned-position tags "
        "derived from a fresh account snapshot. No exported Data-owned "
        "position-tag source exists, so this strategy fails closed. The "
        "recovered source contains no random market-direction signal."
    )
    return _UNAVAILABLE


def main() -> int:
    """Run every strategy example in the library against real MT5 evidence.

    Returns:
        ``0`` when at least one strategy evaluated, or ``3`` when the real MT5
        connection or required receiver-owned evidence is unavailable.
    """
    print("\nSTRATEGY SIGNAL LIBRARY — REAL MT5 EURUSD EVALUATION")
    print("=" * 88)

    start_bound = datetime(2025, 1, 1, 0, 0, tzinfo=UTC)
    end_bound = datetime(2025, 12, 31, 23, 59, tzinfo=UTC)

    try:
        # 500 bars comfortably covers the audit window (260) plus the audited
        # sample (120) with headroom for the 200-period trend filter.
        market = get_market_data(
            source_id="mt5",
            symbol="EURUSD",
            timeframe="H1",
            start=start_bound,
            end=end_bound,
            limit=500,
            use_cache=False,
            quality_failure_behavior="warn",
        )
        metadata = get_symbol_metadata(source_id="mt5", symbol="EURUSD")
    except DataError as error:
        print("Live MT5 evidence unavailable:", error.code)
        return _UNAVAILABLE
    if not isinstance(metadata.point, int | float):
        print("MT5 point-size evidence unavailable:", metadata.point)
        return _UNAVAILABLE
    point = Decimal(str(metadata.point))
    examples = (
        example_01_naive_ma_trend,
        # example_02_decomposing_trade,
        # example_03_white_fairy,
        # example_04_sqx_breakout_atr_trailing,
        # example_05_harriet_hedging,
        # example_06_market_structure,
        # example_07_random_walk,
    )
    evaluated = 0
    for example in examples:
        if example(market, point) == 0:
            evaluated += 1
    print("\n" + "=" * 88)
    print(f"Strategies evaluated with real evidence: {evaluated}/{len(examples)}")
    print("Signals are proposals only; Risk has approved nothing.")
    return 0 if evaluated else _UNAVAILABLE


if __name__ == "__main__":
    raise SystemExit(main())
