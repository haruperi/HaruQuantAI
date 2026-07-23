"""WF-STR-002 vectorized evaluation integration."""

# ruff: noqa: PT018

from datetime import timedelta

from app.services.strategy import (
    StrategyTimingPolicy,
    run_vectorized_strategy_signals,
)
from app.utils import logger

from tests.strategy.unit.test_models import (
    make_config,
    make_context,
    make_decision,
    make_ref,
)
from tests.strategy.unit.test_vectorized_runner import Evaluator, _dataset

_TIMING = StrategyTimingPolicy.BAR_OPEN_PREVIOUS_CLOSE
_SHA256_LENGTH = 64


class _ProposingEvaluator(Evaluator):
    """Evaluator returning two ordered proposals for boundary assertions."""

    def evaluate_vectorized(
        self, market, indicators, config, context, account_snapshot
    ):
        """Return two ordered proposal decisions.

        Returns:
            Two distinct proposal decisions in submission order.
        """
        logger.debug("Evaluating ordered vectorized workflow proposals")
        del market, indicators, config, context, account_snapshot
        first = make_decision()
        second = make_decision().model_copy(
            update={"decision_id": "decision-2", "sequence": 1}
        )
        return (first, second)


def test_vectorized_workflow() -> None:
    """Emit an ordered intent batch with complete replay metadata."""
    logger.debug("Testing WF-STR-002 vectorized workflow output boundary")
    outcome = run_vectorized_strategy_signals(
        make_ref(timing=_TIMING),
        make_config(),
        _dataset(),
        (),
        make_context(timing=_TIMING),
        _ProposingEvaluator(),
    )
    assert outcome.status == "success"
    result = outcome.data
    assert result is not None
    assert len(result.replay_manifest.manifest_hash) == _SHA256_LENGTH
    intents = result.intents
    assert len(intents) == 2
    assert [intent.strategy_sequence for intent in intents] == [0, 1]
    assert len({intent.intent_id for intent in intents}) == 2
    assert len({intent.idempotency_key for intent in intents}) == 2
    forbidden = {"order_id", "fill_id", "risk_approved", "approval_token"}
    assert not forbidden & set(type(intents[0]).model_fields)


def test_vectorized_workflow_neutral_decision_emits_no_intent() -> None:
    """Verify a neutral decision produces an empty intent batch."""
    logger.debug("Testing WF-STR-002 neutral decision boundary")
    outcome = run_vectorized_strategy_signals(
        make_ref(timing=_TIMING),
        make_config(),
        _dataset(),
        (),
        make_context(timing=_TIMING),
        Evaluator(),
    )
    assert outcome.status == "success"
    assert outcome.data is not None and outcome.data.intents == ()


def test_vectorized_workflow_discards_batch_on_lookahead() -> None:
    """Verify any lookahead discards the whole batch and returns no intent."""
    logger.debug("Testing WF-STR-002 fail-closed lookahead behavior")
    context = make_context(timing=_TIMING)
    future = context.decision_timestamp + timedelta(days=1)
    market = _dataset().model_copy(update={"available_at": future})
    outcome = run_vectorized_strategy_signals(
        make_ref(timing=_TIMING),
        make_config(),
        market,
        (),
        context,
        _ProposingEvaluator(),
    )
    assert outcome.status == "error"
    assert outcome.data is None
    assert outcome.error is not None
    assert outcome.error.code == "STRATEGY_LOOKAHEAD_DETECTED"
