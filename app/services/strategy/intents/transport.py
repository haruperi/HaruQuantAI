"""TradePlan-to-TradeIntent projection guards."""

# ruff: noqa: DOC201, DOC501

from collections.abc import Mapping

from app.services.strategy.intents.trade_plan import parse_trade_plan
from app.utils import get_logger

logger = get_logger(__name__)


def validate_trade_plan_for_intent(
    plan: Mapping[str, object], *, route: str, environment: str
) -> dict[str, object]:
    """Validate that a operational plan may reach the existing intent builder."""
    parsed = parse_trade_plan(plan)
    if parsed["status"] != "READY_FOR_RISK":
        raise ValueError("only READY_FOR_RISK plans may produce intents")
    if route != "SIM" or environment == "LIVE":
        logger.warning("Rejected non-sim operational TradePlan projection")
        raise ValueError("operational trade plans are simulation-only")
    return parsed


__all__ = ["validate_trade_plan_for_intent"]
