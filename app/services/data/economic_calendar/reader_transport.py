"""Bounded Jina Reader transport for historical Forex Factory pages."""

from __future__ import annotations

# ruff: noqa: S310 - requests are restricted to the fixed audited Reader host.
import asyncio
import hashlib
import re
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, time
from typing import Final, override
from zoneinfo import ZoneInfo

from app.composition.logging import get_logger
from app.services.data.contracts import DataError
from app.services.data.economic_calendar.firecrawl_transport import (
    _week_params_covering,
)
from app.services.data.economic_calendar.scraper import CalendarTransport

logger = get_logger(__name__)

_READER_ORIGIN: Final = "https://r.jina.ai"
_FOREX_FACTORY_ORIGIN: Final = "http://www.forexfactory.com"
_MAX_RESPONSE_BYTES: Final = 4 * 1024 * 1024
_DAY_PATTERN: Final = re.compile(
    r"^(Sun|Mon|Tue|Wed|Thu|Fri|Sat) ([A-Z][a-z]{2}) (\d{1,2})$"
)
_TIME_PATTERN: Final = re.compile(r"^(\d{1,2}):(\d{2})(am|pm)$")
_IMAGE_PATTERN: Final = re.compile(r"!\[[^]]*]\([^)]+\)")
_LINK_PATTERN: Final = re.compile(r"\[([^]]+)]\([^)]+\)")
_IMPACT_BY_IMAGE: Final = {"red": "high", "ora": "medium", "yel": "low"}
_PAGE_TIMEZONE: Final = ZoneInfo("America/Chicago")
_EVENT_URL_PATTERN: Final = re.compile(
    r"^https://www\.forexfactory\.com/calendar/\d+(?:-[a-z0-9-]+)?/?$"
)


def _plain(value: str) -> str:
    """Remove Markdown presentation syntax without changing provider text.

    Args:
        value: The ``value`` argument.

    Returns:
        The result produced by the operation.
    """
    without_images = _IMAGE_PATTERN.sub("", value)
    return _LINK_PATTERN.sub(r"\1", without_images).strip()


def _timestamp(day: datetime, label: str) -> datetime | None:
    """Map one Forex Factory America/Chicago clock label to UTC when defined.

    Args:
        day: The ``day`` argument.
        label: The ``label`` argument.

    Returns:
        The result produced by the operation.
    """
    normalized = label.strip().lower()
    # Multi-day conference labels ("Day 1", etc.) publish no clock time.
    # Anchor them to page-local day start exactly like Forex Factory's All Day rows.
    if normalized in {"all day", "tentative", ""} or normalized.startswith("day "):
        local = datetime.combine(day.date(), time.min, tzinfo=_PAGE_TIMEZONE)
    else:
        match = _TIME_PATTERN.fullmatch(normalized)
        if match is None:
            return None
        hour = int(match.group(1)) % 12
        if match.group(3) == "pm":
            hour += 12
        local = datetime.combine(
            day.date(),
            time(hour, int(match.group(2))),
            tzinfo=_PAGE_TIMEZONE,
        )
    return local.astimezone(UTC)


def _day(match: re.Match[str], year: int) -> datetime:
    """Build one page-local calendar day from a validated heading.

    Args:
        match: The ``match`` argument.
        year: The ``year`` argument.

    Returns:
        The result produced by the operation.
    """
    return datetime.strptime(
        f"{match.group(2)} {match.group(3)} {year} -0600",
        "%b %d %Y %z",
    )


