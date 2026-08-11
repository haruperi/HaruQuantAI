"""Production reachability for Strategy automation policy."""

import json
from collections.abc import Mapping
from typing import Any, cast

from app.services.strategy.persistence import (
    create_strategy_automation_policy_record,
    read_strategy_automation_policies,
)
from app.utils import canonical_digest, get_logger, to_json_safe

logger = get_logger(__name__)


def persist_automation_policy(
    *,
    strategy_id: str,
    strategy_version: str,
    mode: str,
    request_id: str,
    correlation_id: str,
) -> dict[str, object]:
    """Persist a versioned automation policy record.

    Args:
        strategy_id: Owning strategy identifier.
        strategy_version: Exact strategy version.
        mode: Effective automation mode.
        request_id: Request trace identifier.
        correlation_id: Correlation trace identifier.

    Returns:
        The persisted policy record with its canonical digest.

    Raises:
        StrategyOperationError: If Data rejects the transaction.
    """
    material = cast(
        "dict[str, Any]",
        to_json_safe(
            {
                "strategy_id": strategy_id,
                "strategy_version": strategy_version,
                "mode": mode,
            }
        ),
    )
    record_hash = canonical_digest(material)
    create_strategy_automation_policy_record(
        policy_id=f"{strategy_id}@{strategy_version}",
        strategy_id=strategy_id,
        strategy_version=strategy_version,
        policy_version=1,
        mode=mode,
        policy_json=json.dumps(material, separators=(",", ":")),
        record_hash=record_hash,
        request_id=request_id,
        correlation_id=correlation_id,
    )
    logger.info("Persisted automation policy for %s", strategy_id)
    return {"policy": material, "record_hash": record_hash}


def list_automation_policies(
    *,
    request_id: str,
    strategy_id: str | None = None,
) -> tuple[Mapping[str, object], ...]:
    """List persisted automation policies.

    Args:
        request_id: Request trace identifier.
        strategy_id: Optional exact strategy identifier filter.

    Returns:
        Tuple of matching policy row mappings.
    """
    return tuple(read_strategy_automation_policies(request_id, strategy_id=strategy_id))


__all__ = ["list_automation_policies", "persist_automation_policy"]
