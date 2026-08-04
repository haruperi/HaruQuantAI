"""Decision-time querying and detached source projection."""

from __future__ import annotations

from collections.abc import Mapping

from app.services.data.contracts.errors import DataError
from app.services.data.persistence import read_research_source_records
from app.services.data.research_sources.contracts import (
    JSONScalar,
    ResearchSourceDocument,
    ResearchSourcePage,
    ResearchSourceQuery,
    query_digest,
)
from app.services.data.research_sources.ingestion import (
    _row_to_document,
)
from app.services.data.research_sources.policy import (
    assess_research_source_eligibility,
)


def query_research_sources(query: ResearchSourceQuery) -> ResearchSourcePage:
    """Return eligible records known by the supplied decision time."""
    offset = 0 if query.cursor is None else int(query.cursor)
    result = read_research_source_records(
        query.decision_time.isoformat(),
        query.limit + 1,
        offset,
        request_id=query.request_id,
    )
    eligible: list[ResearchSourceDocument] = []
    for raw in result.rows:
        document = _row_to_document(dict(raw))
        if query.source_kinds and document.source_kind not in query.source_kinds:
            continue
        if query.source_ids and document.source_id not in query.source_ids:
            continue
        if query.asset_scope and not set(query.asset_scope) & set(document.asset_scope):
            continue
        if query.issuer_scope and not set(query.issuer_scope) & set(
            document.issuer_scope
        ):
            continue
        if query.language is not None and document.language != query.language:
            continue
        decision = assess_research_source_eligibility(
            document, decision_time=query.decision_time
        )
        if decision.status == "eligible":
            eligible.append(document)
    records = tuple(eligible[: query.limit])
    next_cursor = str(offset + query.limit) if len(result.rows) > query.limit else None
    return ResearchSourcePage(
        records=records,
        next_cursor=next_cursor,
        decision_time=query.decision_time,
        query_hash=query_digest(query),
    )


def project_research_source_evidence(
    document: object,
) -> Mapping[str, JSONScalar | tuple[str, ...] | Mapping[str, JSONScalar]]:
    """Return a detached bounded projection without unrestricted source content."""
    if not isinstance(document, ResearchSourceDocument):
        raise DataError("INVALID_INPUT", safe_details={"field": "source_document"})
    return {
        "document_id": document.document_id,
        "source_id": document.source_id,
        "source_kind": document.source_kind,
        "document_kind": document.document_kind,
        "external_id": document.external_id,
        "title": document.title[:240],
        "asset_scope": document.asset_scope[:32],
        "issuer_scope": document.issuer_scope[:32],
        "macro_series_scope": document.macro_series_scope[:32],
        "language": document.language,
        "event_at": None
        if document.event_at is None
        else document.event_at.isoformat(),
        "published_at": document.published_at.isoformat(),
        "available_at": document.available_at.isoformat(),
        "revision": document.revision,
        "previous_document_id": document.previous_document_id,
        "original_hash": document.original_hash,
        "normalized_hash": document.normalized_hash,
        "license_id": document.license_id,
        "parser_version": document.parser_version,
        "record_status": document.record_status,
        "trust_status": document.trust_status,
        "manipulation_status": document.manipulation_status,
        "injection_status": document.injection_status,
        "currency": document.currency,
        "unit": document.unit,
        "provenance": dict(document.provenance),
    }


__all__ = ("project_research_source_evidence", "query_research_sources")
