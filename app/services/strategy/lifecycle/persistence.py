"""Production reachability for Strategy lifecycle governance."""

import json
from collections.abc import Mapping
from typing import Any, cast

from app.composition.logging import get_logger
from app.kernel.serialization import to_json_safe
from app.services.strategy.persistence import (
    create_strategy_lifecycle_record,
    read_strategy_lifecycle,
)

logger = get_logger(__name__)


def persist_lifecycle_decision(
    decision: Mapping[str, object],
    *,
    request_id: str,
    correlation_id: str,
) -> dict[str, object]:
    """Append a lifecycle decision record.

    Args:
        decision: Lifecycle mutation evidence mapping.
        request_id: Request trace identifier.
        correlation_id: Correlation trace identifier.

    Returns:
        The persisted lifecycle decision record.

    Raises:
        StrategyOperationError: If Data rejects the transaction.
    """
    material = cast("dict[str, Any]", to_json_safe(dict(decision)))
    create_strategy_lifecycle_record(
        strategy_id=str(material["strategy_id"]),
        strategy_version=str(material["strategy_version"]),
        from_status=str(material["from_status"]),
        to_status=str(material["to_status"]),
        reason=str(material["reason"]),
        decision_json=json.dumps(material, separators=(",", ":")),
        request_id=request_id,
        correlation_id=correlation_id,
    )
    logger.info("Persisted lifecycle decision for %s", material["strategy_id"])
    return {"decision": material}


def list_lifecycle(
    *,
    request_id: str,
    strategy_id: str | None = None,
) -> tuple[Mapping[str, object], ...]:
    """List persisted lifecycle decisions.

    Args:
        request_id: Request trace identifier.
        strategy_id: Optional exact strategy identifier filter.

    Returns:
        Tuple of matching lifecycle decision row mappings.
    """
    return tuple(read_strategy_lifecycle(request_id, strategy_id=strategy_id))


__all__ = ["list_lifecycle", "persist_lifecycle_decision"]
