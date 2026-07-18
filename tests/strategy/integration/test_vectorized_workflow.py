"""WF-STR-002 vectorized evaluation integration."""

# ruff: noqa: PT018

from app.services.strategy import StrategyTimingPolicy, run_vectorized_strategy_signals
from app.utils import logger

from tests.indicators.unit.test_results import _dataset
from tests.strategy.unit.test_models import make_config, make_context, make_ref
from tests.strategy.unit.test_vectorized_runner import Evaluator


def test_vectorized_workflow() -> None:
    """Run a complete no-lookahead vectorized workflow."""
    logger.debug("Testing WF-STR-002 vectorized workflow")
    timing = StrategyTimingPolicy.BAR_OPEN_PREVIOUS_CLOSE
    outcome = run_vectorized_strategy_signals(
        make_ref(timing=timing),
        make_config(),
        _dataset(),
        (),
        make_context(timing=timing),
        Evaluator(),
    )
    assert outcome.data is not None and outcome.data.replay_manifest.manifest_hash
