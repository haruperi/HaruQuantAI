"""Concurrent multi-site economic calendar scraping, cleaning, and persistence.

Network access is supplied by an injected `CalendarTransport`, following the same
injected-dependency pattern as `MarketContextProvider` and `FXRateProvider`. That
keeps parsing, cleaning, validation, and persistence deterministically testable.
The package ships one licensed production transport in
`economic_calendar/firecrawl_transport.py`; tests continue to inject deterministic
transports, and without any declared transport the pipeline fails closed.
"""

from __future__ import annotations

import asyncio
import hashlib

# FR-DATA-099 specifies pickle for ScrapeResult transport. Only locally produced,
# trusted payloads may be deserialized; see ScrapeResult.deserialize.
import pickle
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from importlib import import_module
from typing import TYPE_CHECKING, Final, Literal, Protocol

from app.services.data.contracts import DataError
from app.services.data.persistence.paths import resolve_approved_storage_path
from app.utils import get_logger

logger = get_logger(__name__)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    import pandas as pd
else:

    class _LazyPandas:
        """Load pandas only when calendar parsing or projection requires it."""

        def __getattr__(self, name: str) -> object:
            """Resolve one pandas attribute at the runtime operation boundary.

            Args:
                name: The ``name`` argument.

            Returns:
                The result produced by the operation.
            """
            return getattr(import_module("pandas"), name)

    pd = _LazyPandas()

CALENDAR_SITES: Final[tuple[str, ...]] = (
    "forexfactory",
    "metalsmine",
    "energyexch",
    "cryptocraft",
)

_IMPACTS: Final[frozenset[str]] = frozenset({"low", "medium", "high", "holiday"})
_COLUMNS: Final[tuple[str, ...]] = (
    "site",
    "timestamp",
    "title",
    "country",
    "impact",
    "actual",
    "forecast",
    "previous",
)
_MAX_PARALLEL: Final = 8


class CalendarTransport(Protocol):
    """Read-only transport returning raw calendar rows for one site."""

    async def fetch_site(
        self,
        site: str,
        start: datetime,
        end: datetime,
    ) -> Sequence[Mapping[str, object]]:
        """Return raw provider rows for one site and UTC window.

        Args:
            site: The ``site`` argument.
            start: The ``start`` argument.
            end: The ``end`` argument.
        """
        ...


@dataclass(frozen=True)
class ScrapeOptions:
    """Bounded declaration of one calendar scrape."""

    start: datetime
    end: datetime
    sites: tuple[str, ...] = CALENDAR_SITES
    max_parallel_tasks: int = 4
    request_id: str | None = None
    transport: CalendarTransport | None = field(
        default=None,
        repr=False,
        compare=False,
    )

    def __post_init__(self) -> None:
        """Validate scrape bounds.

        Raises:
            DataError: If the window, site list, or concurrency is invalid.
        """
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise DataError("VALIDATION_FAILED", safe_details={"field": "window"})
        if self.start >= self.end:
            raise DataError("VALIDATION_FAILED", safe_details={"field": "window"})
        if not self.sites:
            raise DataError("VALIDATION_FAILED", safe_details={"field": "sites"})
        unknown = sorted(set(self.sites) - set(CALENDAR_SITES))
        if unknown:
            raise DataError("VALIDATION_FAILED", safe_details={"field": "sites"})
        if not 1 <= self.max_parallel_tasks <= _MAX_PARALLEL:
            raise DataError(
                "VALIDATION_FAILED",
                safe_details={"field": "max_parallel_tasks"},
            )


@dataclass(frozen=True)
class CalendarEvent:
    """One cleaned, validated calendar observation."""

    site: str
    timestamp: datetime
    title: str
    country: str
    impact: Literal["low", "medium", "high", "holiday"]
    provider_event_id: str
    actual: Decimal | None = None
    forecast: Decimal | None = None
    previous: Decimal | None = None
    actual_raw: str | None = None
    forecast_raw: str | None = None
    previous_raw: str | None = None


