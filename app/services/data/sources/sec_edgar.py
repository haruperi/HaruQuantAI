"""SEC EDGAR submissions, Companyfacts, and filing-index normalization."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime

from app.services.data.contracts.errors import DataError

_FORMS = {"10-K", "10-K/A", "10-Q", "10-Q/A", "8-K", "8-K/A", "20-F", "6-K"}
_MAX_OBSERVATIONS = 200
_DOCUMENT_SUFFIXES = (".htm", ".html", ".txt")
_TRANSCRIPT_MARKERS = ("transcript", "preparedremarks", "prepared-remarks")
_EXHIBIT_MARKERS = ("ex99", "ex-99", "exhibit99", "exhibit-99")


def _instant(value: str, fallback: datetime) -> datetime:
    """Parse an SEC acceptance instant or conservatively use observation time.

    Args:
        value: The ``value`` argument.
        fallback: The ``fallback`` argument.

    Returns:
        The result produced by the operation.
    """
    if not value:
        return fallback
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return fallback
    return (
        parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)
    )


def _submissions(
    data: Mapping[str, object], observed_at: datetime
) -> list[dict[str, object]]:
    """Normalize recent filing columns from the SEC submissions response.

    Args:
        data: The ``data`` argument.
        observed_at: The ``observed_at`` argument.

    Returns:
        The result produced by the operation.
    """
    filings = data.get("filings")
    if not isinstance(filings, Mapping):
        return []
    recent = filings.get("recent")
    if not isinstance(recent, Mapping):
        return []
    accessions = recent.get("accessionNumber")
    forms = recent.get("form")
    documents = recent.get("primaryDocument")
    accepted = recent.get("acceptanceDateTime")
    if (
        not isinstance(accessions, list)
        or not isinstance(forms, list)
        or not isinstance(documents, list)
    ):
        return []
    records: list[dict[str, object]] = []
    for index, accession in enumerate(accessions):
        form = str(forms[index]) if index < len(forms) else ""
        if form not in _FORMS:
            continue
        publication = (
            str(accepted[index])
            if isinstance(accepted, list) and index < len(accepted)
            else ""
        )
        primary = str(documents[index]) if index < len(documents) else ""
        records.append(
            {
                "external_id": str(accession),
                "document_kind": "regulatory_filing",
                "title": f"{form} {accession}",
                "published_at": _instant(publication, observed_at).isoformat(),
                "available_at": _instant(publication, observed_at).isoformat(),
                "canonical_locator": primary,
                "parser_version": "sec-edgar-submissions-v1",
                "observations": (),
            }
        )
    return records


def _companyfacts(
    data: Mapping[str, object], observed_at: datetime
) -> list[dict[str, object]]:
    """Normalize bounded SEC Companyfacts observations.

    Args:
        data: The ``data`` argument.
        observed_at: The ``observed_at`` argument.

    Returns:
        The result produced by the operation.
    """
    facts = data.get("facts")
    if not isinstance(facts, Mapping):
        return []
    observations = _fact_observations(facts)
    if not observations:
        return []
    entity = str(data.get("entityName", "SEC issuer"))
    cik = str(data.get("cik", "unknown"))
    return [
        {
            "external_id": f"companyfacts-{cik}",
            "document_kind": "fundamental_facts",
            "title": f"{entity} SEC Companyfacts",
            "published_at": observed_at.isoformat(),
            "available_at": observed_at.isoformat(),
            "canonical_locator": (
                f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik.zfill(10)}.json"
            ),
            "parser_version": "sec-edgar-companyfacts-v1",
            "observations": tuple(observations),
        }
    ]


def _fact_observations(
    facts: Mapping[str, object],
) -> list[dict[str, object]]:
    """Flatten a bounded set of SEC taxonomy facts.

    Args:
        facts: The ``facts`` argument.

    Returns:
        The result produced by the operation.
    """
    observations: list[dict[str, object]] = []
    for taxonomy, concepts in facts.items():
        if not isinstance(concepts, Mapping):
            continue
        for concept, definition in concepts.items():
            if not isinstance(definition, Mapping):
                continue
            units = definition.get("units")
            if not isinstance(units, Mapping):
                continue
            for unit, entries in units.items():
                bounded_entries = entries[-5:] if isinstance(entries, list) else ()
                for entry in bounded_entries:
                    if not isinstance(entry, Mapping) or "val" not in entry:
                        continue
                    observations.append(
                        {
                            "series_id": f"{taxonomy}:{concept}",
                            "observation_period": str(entry.get("end", "")),
                            "value": entry["val"],
                            "unit": str(unit),
                            "accession": str(entry.get("accn", "")),
                            "form": str(entry.get("form", "")),
                        }
                    )
                    if len(observations) >= _MAX_OBSERVATIONS:
                        return observations
    return observations


def parse_payload(
    payload: bytes,
    observed_at: datetime,
) -> tuple[dict[str, object], ...]:
    """Parse one bounded SEC JSON response.

    Args:
        payload: The ``payload`` argument.
        observed_at: The ``observed_at`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the operation cannot be completed safely.
    """
    try:
        data = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DataError(
            "INVALID_INPUT", safe_details={"field": "sec_payload"}
        ) from error
    if not isinstance(data, Mapping):
        raise DataError("INVALID_INPUT", safe_details={"field": "sec_payload"})
    records = _submissions(data, observed_at) or _companyfacts(data, observed_at)
    return tuple(records)


def parse_filing_index_payload(
    payload: bytes,
    observed_at: datetime,
) -> tuple[dict[str, object], ...]:
    """Parse one SEC Archives filing-directory index response.

    Args:
        payload: Raw SEC Archives ``index.json`` bytes.
        observed_at: UTC instant when the response was observed.

    Returns:
        Bounded filing-document and EX-99 exhibit metadata.

    Raises:
        DataError: If the response is not a valid SEC directory index.
    """
    try:
        data = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DataError(
            "INVALID_INPUT", safe_details={"field": "sec_filing_index"}
        ) from error
    directory = data.get("directory") if isinstance(data, Mapping) else None
    items = directory.get("item") if isinstance(directory, Mapping) else None
    path = str(directory.get("name", "")).strip("/") if directory else ""
    if not path or not isinstance(items, list):
        raise DataError("INVALID_INPUT", safe_details={"field": "sec_filing_index"})

    records: list[dict[str, object]] = []
    for item in items:
        if not isinstance(item, Mapping):
            continue
        filename = str(item.get("name", "")).strip()
        lowered = filename.lower()
        if not filename or not lowered.endswith(_DOCUMENT_SUFFIXES):
            continue
        is_exhibit = any(marker in lowered for marker in _EXHIBIT_MARKERS)
        is_transcript = any(marker in lowered for marker in _TRANSCRIPT_MARKERS)
        document_kind = (
            "transcript"
            if is_transcript
            else "official_statement_exhibit"
            if is_exhibit
            else "filing_document"
        )
        modified = _instant(str(item.get("last-modified", "")), observed_at)
        locator = f"https://www.sec.gov/{path}/{filename}"
        records.append(
            {
                "external_id": f"{path}:{filename}",
                "document_kind": document_kind,
                "title": filename,
                "published_at": modified.isoformat(),
                "available_at": modified.isoformat(),
                "canonical_locator": locator,
                "parser_version": "sec-edgar-filing-index-v1",
                "observations": (),
            }
        )
        if len(records) >= _MAX_OBSERVATIONS:
            break
    return tuple(records)


__all__: tuple[str, ...] = ()
