"""Run multi-site economic calendar scraping examples (FEAT-DATA-07).

Covers `FR-DATA-095` through `FR-DATA-099`. Network access is injected, so this
program runs deterministically without contacting an external site. A deployment
supplies a real `CalendarTransport`; the shape of the call is identical.
"""

import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.services.data import (
    CALENDAR_SITES,
    DataError,
    ScrapeOptions,
    ScrapeResult,
    scrape_economic_calendar,
)

_START = datetime(2026, 1, 1, tzinfo=UTC)
_END = datetime(2026, 1, 8, tzinfo=UTC)

_ROWS = {
    "forexfactory": [
        {
            "timestamp": "2026-01-02T12:30:00Z",
            "title": "Non-Farm Employment Change",
            "country": "USD",
            "impact": "High",
            "actual": "216K",
            "forecast": "170K",
            "previous": "173K",
        },
        {
            "timestamp": "2026-01-02T12:30:00Z",
            "title": "Non-Farm Employment Change",
            "country": "USD",
            "impact": "High",
            "actual": "216K",
            "forecast": "170K",
            "previous": "173K",
        },
        {"timestamp": None, "title": "Malformed", "country": "", "impact": "?"},
    ],
    "metalsmine": [
        {
            "timestamp": "2026-01-03T09:00:00Z",
            "title": "Gold Inventories",
            "country": "XAU",
            "impact": "Medium",
            "actual": "1.2M",
            "forecast": "-",
            "previous": "1.1M",
        }
    ],
}


class _DemonstrationTransport:
    """Deterministic transport standing in for live site access."""

    async def fetch_site(
        self, site: str, _start: datetime, _end: datetime
    ) -> list[dict[str, object]]:
        """Return canned rows for one site."""
        await asyncio.sleep(0)
        if site == "cryptocraft":
            raise TimeoutError(site)
        return _ROWS.get(site, [])


def _header(title: str) -> None:
    """Print one example heading."""
    print(f"\n{'=' * 88}\n{title}\n{'=' * 88}")


def _example_fr_data_095() -> ScrapeResult:
    """Scrape several sites concurrently under a declared bound."""
    _header("FR-DATA-095 scrape_economic_calendar")
    options = ScrapeOptions(
        start=_START,
        end=_END,
        sites=CALENDAR_SITES,
        max_parallel_tasks=2,
        transport=_DemonstrationTransport(),
    )
    result = scrape_economic_calendar(options)
    print("Sites requested:", len(options.sites))
    print("Events collected:", len(result.events))
    print("Sites skipped:", dict(result.skipped))
    return result


def _example_fr_data_096(result: ScrapeResult) -> None:
    """Show duplicate removal and malformed-row filtering."""
    _header("FR-DATA-096 cleaning and validation")
    print("Raw forexfactory rows supplied:", len(_ROWS["forexfactory"]))
    kept = [event for event in result.events if event.site == "forexfactory"]
    print("Validated forexfactory events:", len(kept))
    if kept:
        print("Actual parsed exactly:", kept[0].actual)
        print("Missing previous is explicit:", kept[0].previous)
        print(kept)


def _example_fr_data_097(result: ScrapeResult) -> None:
    """Project the result into the fixed calendar column contract."""
    _header("FR-DATA-097 to_dataframe")
    frame = result.to_dataframe()
    print("Columns:", list(frame.columns))
    print("Rows:", len(frame))


def _example_fr_data_098(result: ScrapeResult) -> None:
    """Save one descriptive artifact per non-empty site frame."""
    _header("FR-DATA-098 save with descriptive names")
    with TemporaryDirectory() as temporary:
        directory = Path(temporary)
        result.save(directory, "csv")
        written = tuple(directory.glob("*.csv"))
        print("Artifacts written:", len(written))
        for path in written:
            print(" -", path.name)


def _example_fr_data_099(result: ScrapeResult) -> None:
    """Round-trip the result through its pickled transport form."""
    _header("FR-DATA-099 serialize and deserialize")
    payload = result.serialize()
    restored = ScrapeResult.deserialize(payload)
    print("Payload bytes:", len(payload))
    print("Events preserved:", restored.events == result.events)


def _demonstrate_feature() -> None:
    """Execute every calendar example."""
    try:
        result = _example_fr_data_095()
        _example_fr_data_096(result)
        _example_fr_data_097(result)
        _example_fr_data_098(result)
        _example_fr_data_099(result)
    except DataError as error:
        print("Calendar example failed:", error.code)


_DEMONSTRATED = [False]


def _demonstrate_once() -> None:
    """Run the feature demonstration once for all requirement entry points."""
    if _DEMONSTRATED[0]:
        return
    _demonstrate_feature()
    _DEMONSTRATED[0] = True


def fr_data_095() -> None:
    "FR-DATA-095: Scrape economic calendar events from multiple sites (ForexFactory, MetalsMine, EnergyExch, CryptoCraft) concurrently, using configurable concurrency (`max_parallel_tasks`) in `ScrapeOptions`."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_096() -> None:
    "FR-DATA-096: Clean and validate raw calendar data into structured records (representing title, country, impact, actual, forecast, previous, and timestamp), filtering duplicates and bad values."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_097() -> None:
    "FR-DATA-097: Return scraped datasets as a pandas DataFrame via a clean encapsulation `ScrapeResult`."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_098() -> None:
    "FR-DATA-098: Automatically save non-empty calendar dataframes using descriptive file names that include the site name, date range, and scrape timestamp; empty dataframes are skipped."  # noqa: E501 - exact specification text
    _demonstrate_once()


def fr_data_099() -> None:
    "FR-DATA-099: Support serialization and deserialization of `ScrapeResult` using python's `pickle` module for easy persistence and transport."  # noqa: E501 - exact specification text
    _demonstrate_once()


def main() -> None:
    """Execute every functional-requirement demonstration."""
    demonstrations = (
        fr_data_095,
        fr_data_096,
        fr_data_097,
        fr_data_098,
        fr_data_099,
    )
    for demonstration in demonstrations:
        demonstration()


if __name__ == "__main__":
    main()