@dataclass(frozen=True)
class ScrapeResult:
    """Immutable outcome of one multi-site scrape."""

    events: tuple[CalendarEvent, ...]
    sites: tuple[str, ...]
    start: datetime
    end: datetime
    scraped_at: datetime
    skipped: Mapping[str, str] = field(default_factory=dict)

    def to_dataframe(self) -> pd.DataFrame:
        """Return a new analytical projection of the scraped events.

        Returns:
            A DataFrame with the fixed calendar column contract; empty results
            still carry the full column set.
        """
        logger.debug("Projecting %d calendar events", len(self.events))
        if not self.events:
            return pd.DataFrame(columns=list(_COLUMNS))
        return pd.DataFrame(
            [
                {
                    "site": event.site,
                    "timestamp": event.timestamp,
                    "title": event.title,
                    "country": event.country,
                    "impact": event.impact,
                    "actual": event.actual,
                    "forecast": event.forecast,
                    "previous": event.previous,
                }
                for event in self.events
            ],
            columns=list(_COLUMNS),
        )

    def save(self, directory: Path, format: str = "csv") -> None:  # noqa: A002
        """Write one descriptive artifact per site with a non-empty frame.

        Empty frames are skipped rather than written as headers-only files.

        Args:
            directory: Existing destination directory.
            format: Either `csv` or `parquet`.

        Raises:
            DataError: If the format is unsupported or a write fails.
        """
        approved_directory = resolve_approved_storage_path(directory)
        logger.info("Saving calendar artifacts to an approved storage path")
        if format not in {"csv", "parquet"}:
            raise DataError("VALIDATION_FAILED", safe_details={"field": "format"})
        frame = self.to_dataframe()
        stamp = self.scraped_at.strftime("%Y%m%dT%H%M%SZ")
        window = f"{self.start.strftime('%Y%m%d')}_{self.end.strftime('%Y%m%d')}"
        try:
            for site in self.sites:
                site_frame = frame[frame["site"] == site] if not frame.empty else frame
                if site_frame.empty:
                    logger.info("Skipping empty calendar frame for %s", site)
                    continue
                path = approved_directory / f"{site}_{window}_{stamp}.{format}"
                if format == "csv":
                    site_frame.to_csv(path, index=False)
                else:
                    site_frame.to_parquet(path, index=False)
        except OSError as error:
            logger.exception("Calendar artifact write failed")
            raise DataError(
                "DB_WRITE_FAILED",
                safe_details={"operation": "save_calendar"},
            ) from error

    def serialize(self) -> bytes:
        """Return a pickled representation of this result.

        Returns:
            The pickled result bytes.

        Note:
            `FR-DATA-099` specifies pickle. Pickle payloads execute arbitrary code
            on load, so only trusted, locally produced bytes may be deserialized.
            Never load a payload received across a trust boundary.
        """
        logger.debug("Serializing a calendar scrape result")
        return pickle.dumps(self)

    @staticmethod
    def deserialize(payload: bytes) -> ScrapeResult:
        """Rebuild one result from locally produced trusted bytes.

        Args:
            payload: Bytes previously produced by `serialize`.

        Returns:
            The reconstructed result.

        Raises:
            DataError: If the payload is not a valid result.
        """
        logger.debug("Deserializing a calendar scrape result")
        try:
            value = pickle.loads(payload)  # noqa: S301 - trusted local payload only.
        except (pickle.UnpicklingError, AttributeError, EOFError, TypeError) as error:
            raise DataError(
                "FILE_CORRUPTED",
                safe_details={"operation": "deserialize_calendar"},
            ) from error
        if not isinstance(value, ScrapeResult):
            raise DataError(
                "VALIDATION_FAILED",
                safe_details={"field": "payload"},
            )
        return value


def _decimal(value: object) -> Decimal | None:
    """Return an exact decimal or explicit absence for a raw calendar value.

    Args:
        value: The ``value`` argument.

    Returns:
        The result produced by the operation.
    """
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text or text in {"-", "--", "n/a", "N/A"}:
        return None
    multiplier = Decimal(1)
    if text[-1] in {"K", "k"}:
        multiplier, text = Decimal(1_000), text[:-1]
    elif text[-1] in {"M", "m"}:
        multiplier, text = Decimal(1_000_000), text[:-1]
    elif text[-1] in {"B", "b"}:
        multiplier, text = Decimal(1_000_000_000), text[:-1]
    text = text.removesuffix("%")
    try:
        return Decimal(text) * multiplier
    except InvalidOperation:
        return None


