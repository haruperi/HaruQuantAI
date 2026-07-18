"""Atomic vectorized Strategy runner tests."""

# ruff: noqa: PT018

from datetime import timedelta

from app.services.strategy import (
    StrategyTimingPolicy,
    VectorizedStrategyEvaluator,
    run_vectorized_strategy_signals,
)
from app.utils import logger

from tests.indicators.unit.test_results import _dataset
from tests.strategy.unit.test_models import (
    HASH,
    make_config,
    make_context,
    make_decision,
    make_ref,
)


class Evaluator:
    """Hash-bound deterministic vectorized test evaluator."""

    strategy_id = "mean-reversion"
    strategy_version = "1.0.0"
    module_path = "approved.strategies.mean_reversion"
    source_hash = HASH
    artifact_hash = HASH
    dependency_hash = HASH

    def evaluate_vectorized(
        self, market, indicators, config, context, account_snapshot
    ):
        """Return one neutral decision for supplied evidence."""
        logger.debug("Evaluating vectorized Strategy test evidence")
        del market, indicators, config, context, account_snapshot
        return (make_decision(action="NEUTRAL"),)


def test_evaluator_identity_must_match_registry_ref() -> None:
    """Verify hash mismatch fails before market evidence is inspected."""
    logger.debug("Testing vectorized evaluator hash binding")
    evaluator = Evaluator()
    evaluator.artifact_hash = "b" * 64
    outcome = run_vectorized_strategy_signals(
        make_ref(timing=StrategyTimingPolicy.BAR_OPEN_PREVIOUS_CLOSE),
        make_config(),
        _dataset(),
        (),
        make_context(timing=StrategyTimingPolicy.BAR_OPEN_PREVIOUS_CLOSE),
        evaluator,
    )
    assert outcome.status == "error"


def test_any_lookahead_discards_entire_batch() -> None:
    """Verify future Data availability fails before evaluator invocation."""
    logger.debug("Testing vectorized Strategy lookahead rejection")
    context = make_context(timing=StrategyTimingPolicy.BAR_OPEN_PREVIOUS_CLOSE)
    market = _dataset().model_copy(
        update={"available_at": context.decision_timestamp + timedelta(seconds=1)}
    )
    outcome = run_vectorized_strategy_signals(
        make_ref(timing=StrategyTimingPolicy.BAR_OPEN_PREVIOUS_CLOSE),
        make_config(),
        market,
        (),
        context,
        Evaluator(),
    )
    assert outcome.status == "error"


def test_vectorized_runner_returns_atomic_neutral_result() -> None:
    """Verify ready evidence produces one replay-linked atomic result."""
    logger.debug("Testing successful vectorized Strategy evaluation")
    timing = StrategyTimingPolicy.BAR_OPEN_PREVIOUS_CLOSE
    outcome = run_vectorized_strategy_signals(
        make_ref(timing=timing),
        make_config(),
        _dataset(),
        (),
        make_context(timing=timing),
        Evaluator(),
    )
    assert outcome.status == "success"
    assert outcome.data is not None and outcome.data.intents == ()
    assert isinstance(Evaluator(), VectorizedStrategyEvaluator)
