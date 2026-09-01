"""Deterministic create_trade_intent_value builder tests."""

# ruff: noqa: PT018
from app.composition.logging import get_logger
from app.services.strategy import build_trade_intent

from tests.strategy.unit.test_models import make_context, make_decision

logger = get_logger(__name__)


def test_intent_identity_is_stable() -> None:
    """Verify identical decisions and contexts produce identical intent IDs."""
    logger.debug("Testing stable create_trade_intent_value identity")
    first = build_trade_intent(make_decision(), make_context(), 0)
    second = build_trade_intent(make_decision(), make_context(), 0)
    assert first.data is not None and second.data is not None
    assert first.data.intent_id == second.data.intent_id
