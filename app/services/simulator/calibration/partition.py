"""Deterministic temporal eligibility and pre-fit partitioning."""

# ruff: noqa: DOC201, DOC501

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from typing import Literal

from app.services.simulator.calibration.contracts import (
    _EvidenceRecord,
    _Partition,
    _PartitionBundle,
    partition_hash,
)

_SELECTION_RULE = (
    "sha256_evidence_id_mod_10:v1:0-5=calibration,6-7=validation,8-9=certification"
)
_CALIBRATION_BOUND = 6
_VALIDATION_BOUND = 8


def _record(value: Mapping[str, object]) -> _EvidenceRecord:
    """Parse one exact sanitized evidence mapping."""
    return _EvidenceRecord(
        evidence_id=str(value["evidence_id"]),
        component=str(value["component"]),
        value=Decimal(str(value["value"])),
        unit=str(value["unit"]),
        economic_at=value["economic_at"],  # type: ignore[arg-type]
        available_at=value["available_at"],  # type: ignore[arg-type]
        ingested_at=value["ingested_at"],  # type: ignore[arg-type]
        source_checksum=str(value["source_checksum"]),
        broker=str(value["broker"]),
        server=str(value["server"]),
        account_digest=str(value["account_digest"]),
        environment=str(value["environment"]),  # type: ignore[arg-type]
        symbol=str(value["symbol"]),
        regime=str(value["regime"]),  # type: ignore[arg-type]
    )


def require_temporal_eligibility(
    records: Sequence[_EvidenceRecord],
    *,
    evaluation_start: datetime,
    source_identity: str,
    retrospective: bool,
) -> None:
    """Require prospective point-in-time and single-source eligibility."""
    if evaluation_start.tzinfo is None or evaluation_start.utcoffset() != timedelta(0):
        raise ValueError("evaluation_start must be aware UTC")
    if not retrospective and any(
        record.available_at > evaluation_start for record in records
    ):
        raise ValueError("late availability is ineligible for prospective calibration")
    if any(record.source_checksum != source_identity for record in records):
        raise ValueError("calibration source identity mismatch")


def partition(
    evidence: Sequence[Mapping[str, object]],
    *,
    evaluation_start: datetime,
    source_identity: str,
    retrospective: bool = False,
) -> _PartitionBundle:
    """Create order-independent, immutable, disjoint pre-fit partitions."""
    records = tuple(
        sorted((_record(item) for item in evidence), key=lambda item: item.evidence_id)
    )
    if not records or len({item.evidence_id for item in records}) != len(records):
        raise ValueError("evidence identities must be non-empty and unique")
    require_temporal_eligibility(
        records,
        evaluation_start=evaluation_start,
        source_identity=source_identity,
        retrospective=retrospective,
    )
    groups: dict[str, list[_EvidenceRecord]] = {
        "calibration": [],
        "validation": [],
        "certification": [],
    }
    for record in records:
        remainder = int(sha256(record.evidence_id.encode()).hexdigest(), 16) % 10
        name = (
            "calibration"
            if remainder < _CALIBRATION_BOUND
            else "validation"
            if remainder < _VALIDATION_BOUND
            else "certification"
        )
        groups[name].append(record)
    if any(not group for group in groups.values()):
        raise ValueError("partition policy produced an empty holdout")

    def build(
        name: Literal["calibration", "validation", "certification"],
    ) -> _Partition:
        selected = tuple(groups[name])
        return _Partition(
            name=name, records=selected, checksum=partition_hash(name, selected)
        )

    return _PartitionBundle(
        selection_rule=_SELECTION_RULE,
        retrospective=retrospective,
        calibration=build("calibration"),
        validation=build("validation"),
        certification=build("certification"),
    )


__all__ = []
