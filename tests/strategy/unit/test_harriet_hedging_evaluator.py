"""Harriet Hedging concrete signal tests."""

from app.services.strategy import HarrietHedgingEvaluator
from app.utils import logger

from tests.strategy.unit.test_models import (
    HASH,
    make_context,
    make_market,
    make_signal_config,
    make_signal_evidence,
)


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
    signals = evaluator.evaluate_signals(evidence, (), config, make_context())
    assert tuple(signal.active for signal in signals) == (True, False)
    assert signals[0].facts["higher_timeframe"] == "H1"
