"""Concrete Strategy signal workflow integration tests."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, cast, override

from app.services.strategy import RandomWalkEvaluator, evaluate_strategy_signals
from app.utils import logger

if TYPE_CHECKING:
    from app.services.indicators import IndicatorResult
    from app.services.strategy import (
        StrategyExecutionContext,
        StrategySignal,
        StrategySignalEvidence,
        ValidatedStrategyConfig,
    )

from tests.strategy.unit.test_models import (
    HASH,
    make_context,
    make_market,
    make_ref,
    make_signal_config,
    make_signal_evidence,
)


def _evaluator() -> RandomWalkEvaluator:
    """Build one exact registry-bound concrete evaluator."""
    logger.debug("Building concrete signal workflow evaluator")
    return RandomWalkEvaluator(
        strategy_id="mean-reversion",
        strategy_version="1.0.0",
        module_path="approved.strategies.mean_reversion",
        source_hash=HASH,
        artifact_hash=HASH,
        dependency_hash=HASH,
    )


class _InvalidOutputEvaluator(RandomWalkEvaluator):
    """Registry-bound evaluator returning a deliberately invalid runtime value."""

    @override
    def evaluate_signals(
        self,
        evidence: StrategySignalEvidence,
        indicators: tuple[IndicatorResult, ...],
        config: ValidatedStrategyConfig,
        context: StrategyExecutionContext,
    ) -> tuple[StrategySignal, ...]:
        """Return an invalid object under the declared signal type.

        Args:
            evidence: Point-in-time signal evidence.
            indicators: Official indicator evidence.
            config: Validated configuration.
            context: Fixed evaluation context.

        Returns:
            A deliberately invalid runtime tuple for boundary testing.
        """
        logger.debug("Returning invalid concrete signal output for boundary testing")
        del evidence, indicators, config, context
        return cast("tuple[StrategySignal, ...]", (object(),))


def test_concrete_signal_workflow() -> None:
    """Verify exact registry identity and ready evidence return atomic signals."""
    logger.debug("Testing complete concrete Strategy signal workflow")
    market = make_market((("1", "2", "0", "1"),))
    outcome = evaluate_strategy_signals(
        make_ref(),
        make_signal_config({"buy_magic_number": 10, "sell_magic_number": 20}),
        make_signal_evidence(market),
        (),
        make_context(),
        _evaluator(),
    )
    assert outcome.status == "success"
    assert outcome.data is not None
    assert tuple(signal.signal_name for signal in outcome.data) == (
        "LONG_BASKET_TRIGGER",
        "SHORT_BASKET_TRIGGER",
    )


def test_concrete_signal_workflow_fails_closed_on_hash_mismatch() -> None:
    """Verify evaluator artifact mismatch fails before signal evaluation."""
    logger.debug("Testing concrete signal hash failure")
    market = make_market((("1", "2", "0", "1"),))
    evaluator = _evaluator()
    mismatched = RandomWalkEvaluator(
        strategy_id=evaluator.strategy_id,
        strategy_version=evaluator.strategy_version,
        module_path=evaluator.module_path,
        source_hash=evaluator.source_hash,
        artifact_hash="b" * 64,
        dependency_hash=evaluator.dependency_hash,
    )
    outcome = evaluate_strategy_signals(
        make_ref(),
        make_signal_config({"buy_magic_number": 10, "sell_magic_number": 20}),
        make_signal_evidence(market),
        (),
        make_context(),
        mismatched,
    )
    assert outcome.status == "error"


def test_concrete_signal_workflow_rejects_lookahead() -> None:
    """Verify future market availability fails before evaluator invocation."""
    logger.debug("Testing concrete signal lookahead rejection")
    context = make_context()
    market = make_market((("1", "2", "0", "1"),)).model_copy(
        update={"available_at": context.decision_timestamp + timedelta(seconds=1)}
    )
    outcome = evaluate_strategy_signals(
        make_ref(),
        make_signal_config({"buy_magic_number": 10, "sell_magic_number": 20}),
        make_signal_evidence(market),
        (),
        context,
        _evaluator(),
    )
    assert outcome.status == "error"


def test_concrete_signal_workflow_rejects_invalid_output_contract() -> None:
    """Verify evaluator type violations become structured failures."""
    logger.debug("Testing concrete signal invalid-output rejection")
    market = make_market((("1", "2", "0", "1"),))
    outcome = evaluate_strategy_signals(
        make_ref(),
        make_signal_config({"buy_magic_number": 10, "sell_magic_number": 20}),
        make_signal_evidence(market),
        (),
        make_context(),
        _InvalidOutputEvaluator(
            strategy_id="mean-reversion",
            strategy_version="1.0.0",
            module_path="approved.strategies.mean_reversion",
            source_hash=HASH,
            artifact_hash=HASH,
            dependency_hash=HASH,
        ),
    )
    assert outcome.status == "error"
