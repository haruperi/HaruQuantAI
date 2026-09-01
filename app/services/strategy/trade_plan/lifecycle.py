"""Deterministic TradePlan lifecycle transitions and amendments."""

# ruff: noqa: DOC201, DOC501

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.composition.logging import get_logger
from app.services.strategy.trade_plan.models import build_trade_plan, parse_trade_plan

logger = get_logger(__name__)

_TRANSITIONS = {
    "DRAFT": {"READY_FOR_RISK", "ABORTED"},
    "READY_FOR_RISK": {"APPROVED", "REJECTED", "ABORTED"},
    "APPROVED": {"RELEASED", "ABORTED"},
    "REJECTED": set(),
    "RELEASED": {"MANAGED", "CLOSED", "ABORTED"},
    "MANAGED": {"CLOSED", "ABORTED"},
    "CLOSED": set(),
    "ABORTED": set(),
}


def transition_trade_plan(
    plan: Mapping[str, object], *, target_status: str
) -> dict[str, Any]:
    """Create an immutable lifecycle projection after an allowed transition."""
    parsed = parse_trade_plan(plan)
    source = str(parsed["status"])
    if target_status not in _TRANSITIONS.get(source, set()):
        logger.warning("Rejected TradePlan transition %s -> %s", source, target_status)
        raise ValueError("trade plan transition is not allowed")
    result = dict(parsed)
    result["status"] = target_status
    return parse_trade_plan(result)


def amend_trade_plan(
    plan: Mapping[str, object],
    *,
    created_at: datetime,
    entry_rule: str | None = None,
    entry_price: Decimal | None = None,
    invalidation_rule: str | None = None,
    stop_price: Decimal | None = None,
    target_price: Decimal | None = None,
    planned_rationale: str | None = None,
) -> dict[str, Any]:
    """Create a new version rather than mutate a released plan."""
    parsed = parse_trade_plan(plan)
    if parsed["status"] not in {"RELEASED", "MANAGED"}:
        raise ValueError("only released or managed plans may be amended")
    return build_trade_plan(
        plan_version=int(parsed["plan_version"]) + 1,
        status="READY_FOR_RISK",
        strategy_id=str(parsed["strategy_id"]),
        strategy_version=str(parsed["strategy_version"]),
        symbol=str(parsed["symbol"]),
        direction=str(parsed["direction"]),
        entry_rule=entry_rule or str(parsed["entry_rule"]),
        entry_price=entry_price
        if entry_price is not None
        else Decimal(str(parsed["entry_price"]))
        if parsed["entry_price"] is not None
        else None,
        invalidation_rule=invalidation_rule or str(parsed["invalidation_rule"]),
        stop_price=stop_price or Decimal(str(parsed["stop_price"])),
        target_price=target_price or Decimal(str(parsed["target_price"])),
        exit_plan_ref=str(parsed["exit_plan_ref"]),
        operating_envelope_ref=str(parsed["operating_envelope_ref"]),
        requested_size_basis=str(parsed["requested_size_basis"]),
        planned_rationale=planned_rationale or str(parsed["planned_rationale"]),
        author_type=str(parsed["author_type"]),
        created_at=created_at,
        parent_plan_id=str(parsed["plan_id"]),
    )


__all__ = ["amend_trade_plan", "transition_trade_plan"]
