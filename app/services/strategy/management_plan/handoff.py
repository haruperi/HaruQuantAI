"""Immutable exit and management plan automation handoff."""

# ruff: noqa: DOC201

from collections.abc import Mapping

from app.composition.logging import get_logger
from app.services.strategy.management_plan.models import parse_exit_plan

logger = get_logger(__name__)


def build_exit_plan_handoff(
    exit_plan: Mapping[str, object],
    *,
    risk_interlock: bool,
    trading_interlock: bool,
    route: str,
    environment: str,
) -> dict[str, object]:
    """Build a non-executable handoff only when external interlocks permit it."""
    parsed = parse_exit_plan(exit_plan)
    permitted = (
        risk_interlock
        and trading_interlock
        and route == "SIM"
        and environment != "LIVE"
    )
    if not permitted:
        logger.warning("Exit-plan automation handoff restricted by external interlock")
    return {
        "contract_version": "v1",
        "schema_id": "strategy.exit_plan_handoff.v1",
        "exit_plan_id": parsed["exit_plan_id"],
        "status": "READY" if permitted else "RESTRICTED",
        "execution_authority": False,
    }


__all__ = ["build_exit_plan_handoff"]
