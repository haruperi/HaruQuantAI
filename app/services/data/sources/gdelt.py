"""GDELT headline-metadata normalization."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from app.services.data.contracts.errors import DataError


def _seen(value: object, fallback: datetime) -> datetime:
    """Parse a GDELT seen date or return observation time.

    Args:
        value: The ``value`` argument.
        fallback: The ``fallback`` argument.

    Returns:
        The result produced by the operation.
    """
    text = str(value or "")
    try:
        return datetime.strptime(text, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
    except ValueError:
        return fallback


def parse_payload(
    payload: bytes,
    observed_at: datetime,
) -> tuple[dict[str, object], ...]:
    """Parse headline metadata without publisher article bodies.

    Args:
        payload: The ``payload`` argument.
        observed_at: The ``observed_at`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the operation cannot be completed safely.
    """
    try:
        articles = json.loads(payload)["articles"]
    except (KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DataError(
            "INVALID_INPUT", safe_details={"field": "gdelt_payload"}
        ) from error
    records: list[dict[str, object]] = []
    for article in articles[:200]:
        title = str(article.get("title", "")).strip()
        url = str(article.get("url", "")).strip()
        if not title or not url:
            continue
        first_seen = _seen(article.get("seendate"), observed_at)
        records.append(
            {
                "external_id": url,
                "document_kind": "news_headline",
                "title": title[:1024],
                "published_at": first_seen.isoformat(),
                "available_at": first_seen.isoformat(),
                "canonical_locator": url,
                "parser_version": "gdelt-doc-v1",
                "language": str(article.get("language", "")),
                "source_domain": str(article.get("domain", "")),
                "source_country": str(article.get("sourcecountry", "")),
                "observations": (),
            }
        )
    return tuple(records)


__all__: tuple[str, ...] = ()
