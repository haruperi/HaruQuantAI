"""Production reachability for Strategy trade plans."""

import json
from collections.abc import Mapping
from typing import Any, cast

from app.composition.logging import get_logger
from app.kernel.serialization import canonical_digest, to_json_safe
from app.services.strategy.persistence import (
    create_strategy_plan_record,
    read_strategy_plans,
)

logger = get_logger(__name__)


def persist_trade_plan(
    plan: Mapping[str, object],
    *,
    request_id: str,
    correlation_id: str,
) -> dict[str, object]:
    """Persist a TradePlan v1 and return a record digest.

    Args:
        plan: Validated TradePlan v1 mapping.
        request_id: Request trace identifier.
        correlation_id: Correlation trace identifier.

    Returns:
        The persisted plan record with its canonical digest.

    Raises:
        StrategyOperationError: If Data rejects the transaction.
    """
    material = cast("dict[str, Any]", to_json_safe(dict(plan)))
    record_hash = canonical_digest(material)
    create_strategy_plan_record(
        plan_id=str(material["plan_id"]),
        plan_version=int(material["plan_version"]),
        status=str(material["status"]),
        strategy_id=str(material["strategy_id"]),
        strategy_version=str(material["strategy_version"]),
        plan_json=json.dumps(material, separators=(",", ":")),
        parent_plan_id=material.get("parent_plan_id"),
        record_hash=record_hash,
        request_id=request_id,
        correlation_id=correlation_id,
    )
    logger.info(
        "Persisted TradePlan %s v%s", material["plan_id"], material["plan_version"]
    )
    return {"plan": material, "record_hash": record_hash}


def list_trade_plans(
    *,
    request_id: str,
    plan_id: str | None = None,
) -> tuple[Mapping[str, object], ...]:
    """List persisted TradePlans.

    Args:
        request_id: Request trace identifier.
        plan_id: Optional exact plan identifier filter.

    Returns:
        Tuple of matching plan row mappings.
    """
    return tuple(read_strategy_plans(request_id, plan_id=plan_id))


__all__ = ["list_trade_plans", "persist_trade_plan"]