def _parse_reader_markdown(markdown: str, *, year: int) -> list[Mapping[str, object]]:
    """Parse Reader's bounded Forex Factory Markdown table.

    Args:
        markdown: The ``markdown`` argument.
        year: The ``year`` argument.

    Returns:
        The result produced by the operation.
    """
    rows: list[Mapping[str, object]] = []
    current_day: datetime | None = None
    current_time = ""
    ordinals: dict[tuple[str, str, str], int] = {}
    for line in markdown.splitlines():
        if not line.startswith("|") or line.startswith("| ---"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        first = _plain(cells[0]) if cells else ""
        day_match = _DAY_PATTERN.fullmatch(first)
        if day_match and len(cells) == 1:
            current_day = _day(day_match, year)
            continue
        has_day = day_match is not None
        base = 1 if has_day else 0
        if day_match is not None:
            current_day = _day(day_match, year)
        if current_day is None or len(cells) < base + 9:
            continue
        time_text = _plain(cells[base])
        if time_text:
            current_time = time_text
        currency = _plain(cells[base + 1]).upper()
        impact_cell = cells[base + 2]
        title = _plain(cells[base + 3])
        impact = next(
            (
                value
                for key, value in _IMPACT_BY_IMAGE.items()
                if f"impact-{key}" in impact_cell
            ),
            "low",
        )
        if not currency or not title or not current_time:
            continue
        event_time = _timestamp(current_day, current_time)
        if event_time is None:
            continue
        series = (event_time.date().isoformat(), currency, title)
        ordinal = ordinals.get(series, 0)
        ordinals[series] = ordinal + 1
        identity = hashlib.sha256(
            f"{series[0]}\x1f{currency}\x1f{title}\x1f{ordinal}".encode()
        ).hexdigest()
        rows.append(
            {
                "provider_event_id": f"reader:{identity}",
                "timestamp": event_time,
                "country": currency,
                "impact": impact,
                "title": title,
                "actual": _plain(cells[base + 6]) or None,
                "forecast": _plain(cells[base + 7]) or None,
                "previous": (
                    _plain(cells[base + 8]) or None if len(cells) > base + 8 else None
                ),
            }
        )
    return rows


class _ReaderCalendarTransport(CalendarTransport):
    """Read Forex Factory weekly pages through the credential-free Reader API."""

    def __init__(self, *, request_timeout_sec: float = 30.0) -> None:
        """Initialize the fixed-host bounded transport.

        Args:
            request_timeout_sec: The ``request_timeout_sec`` argument.

        Raises:
            DataError: If the operation cannot be completed safely.
        """
        if request_timeout_sec <= 0:
            raise DataError(
                "VALIDATION_FAILED", safe_details={"field": "request_timeout_sec"}
            )
        self._timeout_sec = float(request_timeout_sec)

    @override
    async def fetch_site(
        self,
        site: str,
        start: datetime,
        end: datetime,
    ) -> Sequence[Mapping[str, object]]:
        """Return Forex Factory rows for at most nine weekly pages.

        Args:
            site: The ``site`` argument.
            start: The ``start`` argument.
            end: The ``end`` argument.

        Returns:
            The result produced by the operation.

        Raises:
            DataError: If the operation cannot be completed safely.
        """
        if site != "forexfactory":
            raise DataError("VALIDATION_FAILED", safe_details={"field": "site"})
        rows: list[Mapping[str, object]] = []
        for week in _week_params_covering(start, end):
            markdown = await asyncio.to_thread(self._fetch_week, week)
            rows.extend(
                _parse_reader_markdown(
                    markdown,
                    year=int(week.rsplit(".", 1)[1]),
                )
            )
        return [row for row in rows if start <= row["timestamp"] < end]  # type: ignore[operator]

    def _fetch_week(self, week: str) -> str:
        """Fetch one fixed Reader URL with response bounds.

        Args:
            week: The ``week`` argument.

        Returns:
            The result produced by the operation.

        Raises:
            DataError: If the operation cannot be completed safely.
        """
        target = f"{_FOREX_FACTORY_ORIGIN}/calendar?week={week}"
        url = f"{_READER_ORIGIN}/{target}"
        request = urllib.request.Request(
            url,
            headers={"Accept": "text/plain", "User-Agent": "HaruQuantAI/1"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_sec) as response:
                final = urllib.parse.urlsplit(response.geturl())
                if final.scheme != "https" or final.hostname != "r.jina.ai":
                    raise DataError(
                        "NETWORK_ERROR", safe_details={"operation": "reader"}
                    )
                payload: bytes = response.read(_MAX_RESPONSE_BYTES + 1)
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise DataError(
                "NETWORK_ERROR", safe_details={"operation": "reader"}
            ) from error
        if len(payload) > _MAX_RESPONSE_BYTES:
            raise DataError("LIMIT_EXCEEDED", safe_details={"operation": "reader"})
        markdown = payload.decode("utf-8")
        if "Forex Calendar | Forex Factory" not in markdown:
            raise DataError("NETWORK_ERROR", safe_details={"operation": "reader"})
        return markdown


def build_reader_calendar_transport(
    *, request_timeout_sec: float = 30.0
) -> CalendarTransport:
    """Build the bounded credential-free historical calendar transport.

    Args:
        request_timeout_sec: The ``request_timeout_sec`` argument.

    Returns:
        The result produced by the operation.
    """
    logger.info("Building the bounded Jina Reader calendar transport")
    return _ReaderCalendarTransport(request_timeout_sec=request_timeout_sec)


def fetch_reader_event_page(
    source_url: str, *, request_timeout_sec: float = 30.0
) -> str:
    """Fetch one validated Forex Factory detail page through Jina Reader.

    Args:
        source_url: The ``source_url`` argument.
        request_timeout_sec: The ``request_timeout_sec`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the operation cannot be completed safely.
    """
    if not _EVENT_URL_PATTERN.fullmatch(source_url) or request_timeout_sec <= 0:
        raise DataError("VALIDATION_FAILED", safe_details={"field": "source_url"})
    url = f"{_READER_ORIGIN}/{source_url}"
    request = urllib.request.Request(
        url,
        headers={"Accept": "text/plain", "User-Agent": "HaruQuantAI/1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=request_timeout_sec) as response:
            final = urllib.parse.urlsplit(response.geturl())
            if final.scheme != "https" or final.hostname != "r.jina.ai":
                raise DataError("NETWORK_ERROR", safe_details={"operation": "reader"})
            payload: bytes = response.read(_MAX_RESPONSE_BYTES + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise DataError(
            "NETWORK_ERROR", safe_details={"operation": "reader"}
        ) from error
    if len(payload) > _MAX_RESPONSE_BYTES:
        raise DataError("LIMIT_EXCEEDED", safe_details={"operation": "reader"})
    return payload.decode("utf-8")


__all__ = ["build_reader_calendar_transport", "fetch_reader_event_page"]
