"""Bounded genuine-source retrieval and transactional ingestion."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

from app.services.data.contracts.errors import DataError
from app.services.data.persistence import (
    create_research_source_record,
    read_latest_research_source_record,
)
from app.services.data.research_sources.contracts import (
    ResearchSourceDocument,
    ResearchSourceIngestRequest,
    ResearchSourcePolicy,
)
from app.services.data.research_sources.policy import validate_research_source_policy
from app.utils import canonical_digest, get_logger, utc_now

logger = get_logger(__name__)
_TAG = re.compile(r"<[^>]+>")
_WHITESPACE = re.compile(r"\s+")


def _normalize(payload: bytes) -> str:
    """Return bounded deterministic plain text from source bytes."""
    decoded = payload.decode("utf-8", errors="replace")
    return _WHITESPACE.sub(" ", unescape(_TAG.sub(" ", decoded))).strip()


def _source_metadata(
    payload: bytes,
    request: ResearchSourceIngestRequest,
) -> tuple[str, str, datetime]:
    """Extract genuine document identity from a supported official feed.

    Args:
        payload: Retrieved source bytes.
        request: Validated acquisition request.

    Returns:
        External identifier, title, and published timestamp.

    Raises:
        DataError: If a declared XML feed has no complete first item.
    """
    if not request.source_url.lower().endswith((".xml", ".rss")):
        return request.external_id, request.title, request.published_at
    # Element expansion and external entity declarations are unnecessary for the
    # supported RSS metadata contract and are rejected before the bounded parse.
    if b"<!DOCTYPE" in payload.upper() or b"<!ENTITY" in payload.upper():
        raise DataError(
            "INVALID_INPUT",
            safe_details={"field": "source_feed_metadata"},
            request_id=request.request_id,
        )
    try:
        root = ET.fromstring(payload)  # noqa: S314 - bounded, declarations rejected.
    except ET.ParseError as error:
        raise DataError(
            "INVALID_INPUT",
            safe_details={"field": "source_feed_metadata"},
            request_id=request.request_id,
        ) from error
    item = root.find("./channel/item")
    if item is None:
        raise DataError(
            "INVALID_INPUT",
            safe_details={"field": "source_feed_metadata"},
            request_id=request.request_id,
        )
    title = (item.findtext("title") or "").strip()
    external_id = (item.findtext("guid") or item.findtext("link") or "").strip()
    published_text = (item.findtext("pubDate") or "").strip()
    try:
        published_at = parsedate_to_datetime(published_text)
    except (TypeError, ValueError) as error:
        raise DataError(
            "INVALID_INPUT",
            safe_details={"field": "source_feed_metadata"},
            request_id=request.request_id,
        ) from error
    if not title or not external_id or published_at.tzinfo is None:
        raise DataError(
            "INVALID_INPUT",
            safe_details={"field": "source_feed_metadata"},
            request_id=request.request_id,
        )
    return external_id, title, published_at


def _fetch(request: ResearchSourceIngestRequest) -> bytes:
    """Retrieve one bounded HTTPS document with no credential material."""
    http_request = Request(  # noqa: S310 - contract accepts HTTPS only.
        request.source_url,
        headers={"User-Agent": "HaruQuantAI/1.0 research-source-reader"},
        method="GET",
    )
    try:
        with urlopen(  # noqa: S310 - request contract permits HTTPS only.
            http_request,
            timeout=request.timeout_seconds,
        ) as response:
            payload = bytes(response.read(request.max_bytes + 1))
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        logger.warning(
            "Research source retrieval failed for source_id=%s",
            request.source_id,
        )
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"source_id": request.source_id},
            request_id=request.request_id,
        ) from exc
    if len(payload) > request.max_bytes:
        raise DataError(
            "LIMIT_EXCEEDED",
            safe_details={"field": "source_payload"},
            request_id=request.request_id,
        )
    return payload


def _row_to_document(row: dict[str, object]) -> ResearchSourceDocument:
    """Rebuild one internal document from a normalized database row."""
    return ResearchSourceDocument(
        document_id=str(row["document_id"]),
        source_id=str(row["source_id"]),
        source_kind=str(row["source_kind"]),  # type: ignore[arg-type]
        document_kind=str(row["document_kind"]),
        external_id=str(row["external_id"]),
        title=str(row["title"]),
        source_url=str(row["source_url"]),
        asset_scope=tuple(json.loads(str(row["asset_scope_json"]))),
        issuer_scope=tuple(json.loads(str(row["issuer_scope_json"]))),
        macro_series_scope=tuple(json.loads(str(row["macro_series_scope_json"]))),
        language=str(row["language"]),
        event_at=(
            None
            if row["event_at"] is None
            else datetime.fromisoformat(str(row["event_at"]))
        ),
        published_at=datetime.fromisoformat(str(row["published_at"])),
        first_seen_at=datetime.fromisoformat(str(row["first_seen_at"])),
        available_at=datetime.fromisoformat(str(row["available_at"])),
        retrieved_at=datetime.fromisoformat(str(row["retrieved_at"])),
        revision=int(str(row["revision"])),
        previous_document_id=(
            None
            if row["previous_document_id"] is None
            else str(row["previous_document_id"])
        ),
        original_hash=str(row["original_hash"]),
        normalized_hash=str(row["normalized_hash"]),
        license_id=str(row["license_id"]),
        parser_version=str(row["parser_version"]),
        record_status=str(row["record_status"]),  # type: ignore[arg-type]
        retention_until=datetime.fromisoformat(str(row["retention_until"])),
        trust_status=str(row["trust_status"]),  # type: ignore[arg-type]
        manipulation_status=str(row["manipulation_status"]),  # type: ignore[arg-type]
        injection_status=str(row["injection_status"]),  # type: ignore[arg-type]
        currency=None if row["currency"] is None else str(row["currency"]),
        unit=None if row["unit"] is None else str(row["unit"]),
        provenance=json.loads(str(row["provenance_json"])),
    )


def ingest_research_source(
    request: ResearchSourceIngestRequest,
    *,
    policy: ResearchSourcePolicy,
    now: datetime | None = None,
) -> ResearchSourceDocument:
    """Retrieve, normalize, and transactionally persist one genuine document.

    Args:
        request: Validated source request.
        policy: Governing source policy.
        now: Testable current UTC instant.

    Returns:
        Persisted immutable source evidence.

    Raises:
        DataError: If retrieval, policy, normalization, or persistence fails.
    """
    observed_at = now or utc_now()
    validate_research_source_policy(request, policy, now=observed_at)
    payload = _fetch(request)
    normalized = _normalize(payload)
    if not normalized:
        raise DataError("EMPTY_RESULT", request_id=request.request_id)
    if request.title.casefold() not in normalized.casefold():
        raise DataError(
            "INVALID_INPUT",
            safe_details={"field": "unverified_source_title"},
            request_id=request.request_id,
        )
    external_id, title, published_at = _source_metadata(payload, request)
    original_hash = hashlib.sha256(payload).hexdigest()
    normalized_hash = hashlib.sha256(normalized.encode()).hexdigest()
    existing = read_latest_research_source_record(
        request.source_id,
        external_id,
        request_id=request.request_id,
    )
    if existing.rows and str(existing.rows[0]["normalized_hash"]) == normalized_hash:
        return _row_to_document(dict(existing.rows[0]))
    revision_value = None if not existing.rows else existing.rows[0]["revision"]
    if revision_value is not None and not isinstance(revision_value, (int, str)):
        raise DataError("PERSISTENCE_FAILED", request_id=request.request_id)
    revision = 1 if revision_value is None else int(revision_value) + 1
    previous = None if not existing.rows else str(existing.rows[0]["document_id"])
    identity = canonical_digest(
        {
            "source": request.source_id,
            "external": external_id,
            "hash": normalized_hash,
        }
    )
    document_id = f"research-source-{identity[:32]}"
    retention_until = observed_at + timedelta(days=policy.retention_days)
    provenance = {
        "policy_id": policy.policy_id,
        "retrieval": "https",
        "source_host": request.source_url.split("/", 3)[2].lower(),
    }
    values = (
        document_id,
        request.source_id,
        request.source_kind,
        external_id,
        title,
        request.source_url,
        json.dumps(request.asset_scope),
        json.dumps(request.issuer_scope),
        request.language,
        None if request.event_at is None else request.event_at.isoformat(),
        published_at.isoformat(),
        observed_at.isoformat(),
        observed_at.isoformat(),
        observed_at.isoformat(),
        revision,
        previous,
        original_hash,
        normalized_hash,
        payload,
        normalized,
        request.license_id,
        retention_until.isoformat(),
        "trusted",
        "clear",
        "clear",
        request.currency,
        request.unit,
        json.dumps(provenance, sort_keys=True),
        "document",
        json.dumps(()),
        "generic-v1",
        "active",
    )
    create_research_source_record(
        values,
        request_id=request.request_id,
    )
    return ResearchSourceDocument(
        document_id=document_id,
        source_id=request.source_id,
        source_kind=request.source_kind,
        document_kind="document",
        external_id=external_id,
        title=title,
        source_url=request.source_url,
        asset_scope=request.asset_scope,
        issuer_scope=request.issuer_scope,
        macro_series_scope=(),
        language=request.language,
        event_at=request.event_at,
        published_at=published_at,
        first_seen_at=observed_at,
        available_at=observed_at,
        retrieved_at=observed_at,
        revision=revision,
        previous_document_id=previous,
        original_hash=original_hash,
        normalized_hash=normalized_hash,
        license_id=request.license_id,
        parser_version="generic-v1",
        record_status="active",
        retention_until=retention_until,
        trust_status="trusted",
        manipulation_status="clear",
        injection_status="clear",
        currency=request.currency,
        unit=request.unit,
        provenance=provenance,
    )


__all__ = ("ingest_research_source",)
