"""Player-authored and automated TradePlan construction."""

# ruff: noqa: DOC201, DOC501

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.composition.logging import get_logger
from app.services.strategy.trade_plan.models import build_trade_plan, parse_trade_plan

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


def validate_manual_trade_plan(plan: Mapping[str, object]) -> dict[str, object]:
    """Validate player input through the same canonical TradePlan model."""
    material = dict(plan)
    author_ref = material.pop("author_ref", None)
    parsed = parse_trade_plan(material)
    if (
        parsed["author_type"] != "PLAYER"
        or not isinstance(author_ref, str)
        or not author_ref.strip()
    ):
        raise ValueError("manual plans require bounded player lineage")
    return parsed | {"author_ref": author_ref}


__all__ = ["build_manual_trade_plan", "validate_manual_trade_plan"]
