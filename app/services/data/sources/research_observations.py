"""Immutable structured-observation persistence and decision-time reads."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import datetime

from app.kernel.serialization import canonical_digest
from app.services.data.contracts.errors import DataError
from app.services.data.persistence import (
    create_research_observation_record,
    read_latest_research_observation_record,
    read_research_observation_records,
)
from app.services.data.sources.research_contracts import ResearchSourceObservation

_MAX_OBSERVATIONS = 200


def _row(row: Mapping[str, object]) -> ResearchSourceObservation:
    """Build one internal observation from a persisted row.

    Args:
        row: The ``row`` argument.

    Returns:
        The result produced by the operation.
    """
    return ResearchSourceObservation(
        observation_id=str(row["observation_id"]),
        document_id=str(row["document_id"]),
        source_id=str(row["source_id"]),
        series_id=str(row["series_id"]),
        observation_period=str(row["observation_period"]),
        value=json.loads(str(row["value_json"])),
        unit=None if row["unit"] is None else str(row["unit"]),
        published_at=datetime.fromisoformat(str(row["published_at"])),
        available_at=datetime.fromisoformat(str(row["available_at"])),
        retrieved_at=datetime.fromisoformat(str(row["retrieved_at"])),
        revision=int(str(row["revision"])),
        previous_observation_id=(
            None
            if row["previous_observation_id"] is None
            else str(row["previous_observation_id"])
        ),
        content_hash=str(row["content_hash"]),
        parser_version=str(row["parser_version"]),
        trust_status=str(row["trust_status"]),  # type: ignore[arg-type]
        provenance=json.loads(str(row["provenance_json"])),
    )


def persist_research_source_observations(
    document_id: str,
    source_id: str,
    observations: Sequence[Mapping[str, object]],
    *,
    published_at: datetime,
    available_at: datetime,
    retrieved_at: datetime,
    parser_version: str,
    request_id: str,
) -> tuple[ResearchSourceObservation, ...]:
    """Persist normalized observations as immutable revisions.

    Args:
        document_id: Owning source-document identity.
        source_id: Provider identity.
        observations: Bounded normalized observations.
        published_at: Provider publication time.
        available_at: Historical availability time.
        retrieved_at: Retrieval time.
        parser_version: Deterministic parser identity.
        request_id: Correlation identity.

    Returns:
        Persisted observations in input order.

    Raises:
        DataError: If input or persistence is invalid.
    """
    if not observations or len(observations) > _MAX_OBSERVATIONS:
        raise DataError("LIMIT_EXCEEDED", request_id=request_id)
    persisted: list[ResearchSourceObservation] = []
    for raw in observations:
        series_id = str(raw.get("series_id", "")).strip()
        period = str(raw.get("observation_period", "")).strip()
        if not series_id or not period or "value" not in raw:
            raise DataError("INVALID_INPUT", request_id=request_id)
        value_json = json.dumps(raw["value"], sort_keys=True)
        content_hash = canonical_digest(
            {
                "series_id": series_id,
                "observation_period": period,
                "value": raw["value"],
                "unit": raw.get("unit"),
            }
        )
        existing = read_latest_research_observation_record(
            source_id,
            series_id,
            period,
            request_id=request_id,
        )
        if existing.rows and str(existing.rows[0]["content_hash"]) == content_hash:
            persisted.append(_row(existing.rows[0]))
            continue
        revision = (
            1 if not existing.rows else int(str(existing.rows[0]["revision"])) + 1
        )
        previous = (
            None if not existing.rows else str(existing.rows[0]["observation_id"])
        )
        observation_id = (
            f"research-observation-"
            f"{canonical_digest({'document': document_id, 'hash': content_hash})[:32]}"
        )
        provenance = {
            key: value
            for key, value in raw.items()
            if key not in {"series_id", "observation_period", "value", "unit"}
            and isinstance(value, (type(None), bool, int, float, str))
        }
        values = (
            observation_id,
            document_id,
            source_id,
            series_id,
            period,
            value_json,
            None if raw.get("unit") is None else str(raw["unit"]),
            published_at.isoformat(),
            available_at.isoformat(),
            retrieved_at.isoformat(),
            revision,
            previous,
            content_hash,
            parser_version,
            "trusted",
            json.dumps(provenance, sort_keys=True),
        )
        create_research_observation_record(
            values,
            request_id=request_id,
        )
        persisted.append(
            ResearchSourceObservation(
                observation_id=observation_id,
                document_id=document_id,
                source_id=source_id,
                series_id=series_id,
                observation_period=period,
                value=raw["value"],  # type: ignore[arg-type]
                unit=None if raw.get("unit") is None else str(raw["unit"]),
                published_at=published_at,
                available_at=available_at,
                retrieved_at=retrieved_at,
                revision=revision,
                previous_observation_id=previous,
                content_hash=content_hash,
                parser_version=parser_version,
                trust_status="trusted",
                provenance=provenance,
            )
        )
    return tuple(persisted)


def query_research_source_observations(
    decision_time: datetime,
    *,
    source_id: str | None = None,
    series_id: str | None = None,
    limit: int = 200,
    request_id: str,
) -> tuple[ResearchSourceObservation, ...]:
    """Read bounded observations available by a historical decision time.

    Args:
        decision_time: The ``decision_time`` argument.
        source_id: The ``source_id`` argument.
        series_id: The ``series_id`` argument.
        limit: The ``limit`` argument.
        request_id: The ``request_id`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the operation cannot be completed safely.
    """
    if not 0 < limit <= _MAX_OBSERVATIONS:
        raise DataError("LIMIT_EXCEEDED", request_id=request_id)
    result = read_research_observation_records(
        decision_time.isoformat(),
        source_id,
        series_id,
        limit,
        request_id=request_id,
    )
    return tuple(_row(row) for row in result.rows)


def project_research_source_observation(
    observation: object,
) -> Mapping[str, object]:
    """Return bounded detached structured observation evidence.

    Args:
        observation: The ``observation`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the operation cannot be completed safely.
    """
    if not isinstance(observation, ResearchSourceObservation):
        raise DataError("INVALID_INPUT", safe_details={"field": "observation"})
    return {
        "observation_id": observation.observation_id,
        "document_id": observation.document_id,
        "source_id": observation.source_id,
        "series_id": observation.series_id,
        "observation_period": observation.observation_period,
        "value": observation.value,
        "unit": observation.unit,
        "published_at": observation.published_at.isoformat(),
        "available_at": observation.available_at.isoformat(),
        "revision": observation.revision,
        "previous_observation_id": observation.previous_observation_id,
        "content_hash": observation.content_hash,
        "parser_version": observation.parser_version,
        "trust_status": observation.trust_status,
        "provenance": dict(observation.provenance),
    }


__all__ = (
    "persist_research_source_observations",
    "project_research_source_observation",
    "query_research_source_observations",
)
