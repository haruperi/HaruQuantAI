"""WF-STR-004 canonical intent handoff integration."""

from app.composition.logging import get_logger
from app.services.strategy import build_trade_intent

from tests.strategy.unit.test_models import make_context, make_decision

logger = get_logger(__name__)


def test_intent_handoff_workflow() -> None:
    """Build the exact proposal contract handed to downstream Risk."""
    logger.debug("Testing WF-STR-004 intent handoff")
    outcome = build_trade_intent(make_decision(), make_context(), 0)
    assert outcome.data is not None
    assert outcome.data.schema_id == "strategy.trade_intent.v1"
    assert not hasattr(outcome.data, "approved")
