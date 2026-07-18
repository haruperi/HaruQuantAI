"""Naive MA Trend concrete signal tests."""

import pytest
from app.services.strategy import NaiveMATrendEvaluator
from app.utils import logger

from tests.strategy.unit.test_models import (
    HASH,
    make_context,
    make_indicator,
    make_market,
    make_signal_config,
    make_signal_evidence,
)


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
            market, indicator_id="sma", output_column="sma_2", values=(1, 1, 3)
        ),
        make_indicator(
            market, indicator_id="sma", output_column="sma_3", values=(2, 2, 2)
        ),
        make_indicator(
            market, indicator_id="sma", output_column="sma_4", values=(1, 1, 1)
        ),
    )
    config = make_signal_config(
        {"fast_ma_period": 2, "slow_ma_period": 3, "filter_ma_period": 4}
    )
    evidence = make_signal_evidence(market)
    first = _evaluator().evaluate_signals(evidence, indicators, config, make_context())
    second = _evaluator().evaluate_signals(evidence, indicators, config, make_context())
    assert first == second
    assert tuple(signal.active for signal in first) == (True, False, False, True)
    with pytest.raises(TypeError):
        first[0].facts["fast_ma"] = "999"  # type: ignore[index]
