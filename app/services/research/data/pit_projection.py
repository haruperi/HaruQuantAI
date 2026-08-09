"""Point-in-time evidence projection gate (TC-IMP-RES-09, EXTEND FEAT-RES-02/04).

Exposes only the evidence available at the supplied simulation timestamp,
refusing any record whose availability instant is after the decision time.
This is the leakage-safe projection gate that complements the existing
``leakage/`` no-lookahead validation: leakage/ validates feature columns, this
module validates temporal availability of source evidence.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from app.services.research.contracts.errors import ValidationError
from app.utils import get_logger

logger = get_logger(__name__)


def project_point_in_time_evidence(
    records: tuple[Mapping[str, object], ...],
    *,
    decision_time_utc: datetime,
    available_at_field: str = "available_at",
) -> tuple[Mapping[str, object], ...]:
    """Project only evidence available at the simulation timestamp.

    Args:
        records: Candidate evidence records with an availability field.
        decision_time_utc: Simulation/decision timestamp (point-in-time cutoff).
        available_at_field: Field name carrying each record's availability instant.

    Returns:
        Eligible records whose availability is at or before the decision time.

    Raises:
        ValidationError: If the decision time is naive or a record is malformed.
    """
    if decision_time_utc.tzinfo is None:
        raise ValidationError("RES_INPUT_INVALID", "PIT_DECISION_TIME_NAIVE")
    logger.info(
        "Projecting point-in-time evidence at %s", decision_time_utc.isoformat()
    )
    eligible: list[Mapping[str, object]] = []
    for record in records:
        if not isinstance(record, Mapping):
            raise ValidationError("RES_INPUT_INVALID", "PIT_RECORD_NOT_MAPPING")
        raw = record.get(available_at_field)
        if raw is None:
            # A record with no availability instant cannot be proven available;
            # fail closed by excluding it rather than guessing.
            continue
        if isinstance(raw, datetime):
            available = raw
        else:
            try:
                available = datetime.fromisoformat(str(raw))
            except ValueError as error:
                raise ValidationError(
                    "RES_INPUT_INVALID", "PIT_AVAILABLE_AT_INVALID"
                ) from error
        if available.tzinfo is None:
            # Naive availability cannot be ordered against a timezone-aware
            # decision time; exclude it fail-closed.
            continue
        if available <= decision_time_utc:
            eligible.append(record)
    return tuple(eligible)


__all__ = ("project_point_in_time_evidence",)
