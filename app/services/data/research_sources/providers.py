"""Transactional persistence for normalized provider batches."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from app.services.data.contracts.errors import DataError
from app.services.data.persistence.contracts import StatementPlan, TransactionRequest
from app.services.data.persistence.transactions import _execute_transaction_raw
from app.services.data.research_sources.ingestion import (
    _SELECT_COLUMNS,
    _row_to_document,
)
from app.services.data.research_sources.observations import (
    persist_research_source_observations,
)
from app.utils import canonical_digest

if TYPE_CHECKING:
    from app.services.data.research_sources.contracts import (
        ResearchSourceDocument,
        ResearchSourcePolicy,
        SourceKind,
    )

_MAX_PROVIDER_RECORDS = 200


def persist_research_provider_records(
    records: Sequence[Mapping[str, object]],
    payload: bytes,
    *,
    source_id: str,
    source_kind: SourceKind,
    asset_scope: tuple[str, ...],
    issuer_scope: tuple[str, ...],
    macro_series_scope: tuple[str, ...],
    language: str,
    license_id: str,
    environment: str,
    decision_use: str,
    policy: ResearchSourcePolicy,
    retrieved_at: datetime,
    request_id: str,
) -> tuple[ResearchSourceDocument, ...]:
    """Persist a normalized provider batch and its structured observations.

    Args:
        records: Provider-normalized records.
        payload: Exact bounded provider response.
        source_id: Stable provider identity.
        source_kind: Governed research-source category.
        asset_scope: Applicable asset identities.
        issuer_scope: Applicable issuer identities.
        macro_series_scope: Applicable macro-series identities.
        language: BCP-47-like source language label.
        license_id: Governed source-use policy label.
        environment: Active non-production environment.
        decision_use: Approved source use.
        policy: Governing source policy.
        retrieved_at: UTC retrieval instant.
        request_id: Correlation identity.

    Returns:
        Persisted immutable source documents.

    Raises:
        DataError: If policy, records, timestamps, or persistence are invalid.
    """
    if (
        not records
        or len(records) > _MAX_PROVIDER_RECORDS
        or source_id != policy.source_id
        or environment not in policy.permitted_environments
        or decision_use not in policy.permitted_uses
    ):
        raise DataError("LICENSE_RESTRICTION", request_id=request_id)
    payload_hash = hashlib.sha256(payload).hexdigest()
    documents: list[ResearchSourceDocument] = []
    for record in records:
        document = _persist_record(
            record,
            payload,
            payload_hash=payload_hash,
            source_id=source_id,
            source_kind=source_kind,
            asset_scope=asset_scope,
            issuer_scope=issuer_scope,
            macro_series_scope=macro_series_scope,
            language=language,
            license_id=license_id,
            retention_days=policy.retention_days,
            retrieved_at=retrieved_at,
            request_id=request_id,
        )
        observations = record.get("observations", ())
        if isinstance(observations, Sequence) and observations:
            persist_research_source_observations(
                document.document_id,
                source_id,
                observations,
                published_at=document.published_at,
                available_at=document.available_at,
                retrieved_at=retrieved_at,
                parser_version=document.parser_version,
                request_id=request_id,
            )
        documents.append(document)
    return tuple(documents)


def _persist_record(
    record: Mapping[str, object],
    payload: bytes,
    *,
    payload_hash: str,
    source_id: str,
    source_kind: SourceKind,
    asset_scope: tuple[str, ...],
    issuer_scope: tuple[str, ...],
    macro_series_scope: tuple[str, ...],
    language: str,
    license_id: str,
    retention_days: int,
    retrieved_at: datetime,
    request_id: str,
) -> ResearchSourceDocument:
    """Persist one normalized provider record."""
    required = (
        "external_id",
        "document_kind",
        "title",
        "published_at",
        "available_at",
        "canonical_locator",
        "parser_version",
    )
    if any(not str(record.get(field, "")).strip() for field in required):
        raise DataError("INVALID_INPUT", request_id=request_id)
    published_at = datetime.fromisoformat(str(record["published_at"]))
    available_at = datetime.fromisoformat(str(record["available_at"]))
    if available_at > retrieved_at:
        raise DataError("INVALID_INPUT", request_id=request_id)
    external_id = str(record["external_id"])
    normalized_hash = canonical_digest(
        {
            "external_id": external_id,
            "title": record["title"],
            "published_at": published_at,
            "observations": record.get("observations", ()),
        }
    )
    existing = _execute_transaction_raw(
        TransactionRequest(
            plan=StatementPlan(
                statements=(
                    f"""
                    SELECT {_SELECT_COLUMNS} FROM data_research_sources
                    WHERE source_id = ? AND external_id = ?
                    ORDER BY revision DESC LIMIT 1
                    """.strip(),  # noqa: S608
                ),
                parameter_sets=((source_id, external_id),),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )
    if existing.rows and str(existing.rows[0]["normalized_hash"]) == normalized_hash:
        return _row_to_document(dict(existing.rows[0]))
    revision = 1 if not existing.rows else int(str(existing.rows[0]["revision"])) + 1
    previous = None if not existing.rows else str(existing.rows[0]["document_id"])
    identity = canonical_digest(
        {
            "source": source_id,
            "external": external_id,
            "hash": normalized_hash,
        }
    )
    document_id = f"research-source-{identity[:32]}"
    provenance = {
        "retrieval": "https",
        "provider": source_id,
        "parser_version": str(record["parser_version"]),
    }
    values = (
        document_id,
        source_id,
        source_kind,
        external_id,
        str(record["title"]),
        str(record["canonical_locator"]),
        json.dumps(asset_scope),
        json.dumps(issuer_scope),
        language,
        None,
        published_at.isoformat(),
        retrieved_at.isoformat(),
        available_at.isoformat(),
        retrieved_at.isoformat(),
        revision,
        previous,
        payload_hash,
        normalized_hash,
        payload,
        str(record["title"]),
        license_id,
        (retrieved_at + timedelta(days=retention_days)).isoformat(),
        "trusted",
        "clear",
        "clear",
        None,
        None,
        json.dumps(provenance, sort_keys=True),
        str(record["document_kind"]),
        json.dumps(macro_series_scope),
        str(record["parser_version"]),
        "active",
    )
    _execute_transaction_raw(
        TransactionRequest(
            plan=StatementPlan(
                statements=(
                    """
                    INSERT INTO data_research_sources (
                        document_id, source_id, source_kind, external_id, title,
                        source_url, asset_scope_json, issuer_scope_json, language,
                        event_at, published_at, first_seen_at, available_at,
                        retrieved_at, revision, previous_document_id, original_hash,
                        normalized_hash, original_content, normalized_text, license_id,
                        retention_until, trust_status, manipulation_status,
                        injection_status, currency, unit, provenance_json,
                        document_kind, macro_series_scope_json, parser_version,
                        record_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                              ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """.strip(),
                ),
                parameter_sets=(values,),
                max_rows=1,
            ),
            request_id=request_id,
        )
    )
    return _row_to_document(
        {
            "document_id": document_id,
            "source_id": source_id,
            "source_kind": source_kind,
            "document_kind": str(record["document_kind"]),
            "external_id": external_id,
            "title": str(record["title"]),
            "source_url": str(record["canonical_locator"]),
            "asset_scope_json": json.dumps(asset_scope),
            "issuer_scope_json": json.dumps(issuer_scope),
            "macro_series_scope_json": json.dumps(macro_series_scope),
            "language": language,
            "event_at": None,
            "published_at": published_at.isoformat(),
            "first_seen_at": retrieved_at.isoformat(),
            "available_at": available_at.isoformat(),
            "retrieved_at": retrieved_at.isoformat(),
            "revision": revision,
            "previous_document_id": previous,
            "original_hash": payload_hash,
            "normalized_hash": normalized_hash,
            "license_id": license_id,
            "retention_until": (
                retrieved_at + timedelta(days=retention_days)
            ).isoformat(),
            "trust_status": "trusted",
            "manipulation_status": "clear",
            "injection_status": "clear",
            "currency": None,
            "unit": None,
            "parser_version": str(record["parser_version"]),
            "record_status": "active",
            "provenance_json": json.dumps(provenance, sort_keys=True),
        }
    )


__all__ = ("persist_research_provider_records",)
