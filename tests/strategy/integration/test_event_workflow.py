"""WF-STR-003 event evaluation integration."""

# ruff: noqa: PT018

from app.services.strategy import run_event_strategy_hook
from app.utils import logger

from tests.strategy.unit.test_event_runner import Evaluator
from tests.strategy.unit.test_models import (
    make_config,
    make_context,
    make_event,
    make_ref,
)


def test_event_workflow() -> None:
    """Run a complete typed event-hook workflow."""
    logger.debug("Testing WF-STR-003 event workflow")
    outcome = run_event_strategy_hook(
        make_ref(), make_config(), make_event(), make_context(), Evaluator()
    )
    assert outcome.data is not None and outcome.data.local_state_update == {
        "counter": 1
    }
