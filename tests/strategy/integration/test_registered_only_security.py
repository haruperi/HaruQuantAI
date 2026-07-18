"""Registered-only evaluator security integration."""

from app.services.strategy import StrategyTimingPolicy, run_vectorized_strategy_signals
from app.utils import logger

from tests.indicators.unit.test_results import _dataset
from tests.strategy.unit.test_models import make_config, make_context, make_ref
from tests.strategy.unit.test_vectorized_runner import Evaluator


def test_unregistered_evaluator_hash_fails_closed() -> None:
    """Verify an unbound evaluator cannot execute despite protocol shape."""
    logger.debug("Testing registered-only Strategy evaluator security")
    evaluator = Evaluator()
    evaluator.source_hash = "f" * 64
    timing = StrategyTimingPolicy.BAR_OPEN_PREVIOUS_CLOSE
    outcome = run_vectorized_strategy_signals(
        make_ref(timing=timing),
        make_config(),
        _dataset(),
        (),
        make_context(timing=timing),
        evaluator,
    )
    assert outcome.status == "error"
