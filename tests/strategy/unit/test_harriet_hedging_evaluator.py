"""Harriet Hedging concrete signal tests."""

from datetime import timedelta

from app.services.strategy import evaluate_strategy_signals
from app.services.strategy.evaluators.harriet_hedging import HarrietHedgingEvaluator
from app.utils import get_logger

from tests.strategy.unit.test_models import (
    HASH,
    make_context,
    make_market,
    make_ref,
    make_signal_config,
    make_signal_evidence,
)

logger = get_logger(__name__)


def test_harriet_uses_only_available_higher_timeframe_bars() -> None:
    """Verify recovered higher-low confirmation uses named point-in-time bars."""
    logger.debug("Testing Harriet point-in-time higher-low confirmation")
    lower = make_market((("2", "4", "1", "3"), ("3", "5", "2", "4")), timeframe="M5")
    higher = make_market((("2", "5", "1", "3"), ("4", "7", "3", "6")), timeframe="H1")
    evidence = make_signal_evidence(lower, related_markets={"H1": higher})
    config = make_signal_config(
        {
            "higher_timeframe": "H1",
            "lower_timeframe": "M5",
            "pip_multiplier": "1",
            "higher_min_distance_pips": "1",
            "lower_min_distance_pips": "1",
        }
    )
    evaluator = HarrietHedgingEvaluator(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        module_path="approved.strategies.mean_reversion",
        source_hash=HASH,
        artifact_hash=HASH,
        dependency_hash=HASH,
    )
    response = evaluator.evaluate_signals(evidence, (), config, make_context())
    assert response.data is not None
    signals = response.data
    assert tuple(signal.active for signal in signals) == (True, False)
    assert signals[0].facts["higher_timeframe"] == "H1"


def test_harriet_accepts_causal_records_retrieved_after_signal_time() -> None:
    """Dataset retrieval time does not make already-closed bars look ahead."""
    lower = make_market((("2", "4", "1", "3"), ("3", "5", "2", "4")))
    closed_lower = lower.records[-1].model_copy(
        update={"available_at": lower.records[-1].timestamp + timedelta(minutes=5)}
    )
    lower = lower.model_copy(
        update={
            "records": (*lower.records[:-1], closed_lower),
            "available_at": make_context().decision_timestamp,
        }
    )
    higher = make_market(
        (("2", "5", "1", "3"), ("4", "7", "3", "6")), timeframe="H1"
    ).model_copy(update={"available_at": make_context().decision_timestamp})
    evidence = make_signal_evidence(lower, related_markets={"M5": lower, "H1": higher})
    config = make_signal_config(
        {
            "higher_timeframe": "H1",
            "lower_timeframe": "M5",
            "pip_multiplier": "1",
            "higher_min_distance_pips": "1",
            "lower_min_distance_pips": "1",
        }
    )
    evaluator = HarrietHedgingEvaluator(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        module_path="approved.strategies.mean_reversion",
        source_hash=HASH,
        artifact_hash=HASH,
        dependency_hash=HASH,
    )

    outcome = evaluate_strategy_signals(
        make_ref(), config, evidence, (), make_context(), evaluator
    )

    assert outcome.status == "success"


def test_harriet_rejects_a_related_record_unavailable_at_signal_time() -> None:
    """A genuinely future higher-timeframe record still fails closed."""
    lower = make_market((("2", "4", "1", "3"), ("3", "5", "2", "4")))
    higher = make_market((("2", "5", "1", "3"), ("4", "7", "3", "6")), timeframe="H1")
    future_record = higher.records[-1].model_copy(
        update={"available_at": lower.records[-1].available_at + timedelta(seconds=1)}
    )
    higher = higher.model_copy(
        update={
            "records": (*higher.records[:-1], future_record),
            "available_at": make_context().decision_timestamp,
        }
    )
    evidence = make_signal_evidence(lower, related_markets={"H1": higher})
    config = make_signal_config(
        {
            "higher_timeframe": "H1",
            "lower_timeframe": "M5",
            "pip_multiplier": "1",
            "higher_min_distance_pips": "1",
            "lower_min_distance_pips": "1",
        }
    )
    evaluator = HarrietHedgingEvaluator(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        module_path="approved.strategies.mean_reversion",
        source_hash=HASH,
        artifact_hash=HASH,
        dependency_hash=HASH,
    )

    outcome = evaluate_strategy_signals(
        make_ref(), config, evidence, (), make_context(), evaluator
    )

    assert outcome.status == "error"
    assert outcome.error is not None
    assert outcome.error.code == "STRATEGY_LOOKAHEAD_DETECTED"
