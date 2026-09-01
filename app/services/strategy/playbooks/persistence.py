"""Production reachability for versioned Strategy playbooks."""

import json
from collections.abc import Mapping
from typing import Any, cast

from app.composition.logging import get_logger
from app.kernel.serialization import canonical_digest, to_json_safe
from app.services.strategy.persistence import (
    create_strategy_playbook_record,
    read_strategy_playbooks,
)

logger = get_logger(__name__)


def persist_strategy_playbook(
    playbook: Mapping[str, object],
    *,
    request_id: str,
    correlation_id: str,
) -> dict[str, object]:
    """Persist a StrategyPlaybook v1 and return a record digest.

    Args:
        playbook: Validated StrategyPlaybook v1 mapping.
        request_id: Request trace identifier.
        correlation_id: Correlation trace identifier.

    Returns:
        The persisted playbook record with its canonical digest.

    Raises:
        StrategyOperationError: If Data rejects the transaction.
    """
    material = cast("dict[str, Any]", to_json_safe(dict(playbook)))
    record_hash = canonical_digest(material)
    create_strategy_playbook_record(
        playbook_id=str(material["playbook_id"]),
        playbook_version=1,
        strategy_profile_ref=str(material["strategy_profile_ref"]),
        playbook_json=json.dumps(material, separators=(",", ":")),
        record_hash=record_hash,
        request_id=request_id,
        correlation_id=correlation_id,
    )
    logger.info("Persisted Strategy playbook %s", material["playbook_id"])
    return {"playbook": material, "record_hash": record_hash}


def list_strategy_playbooks(
    *,
    request_id: str,
    playbook_id: str | None = None,
) -> tuple[Mapping[str, object], ...]:
    """List persisted Strategy playbooks.

    Args:
        request_id: Request trace identifier.
        playbook_id: Optional exact playbook identifier filter.

    Returns:
        Tuple of matching playbook row mappings.
    """
    return tuple(read_strategy_playbooks(request_id, playbook_id=playbook_id))


__all__ = ["list_strategy_playbooks", "persist_strategy_playbook"]