def _raw_value(value: object) -> str | None:
    """Return the trimmed provider representation or explicit absence.

    Args:
        value: The ``value`` argument.

    Returns:
        The result produced by the operation.
    """
    if value is None:
        return None
    text = str(value).strip()
    return None if not text or text in {"-", "--", "n/a", "N/A"} else text


def _provider_event_id(
    site: str,
    row: Mapping[str, object],
    *,
    timestamp: datetime,
    title: str,
    country: str,
) -> str:
    """Return a provider identifier stable across intraday schedule changes.

    Args:
        site: The ``site`` argument.
        row: The ``row`` argument.
        timestamp: The ``timestamp`` argument.
        title: The ``title`` argument.
        country: The ``country`` argument.

    Returns:
        The result produced by the operation.
    """
    for key in ("provider_event_id", "event_id", "id"):
        value = _raw_value(row.get(key))
        if value is not None:
            return value
    identity = f"{site}|{timestamp.date().isoformat()}|{country}|{title}"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _clean_row(site: str, row: Mapping[str, object]) -> CalendarEvent | None:
    """Validate one raw row into a canonical event, or discard it.

    Args:
        site: The ``site`` argument.
        row: The ``row`` argument.

    Returns:
        The result produced by the operation.
    """
    title = str(row.get("title", "")).strip()
    country = str(row.get("country", "")).strip()
    impact = str(row.get("impact", "")).strip().lower()
    raw_time = row.get("timestamp")
    if not title or not country or impact not in _IMPACTS or raw_time is None:
        return None
    try:
        timestamp = pd.to_datetime(raw_time, utc=True).to_pydatetime()
    except TypeError, ValueError:
        return None
    return CalendarEvent(
        site=site,
        timestamp=timestamp,
        title=title,
        country=country,
        impact=impact,  # type: ignore[arg-type]
        provider_event_id=_provider_event_id(
            site,
            row,
            timestamp=timestamp,
            title=title,
            country=country,
        ),
        actual=_decimal(row.get("actual")),
        forecast=_decimal(row.get("forecast")),
        previous=_decimal(row.get("previous")),
        actual_raw=_raw_value(row.get("actual")),
        forecast_raw=_raw_value(row.get("forecast")),
        previous_raw=_raw_value(row.get("previous")),
    )


async def _scrape_site(
    site: str,
    options: ScrapeOptions,
    transport: CalendarTransport,
    semaphore: asyncio.Semaphore,
) -> tuple[str, tuple[CalendarEvent, ...], str | None]:
    """Fetch and clean one site under the shared concurrency bound.

    Args:
        site: The ``site`` argument.
        options: The ``options`` argument.
        transport: The ``transport`` argument.
        semaphore: The ``semaphore`` argument.

    Returns:
        The result produced by the operation.
    """
    async with semaphore:
        logger.info("Scraping economic calendar site %s", site)
        try:
            rows = await transport.fetch_site(site, options.start, options.end)
        except DataError as error:
            return site, (), error.code
        except OSError, TimeoutError, ValueError:
            # One site failing must not fail the whole scrape; the reason is
            # recorded in `skipped` rather than silently dropped.
            logger.warning("Calendar transport failed for %s", site)
            return site, (), "NETWORK_ERROR"
    cleaned = [_clean_row(site, row) for row in rows]
    events = tuple(event for event in cleaned if event is not None)
    deduplicated: dict[tuple[str, str], CalendarEvent] = {}
    for event in events:
        deduplicated.setdefault((event.site, event.provider_event_id), event)
    return site, tuple(deduplicated.values()), None


