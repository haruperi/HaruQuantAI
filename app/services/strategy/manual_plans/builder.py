"""Player-authored TradePlan construction."""

# ruff: noqa: DOC201, DOC501

from datetime import datetime
from decimal import Decimal
from typing import Any

from app.services.strategy.intents.trade_plan import build_trade_plan
from app.utils import get_logger

logger = get_logger(__name__)


def build_manual_trade_plan(
    *,
    player_ref: str,
    strategy_id: str,
    strategy_version: str,
    symbol: str,
    direction: str,
    entry_rule: str,
    entry_price: Decimal | None,
    invalidation_rule: str,
    stop_price: Decimal,
    target_price: Decimal,
    exit_plan_ref: str,
    operating_envelope_ref: str,
    requested_size_basis: str,
    planned_rationale: str,
    created_at: datetime,
) -> dict[str, Any]:
    """Build a manual plan through the canonical TradePlan validator."""
    if not player_ref.strip():
        raise ValueError("player_ref must be non-empty")
    logger.info("Building player-authored TradePlan")
    plan = build_trade_plan(
        plan_version=1,
        status="DRAFT",
        strategy_id=strategy_id,
        strategy_version=strategy_version,
        symbol=symbol,
        direction=direction,
        entry_rule=entry_rule,
        entry_price=entry_price,
        invalidation_rule=invalidation_rule,
        stop_price=stop_price,
        target_price=target_price,
        exit_plan_ref=exit_plan_ref,
        operating_envelope_ref=operating_envelope_ref,
        requested_size_basis=requested_size_basis,
        planned_rationale=planned_rationale,
        author_type="PLAYER",
        created_at=created_at,
    )
    plan["author_ref"] = player_ref
    return plan


__all__ = ["build_manual_trade_plan"]
