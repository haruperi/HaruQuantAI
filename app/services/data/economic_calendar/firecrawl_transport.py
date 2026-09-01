"""Licensed Firecrawl transport for economic-calendar acquisition (FEAT-DATA-11).

The four declared calendar sites (ForexFactory, MetalsMine, EnergyExch,
CryptoCraft) share the Fair Economy calendar application. Their pages are
JavaScript-rendered and bot-protected, so acquisition flows through the
licensed Firecrawl scraping intermediary (`POST /v2/scrape` with the
``enhanced`` proxy tier) rather than a direct embedded crawler.

Timezone discipline: the rendered page displays all timestamps in the viewing
browser's local time and publishes that local time in its ``syncedtime``
element. The transport therefore requests a fresh render (``maxAge: 0``),
captures the Firecrawl HTTP ``Date`` header as the UTC reference instant, and
derives the page offset from the synced display. Event times are converted to
UTC with that per-page offset; if the synced element is absent the page fails
closed rather than guessing a timezone.
"""

from __future__ import annotations

# ruff: noqa: S310 - URL is the fixed audited Firecrawl HTTPS API endpoint.
import asyncio
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from html.parser import HTMLParser
from typing import Any, Final, override

from pydantic import SecretStr

from app.composition.config import load_broker_provider_settings
from app.composition.logging import get_logger
from app.services.data.contracts import DataError
from app.services.data.economic_calendar.scraper import CalendarTransport

logger = get_logger(__name__)

_FIRECRAWL_SCRAPE_URL: Final = "https://api.firecrawl.dev/v2/scrape"
_SITE_BASE_URLS: Final[Mapping[str, str]] = {
    "forexfactory": "https://www.forexfactory.com/calendar",
    "metalsmine": "https://www.metalsmine.com/calendar",
    "energyexch": "https://www.energyexch.com/calendar",
    "cryptocraft": "https://www.cryptocraft.com/calendar",
}
_MONTHS: Final[Mapping[str, int]] = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}
_MAX_WEEK_PAGES: Final = 9
_MAX_PARALLEL_REQUESTS: Final = 8
_MAX_RESPONSE_BYTES: Final = 8 * 1024 * 1024
_MINUTES_PER_DAY: Final = 1440
_HALF_DAY_MINUTES: Final = 720
_OFFSET_STEP_MINUTES: Final = 15
_SYNCED_TIME_PATTERN: Final = re.compile(
    r'<strong class="syncedtime">(\d{1,2}:\d{2}(?:am|pm))</strong>'
)
_IMPACT_BY_TITLE: Final[Mapping[str, str]] = {
    "Low Impact Expected": "low",
    "Medium Impact Expected": "medium",
    "High Impact Expected": "high",
}

# Niche Fair Economy sites (CryptoCraft, MetalsMine, EnergyExch) render no
# currency cell; their event titles carry a country prefix instead. This
# mapping is transcribed from the genuine 2026-07 week pages. Titles with an
# unrecognized prefix are dropped rather than assigned an invented currency.
_PREFIX_CURRENCY: Final[Mapping[str, str]] = {
    "US": "USD",
    "UK": "GBP",
    "AU": "AUD",
    "JN": "JPY",
    "EZ": "EUR",
    "GE": "EUR",
    "CA": "CAD",
    "CH": "CHF",
}

# The Fair Economy calendar renders unscheduled rows as "All Day" or
# "Tentative" without a clock time; the canonical contract requires one
# instant, so these rows are anchored to the start of their day (page-local)
# rather than dropped or assigned an invented hour.
_DAY_START_TIMES: Final = {"all day", "tentative"}


def _week_param(sunday: date) -> str:
    """Format one Sunday week start as the provider's ``week`` URL parameter.

    Args:
        sunday: The ``sunday`` argument.

    Returns:
        The result produced by the operation.
    """
    month_abbrev = next(key for key, value in _MONTHS.items() if value == sunday.month)
    return f"{month_abbrev}{sunday.day}.{sunday.year}"


