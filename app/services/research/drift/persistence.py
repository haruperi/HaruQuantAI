"""Immutable persistence for performance-drift evidence."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from app.services.research.drift.contracts import parse_performance_drift_evidence
from app.services.research.persistence import (
    create_governed_evidence,
    read_latest_governed_evidence,
)
from app.utils import canonical_json, get_logger

logger = get_logger(__name__)


def persist_performance_drift_evidence(
    evidence: Mapping[str, object], *, request_id: str
) -> Mapping[str, object]:
    """Append validated drift evidence.

    Args:
        evidence: Candidate drift evidence.
        request_id: Request trace identifier.

    Returns:
        Persistence acknowledgement.
    """
    parsed = parse_performance_drift_evidence(evidence)
    logger.info("Persisting performance drift evidence for %s", parsed["profile_id"])
    return create_governed_evidence(
        table="research_performance_drift_evidence",
        identity_column="profile_id",
        identity=str(parsed["profile_id"]),
        evidence_json=canonical_json(parsed),
        canonical_hash=str(parsed["canonical_hash"]),
        request_id=request_id,
    )


def load_latest_performance_drift_evidence(
    *, profile_id: str, request_id: str
) -> dict[str, Any] | None:
    """Load the latest validated drift evidence for a profile.

    Args:
        profile_id: Expectancy profile identity.
        request_id: Request trace identifier.

    Returns:
        Validated evidence, or ``None``.
    """
    row = read_latest_governed_evidence(
        table="research_performance_drift_evidence",
        identity_column="profile_id",
        identity=profile_id,
        request_id=request_id,
    )
    if row is None:
        return None
    return parse_performance_drift_evidence(json.loads(str(row["evidence_json"])))


__all__ = (
    "load_latest_performance_drift_evidence",
    "persist_performance_drift_evidence",
)
