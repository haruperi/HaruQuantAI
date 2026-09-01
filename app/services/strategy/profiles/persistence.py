"""Production reachability for versioned Strategy profiles."""

import json
from collections.abc import Mapping
from typing import Any, cast

from app.composition.logging import get_logger
from app.kernel.serialization import canonical_digest, to_json_safe
from app.services.strategy.persistence import (
    create_strategy_profile_record,
    read_strategy_profiles,
)

logger = get_logger(__name__)


def persist_strategy_profile(
    profile: Mapping[str, object],
    *,
    request_id: str,
    correlation_id: str,
) -> dict[str, object]:
    """Persist a StrategyProfile v1 and return a record digest.

    Args:
        profile: Validated StrategyProfile v1 mapping.
        request_id: Request trace identifier.
        correlation_id: Correlation trace identifier.

    Returns:
        The persisted profile record with its canonical digest.

    Raises:
        StrategyOperationError: If Data rejects the transaction.
    """
    material = cast("dict[str, Any]", to_json_safe(dict(profile)))
    record_hash = canonical_digest(material)
    create_strategy_profile_record(
        profile_id=f"{material['strategy_id']}@{material['strategy_version']}",
        strategy_id=str(material["strategy_id"]),
        strategy_version=str(material["strategy_version"]),
        profile_json=json.dumps(material, separators=(",", ":")),
        expectancy_profile_ref=None,
        expectancy_exact_version=None,
        record_hash=record_hash,
        request_id=request_id,
        correlation_id=correlation_id,
    )
    logger.info("Persisted Strategy profile for %s", material["strategy_id"])
    return {"profile": material, "record_hash": record_hash}


def list_strategy_profiles(
    *,
    request_id: str,
    strategy_id: str | None = None,
) -> tuple[Mapping[str, object], ...]:
    """List persisted Strategy profiles.

    Args:
        request_id: Request trace identifier.
        strategy_id: Optional exact strategy identifier filter.

    Returns:
        Tuple of matching profile row mappings.
    """
    return tuple(read_strategy_profiles(request_id, strategy_id=strategy_id))


__all__ = ["list_strategy_profiles", "persist_strategy_profile"]
