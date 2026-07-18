"""Atomic event-driven Strategy runner tests."""

# ruff: noqa: PT018

from app.services.strategy import EventStrategyEvaluator, run_event_strategy_hook
from app.utils import logger

from tests.strategy.unit.test_models import (
    HASH,
    make_config,
    make_context,
    make_decision,
    make_event,
    make_ref,
)


class Evaluator:
    """Hash-bound deterministic event test evaluator."""

    strategy_id = "mean-reversion"
    strategy_version = "1.0.0"
    module_path = "approved.strategies.mean_reversion"
    source_hash = HASH
    artifact_hash = HASH
    dependency_hash = HASH
    supported_hooks = ("on_bar",)

    def evaluate_event(self, event, config, context, local_state, account_snapshot):
        """Return one neutral decision for supplied event evidence."""
        logger.debug("Evaluating event Strategy test evidence")
        del event, config, context, local_state, account_snapshot
        decision = make_decision(action="NEUTRAL")
        return (decision.model_copy(update={"candidate_local_state": {"counter": 1}}),)


def test_event_evaluator_identity_and_hook_are_verified() -> None:
    """Verify unsupported evaluator hooks fail before invocation."""
    logger.debug("Testing event evaluator hook binding")
    evaluator = Evaluator()
    evaluator.supported_hooks = ("on_tick",)
    outcome = run_event_strategy_hook(
        make_ref(), make_config(), make_event(), make_context(), evaluator
    )
    assert outcome.status == "error"


def test_event_result_commits_state_atomically() -> None:
    """Verify a validated local-state candidate appears only in success."""
    logger.debug("Testing atomic event Strategy local-state result")
    outcome = run_event_strategy_hook(
        make_ref(), make_config(), make_event(), make_context(), Evaluator()
    )
    assert outcome.status == "success"
    assert outcome.data is not None and outcome.data.local_state_update == {
        "counter": 1
    }
    assert isinstance(Evaluator(), EventStrategyEvaluator)