async def _gather(options: ScrapeOptions, transport: CalendarTransport) -> ScrapeResult:
    """Run every site scrape concurrently under the declared bound.

    Args:
        options: The ``options`` argument.
        transport: The ``transport`` argument.

    Returns:
        The result produced by the operation.
    """
    semaphore = asyncio.Semaphore(options.max_parallel_tasks)
    outcomes = await asyncio.gather(
        *(_scrape_site(site, options, transport, semaphore) for site in options.sites)
    )
    events: list[CalendarEvent] = []
    skipped: dict[str, str] = {}
    for site, site_events, failure in outcomes:
        if failure is not None:
            skipped[site] = failure
            continue
        events.extend(site_events)
    events.sort(key=lambda event: (event.timestamp, event.site, event.title))
    return ScrapeResult(
        events=tuple(events),
        sites=options.sites,
        start=options.start,
        end=options.end,
        scraped_at=datetime.now(UTC),
        skipped=skipped,
    )


def scrape_economic_calendar(
    options: ScrapeOptions,
    transport: CalendarTransport | None = None,
) -> ScrapeResult:
    """Scrape, clean, and validate calendar events across the declared sites.

    Sites are fetched concurrently under `max_parallel_tasks`. A site that fails is
    recorded in `skipped` with its reason rather than failing the whole scrape or
    silently returning nothing.

    Args:
        options: Bounded scrape declaration.
        transport: Optional direct injection retained for low-level callers. The
            documented public form carries this dependency on ``options``.

    Returns:
        The cleaned, deduplicated, chronologically ordered result.

    Raises:
        DataError: If no transport is declared or every requested site fails.
    """
    logger.info("Scraping %d economic calendar sites", len(options.sites))
    active_transport = options.transport if options.transport is not None else transport
    if active_transport is None:
        raise DataError(
            "SOURCE_UNAVAILABLE",
            safe_details={"operation": "scrape_economic_calendar"},
            request_id=options.request_id,
        )
    result = asyncio.run(_gather(options, active_transport))
    if not result.events and len(result.skipped) == len(options.sites):
        raise DataError(
            "NETWORK_ERROR",
            safe_details={"operation": "scrape_economic_calendar"},
            request_id=options.request_id,
        )
    return result


def scrape_result_to_dataframe(result: ScrapeResult) -> pd.DataFrame:
    """Project a scrape result through the public function boundary.

    Args:
        result: The ``result`` argument.

    Returns:
        The result produced by the operation.
    """
    return result.to_dataframe()


def save_scrape_result(
    result: ScrapeResult, directory: Path, file_format: str = "csv"
) -> None:
    """Persist a scrape result through the public function boundary.

    Args:
        result: The ``result`` argument.
        directory: The ``directory`` argument.
        file_format: The ``file_format`` argument.
    """
    result.save(directory, file_format)


def serialize_scrape_result(result: ScrapeResult) -> bytes:
    """Serialize a scrape result through the public function boundary.

    Args:
        result: The ``result`` argument.

    Returns:
        The result produced by the operation.
    """
    return result.serialize()


def deserialize_scrape_result(payload: bytes) -> ScrapeResult:
    """Deserialize a trusted scrape result through the public boundary.

    Args:
        payload: The ``payload`` argument.

    Returns:
        The result produced by the operation.
    """
    return ScrapeResult.deserialize(payload)


def get_calendar_value_field(value: object, field: str) -> object:
    """Return one approved public field from an economic-calendar value.

    Args:
        value: Opaque calendar contract returned by the Data package root.
        field: Non-private field name.

    Returns:
        Detached or immutable field value.

    Raises:
        ValueError: If the field is private or unavailable.
    """
    if not field or field.startswith("_") or not hasattr(value, field):
        raise ValueError("Economic-calendar value does not expose the field")
    return getattr(value, field)


__all__ = [
    "CALENDAR_SITES",
    "CalendarEvent",
    "CalendarTransport",
    "ScrapeOptions",
    "ScrapeResult",
    "deserialize_scrape_result",
    "get_calendar_value_field",
    "save_scrape_result",
    "scrape_economic_calendar",
    "scrape_result_to_dataframe",
    "serialize_scrape_result",
]
