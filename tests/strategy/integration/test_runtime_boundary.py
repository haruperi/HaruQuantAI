"""WF-STR-007 runtime safety-boundary integration."""

# ruff: noqa: PT018

from app.services.strategy import (
    StrategyTimingPolicy,
    run_vectorized_strategy_signals,
)
from app.utils import logger

from tests.strategy.integration.test_vectorized_workflow import _ProposingEvaluator
from tests.strategy.unit.test_models import make_config, make_context, make_ref
from tests.strategy.unit.test_vectorized_runner import Evaluator, _dataset

_TIMING = StrategyTimingPolicy.BAR_OPEN_PREVIOUS_CLOSE


def test_runtime_boundary_emits_proposals_only() -> None:
    """Verify a prepared runtime evaluation returns proposals and nothing else."""
    logger.debug("Testing WF-STR-007 runtime boundary output")
    outcome = run_vectorized_strategy_signals(
        make_ref(timing=_TIMING),
        make_config(),
        _dataset(),
        (),
        make_context(timing=_TIMING),
        _ProposingEvaluator(),
    )
    assert outcome.status == "success"
    assert outcome.data is not None
    intents = outcome.data.intents
    assert intents
    forbidden = {
        "approval_token",
        "approved_size",
        "broker_order_id",
        "fill_id",
        "fill_price",
        "order_id",
        "risk_approved",
        "risk_decision_id",
    }
    for intent in intents:
        assert not forbidden & set(intent.model_dump(mode="json"))
        assert intent.schema_id == "strategy.trade_intent.v1"


def test_runtime_boundary_neutral_evaluation_ends_workflow() -> None:
    """Verify a neutral runtime evaluation hands Trading no action."""
    logger.debug("Testing WF-STR-007 neutral runtime boundary")
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