def _week_params_covering(start: datetime, end: datetime) -> tuple[str, ...]:
    """Return the Sunday-anchored week parameters covering ``[start, end)``.

    Computation is date-based so time components never affect page selection.

    Args:
        start: The ``start`` argument.
        end: The ``end`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        DataError: If the window spans more than the bounded page count.
    """
    start_day = start.date()
    last_day = (end - timedelta(microseconds=1)).date()
    first_sunday = start_day - timedelta(days=(start_day.weekday() + 1) % 7)
    last_sunday = last_day - timedelta(days=(last_day.weekday() + 1) % 7)
    weeks: list[str] = []
    current = first_sunday
    while current <= last_sunday:
        weeks.append(_week_param(current))
        current += timedelta(days=7)
    if len(weeks) > _MAX_WEEK_PAGES:
        raise DataError("VALIDATION_FAILED", safe_details={"field": "window"})
    return tuple(weeks)


def _resolve_offset_minutes(synced_text: str, utc_reference: datetime) -> int:
    """Return the page-local minus UTC offset in whole fifteen-minute steps.

    The page's synced-time display truncates to the minute; rounding to the
    nearest quarter hour absorbs that truncation plus render latency. World
    timezone offsets are whole quarter hours.

    Args:
        synced_text: The ``synced_text`` argument.
        utc_reference: The ``utc_reference`` argument.

    Returns:
        The result produced by the operation.
    """
    local_hour, local_minute = _parse_clock(synced_text)
    local_minutes = local_hour * 60 + local_minute
    utc_minutes = utc_reference.hour * 60 + utc_reference.minute
    raw = local_minutes - utc_minutes
    if raw <= -_HALF_DAY_MINUTES:
        raw += _MINUTES_PER_DAY
    elif raw > _HALF_DAY_MINUTES:
        raw -= _MINUTES_PER_DAY
    return round(raw / _OFFSET_STEP_MINUTES) * _OFFSET_STEP_MINUTES


def _parse_clock(text: str) -> tuple[int, int]:
    """Parse one ``h:mmam``/``h:mmpm`` clock label into a 24-hour ``(hour, minute)``.

    Args:
        text: The ``text`` argument.

    Returns:
        The result produced by the operation.

    Raises:
        ValueError: If the label does not match the provider clock format.
    """
    match = re.fullmatch(r"(\d{1,2}):(\d{2})(am|pm)", text)
    if not match:
        message = f"Unrecognized provider clock label: {text!r}"
        raise ValueError(message)
    hour = int(match.group(1)) % 12
    if match.group(3) == "pm":
        hour += 12
    return hour, int(match.group(2))


def _cell_value(raw: object) -> str | None:
    """Return the trimmed visible cell text or explicit absence.

    Args:
        raw: The ``raw`` argument.

    Returns:
        The result produced by the operation.
    """
    text = str(raw or "").strip()
    return text or None


def _resolve_currency(row: Mapping[str, Any]) -> str | None:
    """Return the row currency from the currency cell or the title prefix.

    Args:
        row: The ``row`` argument.

    Returns:
        The result produced by the operation.
    """
    currency = str(row.get("currency") or "").strip()
    if currency:
        return currency
    title = str(row.get("title") or "").strip()
    if not title:
        return None
    return _PREFIX_CURRENCY.get(title.split(" ", 1)[0])


