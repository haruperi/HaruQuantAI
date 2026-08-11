"""Production reachability for Strategy setup evaluations."""

import json
from collections.abc import Mapping
from typing import Any, cast

from app.services.strategy.persistence import (
    create_strategy_setup_evaluation_record,
    read_strategy_setup_evaluations,
)
from app.utils import canonical_digest, get_logger, to_json_safe

logger = get_logger(__name__)


def persist_setup_evaluation(
    evaluation: Mapping[str, object],
    *,
    request_id: str,
    correlation_id: str,
) -> dict[str, object]:
    """Append a SetupEvaluation v1 evidence record.

    Args:
        evaluation: Validated SetupEvaluation v1 mapping.
        request_id: Request trace identifier.
        correlation_id: Correlation trace identifier.

    Returns:
        The persisted evaluation record with its canonical digest.

    Raises:
        StrategyOperationError: If Data rejects the transaction.
    """
    material = cast("dict[str, Any]", to_json_safe(dict(evaluation)))
    record_hash = canonical_digest(material)
    create_strategy_setup_evaluation_record(
        evaluation_id=str(material["evaluation_id"]),
        playbook_ref=str(material["playbook_ref"]),
        outcome=str(material["outcome"]),
        source_snapshot_json=json.dumps(
            material["source_snapshot_refs"], separators=(",", ":")
        ),
        reason_code_json=json.dumps(material["reason_codes"], separators=(",", ":")),
        record_hash=record_hash,
        request_id=request_id,
        correlation_id=correlation_id,
    )
    logger.info("Persisted setup evaluation %s", material["evaluation_id"])
    return {"evaluation": material, "record_hash": record_hash}


def list_setup_evaluations(
    *,
    request_id: str,
    playbook_ref: str | None = None,
) -> tuple[Mapping[str, object], ...]:
    """List persisted setup evaluations.

    Args:
        request_id: Request trace identifier.
        playbook_ref: Optional playbook reference filter.

    Returns:
        Tuple of matching evaluation row mappings.
    """
    return tuple(read_strategy_setup_evaluations(request_id, playbook_ref=playbook_ref))


__all__ = ["list_setup_evaluations", "persist_setup_evaluation"]
