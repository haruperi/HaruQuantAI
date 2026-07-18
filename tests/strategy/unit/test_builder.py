"""Deterministic TradeIntent builder tests."""

# ruff: noqa: PT018

from app.services.strategy import build_trade_intent
from app.utils import logger

from tests.strategy.unit.test_models import make_context, make_decision


def test_intent_identity_is_stable() -> None:
    """Verify identical decisions and contexts produce identical intent IDs."""
    logger.debug("Testing stable TradeIntent identity")
    first = build_trade_intent(make_decision(), make_context(), 0)
    second = build_trade_intent(make_decision(), make_context(), 0)
    assert first.data is not None and second.data is not None
    assert first.data.intent_id == second.data.intent_id
