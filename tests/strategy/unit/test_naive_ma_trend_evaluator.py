"""Naive MA Trend concrete signal tests."""

import pytest
from app.services.strategy.evaluators.naive_ma_trend import NaiveMATrendEvaluator
from app.services.strategy.evaluators.naive_ma_trend_incremental import (
    NaiveMATrendIncrementalEvaluator,
)
from app.utils import get_logger

from tests.strategy.unit.test_models import (
    HASH,
    make_context,
    make_indicator,
    make_market,
    make_signal_config,
    make_signal_evidence,
)

logger = get_logger(__name__)


def _evaluator() -> NaiveMATrendEvaluator:
    """Build the registry-bound Naive evaluator fixture."""
    logger.debug("Building Naive MA Trend evaluator fixture")
    return NaiveMATrendEvaluator(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        module_path="approved.strategies.mean_reversion",
        source_hash=HASH,
        artifact_hash=HASH,
        dependency_hash=HASH,
    )


def test_naive_ma_signals_are_deterministic() -> None:
    """Verify supplied MA evidence yields stable recovered entry and exit signals."""
    logger.debug("Testing deterministic Naive MA Trend signals")
    market = make_market(
        (("1", "2", "0", "1"), ("2", "3", "1", "2"), ("3", "4", "2", "3"))
    )
    indicators = (
        make_indicator(
            market, indicator_id="ema", output_column="ema_2", values=(1, 1, 3)
        ),
        make_indicator(
            market, indicator_id="ema", output_column="ema_3", values=(2, 2, 2)
        ),
        make_indicator(
            market, indicator_id="ema", output_column="ema_4", values=(1, 1, 1)
        ),
    )
    config = make_signal_config(
        {"fast_ma_period": 2, "slow_ma_period": 3, "filter_ma_period": 4}
    )
    evidence = make_signal_evidence(market)
    first = _evaluator().evaluate_signals(evidence, indicators, config, make_context())
    second = _evaluator().evaluate_signals(evidence, indicators, config, make_context())
    assert first.data == second.data
    assert first.data is not None
    assert tuple(signal.active for signal in first.data) == (True, False, False, True)
    with pytest.raises(TypeError):
        first[0].facts["fast_ma"] = "999"  # type: ignore[index]


def test_incremental_naive_ma_matches_batch_signals_across_windows() -> None:
    """Bounded bar evaluation preserves every registered batch signal rule."""
    closes = (
        10,
        9,
        8,
        7,
        6,
        5,
        4,
        3,
        2,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        10,
        9,
        8,
        7,
        6,
    )
    market = make_market(
        tuple((str(value), str(value), str(value), str(value)) for value in closes)
    )
    config = make_signal_config(
        {"fast_ma_period": 5, "slow_ma_period": 10, "filter_ma_period": 20}
    )
    incremental = NaiveMATrendIncrementalEvaluator(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        module_path="approved.strategies.mean_reversion",
        source_hash=HASH,
        artifact_hash=HASH,
        dependency_hash=HASH,
    )
    compact_evaluator = NaiveMATrendIncrementalEvaluator(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        module_path="approved.strategies.mean_reversion",
        source_hash=HASH,
        artifact_hash=HASH,
        dependency_hash=HASH,
    )

    for end in range(20, len(closes) + 1):
        records = market.records[end - 20 : end]
        quality = market.quality_report.model_copy(
            update={"record_count": len(records), "checked_count": len(records)}
        )
        window = market.model_copy(
            update={
                "records": records,
                "record_count": len(records),
                "start": records[0].timestamp,
                "end": records[-1].timestamp,
                "available_at": records[-1].available_at,
                "quality_report": quality,
            }
        )
        values = tuple(float(value) for value in closes[:end])

        def rolling(period: int, source_values: tuple[float, ...]) -> tuple[float, ...]:
            values = [float("nan")] * len(source_values)
            current = sum(source_values[:period]) / period
            values[period - 1] = current
            alpha = 2.0 / (period + 1)
            for index in range(period, len(source_values)):
                current = source_values[index] * alpha + current * (1.0 - alpha)
                values[index] = current
            return tuple(values)

        indicators = tuple(
            make_indicator(
                window,
                indicator_id="ema",
                output_column=f"ema_{period}",
                values=rolling(period, values)[-len(records) :],
            )
            for period in (5, 10, 20)
        )
        evidence = make_signal_evidence(window)
        batch = _evaluator().evaluate_signals(
            evidence, indicators, config, make_context()
        )
        causal = incremental.evaluate_signals(evidence, (), config, make_context())
        assert batch.data is not None
        assert causal.data is not None
        assert tuple((item.signal_name, item.active) for item in causal.data) == tuple(
            (item.signal_name, item.active) for item in batch.data
        )
        compact = frozenset(item.signal_name for item in causal.data if item.active)
        assert compact == compact_evaluator._evaluate_compact(records, config)
