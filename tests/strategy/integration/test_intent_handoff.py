"""WF-STR-004 canonical intent handoff integration."""

from app.services.strategy import TradeIntent, build_trade_intent
from app.utils import logger

from tests.strategy.unit.test_models import make_context, make_decision


def test_intent_handoff_workflow() -> None:
    """Build the exact proposal contract handed to downstream Risk."""
    logger.debug("Testing WF-STR-004 intent handoff")
    outcome = build_trade_intent(make_decision(), make_context(), 0)
    assert isinstance(outcome.data, TradeIntent)
    assert not hasattr(outcome.data, "approved")
