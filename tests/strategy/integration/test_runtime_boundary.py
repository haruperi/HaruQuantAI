"""WF-STR-007 runtime safety-boundary integration."""

from app.services.strategy import build_trade_intent
from app.utils import logger

from tests.strategy.unit.test_models import make_context, make_decision


def test_runtime_boundary_emits_proposals_only() -> None:
    """Verify Strategy output cannot represent official execution state."""
    logger.debug("Testing WF-STR-007 runtime boundary")
    intent = build_trade_intent(make_decision(), make_context(), 0).data
    assert intent is not None
    assert not (
        {"order_id", "fill_id", "risk_approved"} & set(type(intent).model_fields)
    )