class _CalendarPageParser(HTMLParser):
    """Class-driven parser for one rendered Fair Economy calendar page."""

    def __init__(self, *, year: int, offset_minutes: int) -> None:
        """Initialize the parser with the page year and UTC offset context.

        Args:
            year: The ``year`` argument.
            offset_minutes: The ``offset_minutes`` argument.
        """
        super().__init__(convert_charrefs=True)
        self._year = year
        self._offset = timedelta(minutes=offset_minutes)
        self.rows: list[Mapping[str, object]] = []
        self._day: datetime | None = None
        self._last_time: tuple[int, int] | None = None
        self._row: dict[str, Any] | None = None
        self._cell: str | None = None

    @override
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Track row openings, cell classes, and impact span metadata.

        Cells never nest inside one another in this table, so no depth counter
        is required; void elements such as ``<img>`` never emit end tags and
        must not influence cell state.

        Args:
            tag: The ``tag`` argument.
            attrs: The ``attrs`` argument.
        """
        attr = dict(attrs)
        classes = (attr.get("class") or "").split()
        if tag == "tr":
            if self._row is None:
                if "calendar__row--day-breaker" in classes:
                    self._row = {"_day_breaker": True, "_text": ""}
                elif "calendar__row" in classes and attr.get("data-event-id"):
                    self._row = {"event_id": attr["data-event-id"]}
            return
        if self._row is None:
            return
        if tag in {"td", "th"}:
            for cell_class in classes:
                if (
                    cell_class.startswith("calendar__")
                    and cell_class != "calendar__cell"
                ):
                    self._cell = cell_class.removeprefix("calendar__")
                    return
            return
        if tag == "span" and self._cell == "impact":
            self._row["_impact_title"] = attr.get("title") or ""
            self._row["_impact_class"] = attr.get("class") or ""

    @override
    def handle_endtag(self, tag: str) -> None:
        """Close the active cell on ``</td>`` and emit completed rows on ``</tr>``.

        Args:
            tag: The ``tag`` argument.
        """
        if self._row is None:
            return
        if tag in {"td", "th"}:
            self._cell = None
            return
        if tag == "tr":
            self._cell = None
            self._emit()
            self._row = None

    @override
    def handle_data(self, data: str) -> None:
        """Accumulate visible text for the active row or cell.

        Args:
            data: The ``data`` argument.
        """
        if self._row is None:
            return
        if "_day_breaker" in self._row:
            self._row["_text"] += data
            return
        if self._cell is None:
            return
        key = {
            "date": "date_text",
            "time": "time_text",
            "currency": "currency",
            "event": "title",
            "actual": "actual",
            "forecast": "forecast",
            "previous": "previous",
        }.get(self._cell)
        if key is not None:
            self._row[key] = (self._row.get(key) or "") + data

    def _emit(self) -> None:
        """Finalize one parsed row into the raw transport contract."""
        row, self._row = self._row, None
        if row is None:
            return
        if "_day_breaker" in row:
            parsed_day = self._parse_day(row["_text"])
            if parsed_day is not None and parsed_day != self._day:
                self._last_time = None
            self._day = parsed_day or self._day
            return
        date_text = (row.get("date_text") or "").strip()
        if date_text:
            parsed = self._parse_day(date_text)
            if parsed is not None:
                if parsed != self._day:
                    self._last_time = None
                self._day = parsed
        title = (row.get("title") or "").strip()
        currency = _resolve_currency(row)
        if self._day is None or not title or not currency:
            return
        timestamp = self._parse_timestamp((row.get("time_text") or "").strip())
        if timestamp is None:
            return
        self.rows.append(
            {
                "event_id": (row.get("event_id") or "").strip() or None,
                "timestamp": timestamp,
                "title": title,
                "country": currency,
                "impact": self._parse_impact(row),
                "actual": _cell_value(row.get("actual")),
                "forecast": _cell_value(row.get("forecast")),
                "previous": _cell_value(row.get("previous")),
            }
        )

    def _parse_day(self, text: str) -> datetime | None:
        """Parse one ``Sun Jul 26`` style label into the page-year date.

        Args:
            text: The ``text`` argument.

        Returns:
            The result produced by the operation.
        """
        match = re.search(r"([A-Za-z]{3})\s+(\d{1,2})\b", text)
        if not match:
            return None
        month = _MONTHS.get(match.group(1).lower())
        if month is None:
            return None
        # The label is a page-local date; the per-page UTC offset is applied
        # later, so the day anchor carries UTC only as arithmetic context.
        return datetime(self._year, month, int(match.group(2)), tzinfo=UTC)

    def _parse_timestamp(self, time_text: str) -> datetime | None:
        """Combine the current day and the row time label into a UTC instant.

        An empty time label is the provider's same-time-as-above marker: the
        row inherits the most recent explicit clock time of the current day.

        Args:
            time_text: The ``time_text`` argument.

        Returns:
            The result produced by the operation.
        """
        if self._day is None:
            return None
        lowered = time_text.lower()
        if lowered in _DAY_START_TIMES:
            return (self._day - self._offset).replace(tzinfo=UTC)
        if lowered == "":
            if self._last_time is None:
                return None
            local = self._day.replace(
                hour=self._last_time[0], minute=self._last_time[1]
            )
            return (local - self._offset).replace(tzinfo=UTC)
        match = re.fullmatch(r"(\d{1,2}:\d{2}(?:am|pm))", lowered)
        if not match:
            return None
        clock_hour, clock_minute = _parse_clock(match.group(1))
        self._last_time = (clock_hour, clock_minute)
        local = self._day.replace(hour=clock_hour, minute=clock_minute)
        return (local - self._offset).replace(tzinfo=UTC)

    @staticmethod
    def _parse_impact(row: Mapping[str, Any]) -> str:
        """Map the provider impact metadata to the canonical literal.

        Args:
            row: The ``row`` argument.

        Returns:
            The result produced by the operation.
        """
        title = row.get("_impact_title") or ""
        if title in _IMPACT_BY_TITLE:
            return _IMPACT_BY_TITLE[title]
        # Gray-icon rows are non-economic/bank-holiday entries; any
        # unrecognized impact metadata fails to the neutral holiday bucket
        # rather than inventing an importance level.
        return "holiday"


def _parse_page(
    site: str,
    html: str,
    *,
    year: int,
    offset_minutes: int,
) -> list[Mapping[str, object]]:
    """Parse one rendered calendar page into raw `_clean_row`-compatible rows.

    Args:
        site: The ``site`` argument.
        html: The ``html`` argument.
        year: The ``year`` argument.
        offset_minutes: The ``offset_minutes`` argument.

    Returns:
        The result produced by the operation.
    """
    parser = _CalendarPageParser(year=year, offset_minutes=offset_minutes)
    parser.feed(html)
    parser.close()
    seen: set[str] = set()
    rows: list[Mapping[str, object]] = []
    for row in parser.rows:
        event_id = row.get("event_id")
        if isinstance(event_id, str):
            if event_id in seen:
                continue
            seen.add(event_id)
        rows.append(row)
    logger.debug("Parsed %d calendar rows for %s", len(rows), site)
    return rows


class _FirecrawlCalendarTransport(CalendarTransport):
    """Licensed `CalendarTransport` reading the four Fair Economy calendar sites."""

    def __init__(
        self,
        api_key: SecretStr,
        *,
        request_timeout_sec: float = 90.0,
        max_parallel_requests: int = 2,
        wait_for_ms: int = 8000,
    ) -> None:
        """Initialize the transport with licensed credentials and bounds.

        Args:
            api_key: The ``api_key`` argument.
            request_timeout_sec: The ``request_timeout_sec`` argument.
            max_parallel_requests: The ``max_parallel_requests`` argument.
            wait_for_ms: The ``wait_for_ms`` argument.

        Raises:
            DataError: If any bound is invalid.
        """
        if request_timeout_sec <= 0:
            raise DataError(
                "VALIDATION_FAILED", safe_details={"field": "request_timeout_sec"}
            )
        if not 1 <= max_parallel_requests <= _MAX_PARALLEL_REQUESTS:
            raise DataError(
                "VALIDATION_FAILED", safe_details={"field": "max_parallel_requests"}
            )
        if wait_for_ms < 0:
            raise DataError("VALIDATION_FAILED", safe_details={"field": "wait_for_ms"})
        self._api_key = api_key
        self._timeout_sec = float(request_timeout_sec)
        self._wait_for_ms = int(wait_for_ms)
        self._semaphore = asyncio.Semaphore(max_parallel_requests)

    @override
    async def fetch_site(
        self,
        site: str,
        start: datetime,
        end: datetime,
    ) -> Sequence[Mapping[str, object]]:
        """Return raw calendar rows for one site and UTC window.

        Args:
            site: One declared calendar site identifier.
            start: Inclusive UTC window start.
            end: Exclusive UTC window end.

        Returns:
            Raw rows shaped for `scraper._clean_row`, filtered to the window.

        Raises:
            DataError: If the site is undeclared, the window spans too many
                pages, or the licensed scrape fails.
        """
        if site not in _SITE_BASE_URLS:
            raise DataError("VALIDATION_FAILED", safe_details={"field": "site"})
        base_url = _SITE_BASE_URLS[site]
        rows: list[Mapping[str, object]] = []
        for week in _week_params_covering(start, end):
            page_url = f"{base_url}?week={week}"
            html, reference = await self._post(page_url)
            year = int(week.rsplit(".", 1)[1])
            rows.extend(
                _parse_page(
                    site,
                    html,
                    year=year,
                    offset_minutes=self._page_offset(html, reference),
                )
            )
        return [row for row in rows if start <= row["timestamp"] < end]  # type: ignore[operator]

    async def _post(self, page_url: str) -> tuple[str, datetime]:
        """POST one licensed scrape and return ``(html, utc_reference)``.

        Args:
            page_url: The ``page_url`` argument.

        Returns:
            The result produced by the operation.

        Raises:
            DataError: Mapped transport failure; never carries credentials.
        """
        async with self._semaphore:
            try:
                html, reference = await asyncio.wait_for(
                    asyncio.to_thread(self._post_sync, page_url),
                    timeout=self._timeout_sec + 5,
                )
            except TimeoutError as error:
                raise DataError(
                    "TIMEOUT", safe_details={"operation": "firecrawl_scrape"}
                ) from error
            except urllib.error.HTTPError as error:
                mapped = self._map_http_error(error)
                error.close()
                raise mapped from error
            except (urllib.error.URLError, OSError, json.JSONDecodeError) as error:
                raise DataError(
                    "NETWORK_ERROR", safe_details={"operation": "firecrawl_scrape"}
                ) from error
        return html, reference

    def _post_sync(self, page_url: str) -> tuple[str, datetime]:
        """Execute the blocking licensed POST off the event loop.

        Args:
            page_url: The ``page_url`` argument.

        Returns:
            The result produced by the operation.

        Raises:
            DataError: If the intermediary reports failure or malformed output.
        """
        body = json.dumps(
            {
                "url": page_url,
                # The basic proxy tier receives an empty anti-bot shell from
                # these sites; the licensed enhanced tier renders the calendar.
                "proxy": "enhanced",
                "formats": ["html"],
                "onlyMainContent": False,
                "waitFor": self._wait_for_ms,
                # Calendar pages contain no personal input and need no shared
                # intermediary cache. Explicitly retain neither request nor
                # response in Firecrawl's index.
                "storeInCache": False,
                # Firecrawl defaults this to true; financial evidence must
                # never weaken TLS verification.
                "skipTlsVerification": False,
                # A fresh render is mandatory: the page timezone offset is
                # derived against the response Date header.
                "maxAge": 0,
                "timeout": int(self._timeout_sec * 1000),
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            _FIRECRAWL_SCRAPE_URL,
            data=body,
            headers={
                "Authorization": f"Bearer {self._api_key.get_secret_value()}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(request, timeout=self._timeout_sec) as response:
            final_url = response.geturl()
            final_host = urllib.parse.urlsplit(final_url).hostname
            content_type = response.headers.get_content_type()
            if final_host != "api.firecrawl.dev" or content_type != "application/json":
                raise DataError(
                    "NETWORK_ERROR",
                    safe_details={"operation": "firecrawl_scrape"},
                )
            response_bytes = response.read(_MAX_RESPONSE_BYTES + 1)
            if len(response_bytes) > _MAX_RESPONSE_BYTES:
                raise DataError(
                    "LIMIT_EXCEEDED",
                    safe_details={"operation": "firecrawl_scrape"},
                )
            payload = json.loads(response_bytes.decode("utf-8"))
            date_header = response.headers.get("Date")
        reference = (
            datetime.strptime(date_header, "%a, %d %b %Y %H:%M:%S %Z").replace(
                tzinfo=UTC
            )
            if date_header
            else datetime.now(UTC)
        )
        if payload.get("success") is not True:
            raise DataError(
                "NETWORK_ERROR", safe_details={"operation": "firecrawl_scrape"}
            )
        html = payload.get("data", {}).get("html")
        if not isinstance(html, str) or not html:
            raise DataError(
                "NETWORK_ERROR", safe_details={"operation": "firecrawl_scrape"}
            )
        return html, reference

    @staticmethod
    def _map_http_error(error: urllib.error.HTTPError) -> DataError:
        """Map one licensed-intermediary HTTP failure to a canonical code.

        Args:
            error: The ``error`` argument.

        Returns:
            The result produced by the operation.
        """
        if error.code in {401, 402, 403}:
            return DataError(
                "SOURCE_UNAVAILABLE",
                safe_details={"operation": "firecrawl_scrape", "reason": "credentials"},
            )
        return DataError(
            "NETWORK_ERROR",
            safe_details={"operation": "firecrawl_scrape", "status": str(error.code)},
        )

    @staticmethod
    def _page_offset(html: str, utc_reference: datetime) -> int:
        """Derive the page-local offset from the synced-time element.

        Args:
            html: The ``html`` argument.
            utc_reference: The ``utc_reference`` argument.

        Returns:
            The result produced by the operation.

        Raises:
            DataError: If the page does not publish its local time; the
                transport fails closed rather than guessing a timezone.
        """
        match = _SYNCED_TIME_PATTERN.search(html)
        if not match:
            raise DataError(
                "NETWORK_ERROR", safe_details={"operation": "firecrawl_scrape"}
            )
        return _resolve_offset_minutes(match.group(1), utc_reference)


def build_firecrawl_calendar_transport(
    api_key: SecretStr | None = None,
    *,
    request_timeout_sec: float = 90.0,
    max_parallel_requests: int = 2,
    wait_for_ms: int = 8000,
) -> CalendarTransport:
    """Build the licensed Firecrawl calendar transport.

    Args:
        api_key: Explicit licensed key; when absent, the key is resolved from
            database-backed composition through the shared
            `load_broker_provider_settings` boundary.
        request_timeout_sec: Per-page bound for the licensed scrape call.
        max_parallel_requests: Client-side cap on concurrent licensed requests.
        wait_for_ms: Render wait passed to the intermediary.

    Returns:
        An opaque transport ready for `ScrapeOptions.transport` injection.

    Raises:
        DataError: If no licensed key is available or a bound is invalid.
    """
    resolved = api_key
    if resolved is None:
        settings = load_broker_provider_settings()
        resolved = getattr(settings, "firecrawl_api_key", None)
    if resolved is None:
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={
                "operation": "build_firecrawl_calendar_transport",
                "reason": "credentials_missing",
            },
        )
    logger.info("Building the licensed Firecrawl calendar transport")
    return _FirecrawlCalendarTransport(
        resolved,
        request_timeout_sec=request_timeout_sec,
        max_parallel_requests=max_parallel_requests,
        wait_for_ms=wait_for_ms,
    )
