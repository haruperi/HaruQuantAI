"""Immutable persistence for stress-scenario evidence."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from app.composition.logging import get_logger
from app.kernel.serialization import canonical_json
from app.services.research.persistence import (
    create_governed_evidence,
    read_latest_governed_evidence,
)
from app.services.research.stress_evidence.contracts import (
    parse_stress_scenario_evidence,
)

logger = get_logger(__name__)


def persist_stress_scenario_evidence(
    evidence: Mapping[str, object], *, request_id: str
) -> Mapping[str, object]:
    """Append validated stress evidence.

    Args:
        evidence: Candidate stress evidence.
        request_id: Request trace identifier.

    Returns:
        Persistence acknowledgement.
    """
    parsed = parse_stress_scenario_evidence(evidence)
    logger.info("Persisting stress evidence %s", parsed["scenario_id"])
    return create_governed_evidence(
        table="research_stress_scenario_evidence",
        identity_column="scenario_id",
        identity=str(parsed["scenario_id"]),
        evidence_json=canonical_json(parsed),
        canonical_hash=str(parsed["canonical_hash"]),
        request_id=request_id,
    )


def load_latest_stress_scenario_evidence(
    *, scenario_id: str, request_id: str
) -> dict[str, Any] | None:
    """Load the latest validated stress evidence for a scenario.

    Args:
        scenario_id: Stress scenario identity.
        request_id: Request trace identifier.

    Returns:
        Validated evidence, or ``None``.
    """
    row = read_latest_governed_evidence(
        table="research_stress_scenario_evidence",
        identity_column="scenario_id",
        identity=scenario_id,
        request_id=request_id,
    )
    if row is None:
        return None
    return parse_stress_scenario_evidence(json.loads(str(row["evidence_json"])))


__all__ = (
    "load_latest_stress_scenario_evidence",
    "persist_stress_scenario_evidence",
)
