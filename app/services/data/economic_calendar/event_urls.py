"""Permanent Forex Factory event URL discovery and specification parsing."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Final

from app.services.data.contracts import DataError

_EVENT_URL: Final = re.compile(
    r"^https://www\.forexfactory\.com/calendar/(\d+)(?:-[a-z0-9-]+)?/?$"
)
_TITLE: Final = re.compile(r"^(?:Title:|#) ([A-Z]{2}) (.+?)(?: \|.*)?$", re.MULTILINE)
_LINK: Final = re.compile(r"\[([^]]+)]\((https?://[^)]+)\)")
_REGION_COUNTRY: Final = {
    "AU": "AUD",
    "CA": "CAD",
    "CH": "CHF",
    "CN": "CNY",
    "EZ": "EUR",
    "FR": "EUR",
    "GE": "EUR",
    "IT": "EUR",
    "JN": "JPY",
    "NZ": "NZD",
    "SP": "EUR",
    "UK": "GBP",
    "US": "USD",
}
_MAX_DEFINITION_ID: Final = 10_000


@dataclass(frozen=True, slots=True)
class _EventDefinition:
    """One verified Forex Factory event definition."""

    provider_definition_id: str
    country: str
    title: str
    source_url: str
    source_original: str | None
    source_latest: str | None
    measures: str | None
    effect: str | None
    frequency: str | None
    also_called: str | None
    event_type: str | None


def _section(markdown: str, label: str) -> str | None:
    """Extract one bounded Specs value from Reader Markdown."""
    pattern = re.compile(
        rf"^#+\s*{re.escape(label)}:\s*$\s*(.*?)(?=^#+\s*.+?:\s*$|^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(markdown)
    if match is None:
        return None
    value = " ".join(
        line.strip() for line in match.group(1).splitlines() if line.strip()
    )
    return value.rstrip(";").strip() or None


def parse_event_definition(
    markdown: str,
    source_url: str,
    *,
    country: str | None = None,
) -> dict[str, str | None]:
    """Parse one verified Forex Factory event-definition page.

    Args:
        markdown: Reader Markdown for one detail page.
        source_url: Permanent Forex Factory URL used to retrieve the page.
        country: Optional currency code from the authoritative weekly CSV.

    Returns:
        Nullable scalar definition fields suitable for persistence.

    Raises:
        DataError: If the URL or page identity is not a verified definition.
    """
    url_match = _EVENT_URL.fullmatch(source_url)
    title_match = _TITLE.search(markdown)
    if url_match is None or title_match is None or "## Specs" not in markdown:
        raise DataError("VALIDATION_FAILED", safe_details={"field": "event_page"})
    region, title = title_match.groups()
    resolved_country = country or _REGION_COUNTRY.get(region)
    if resolved_country is None:
        raise DataError("VALIDATION_FAILED", safe_details={"field": "country"})

    source_block = _section(markdown, "Source")
    links = () if source_block is None else tuple(_LINK.finditer(source_block))
    definition = _EventDefinition(
        provider_definition_id=url_match.group(1),
        country=resolved_country,
        title=title.strip(),
        source_url=source_url.rstrip("/"),
        source_original=links[0].group(2) if links else None,
        source_latest=links[1].group(2) if len(links) > 1 else None,
        measures=_section(markdown, "Measures"),
        effect=_section(markdown, "Usual Effect"),
        frequency=_section(markdown, "Frequency"),
        also_called=_section(markdown, "Also Called"),
        event_type=_section(markdown, "Event Type"),
    )
    return asdict(definition)


def discover_event_definitions(
    fetch_page: Callable[[str], str],
    *,
    start_id: int = 1,
    end_id: int = 1024,
) -> Iterator[dict[str, str | None]]:
    """Yield verified definitions from a bounded numeric-ID interval.

    The caller owns rate limiting, retries, and incremental persistence so this
    deterministic iterator remains directly unit-testable without network I/O.
    """
    if start_id < 1 or end_id < start_id or end_id > _MAX_DEFINITION_ID:
        raise DataError("VALIDATION_FAILED", safe_details={"field": "id_range"})
    for definition_id in range(start_id, end_id + 1):
        url = f"https://www.forexfactory.com/calendar/{definition_id}"
        markdown = fetch_page(url)
        try:
            yield parse_event_definition(markdown, url)
        except DataError:
            continue


def definition_parameters(
    definition: dict[str, str | None], *, request_id: str
) -> tuple[object, ...]:
    """Return one definition's ordered persistence parameters."""
    now = datetime.now(UTC).isoformat()
    return (
        "forexfactory",
        definition["provider_definition_id"],
        definition["country"],
        definition["title"],
        definition["source_url"],
        definition["source_original"],
        definition["source_latest"],
        definition["measures"],
        definition["effect"],
        definition["frequency"],
        definition["also_called"],
        definition["event_type"],
        now,
        now,
        now,
        request_id,
    )


__all__ = [
    "definition_parameters",
    "discover_event_definitions",
    "parse_event_definition",
]
