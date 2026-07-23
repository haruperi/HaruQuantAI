"""Integration evidence for WF-DATA-016 calendar acquisition and persistence."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.services.data.economic_calendar.scraper import (
    ScrapeOptions,
    scrape_economic_calendar,
)


class _Transport:
    """Deterministic one-site integration transport."""

    async def fetch_site(
        self,
        site: str,
        start: datetime,
        _end: datetime,
    ) -> list[dict[str, object]]:
        """Return one valid row for the requested site."""
        return [
            {
                "site": site,
                "timestamp": start + timedelta(minutes=1),
                "title": "Usage Event",
                "country": "USD",
                "impact": "high",
            }
        ]


def test_calendar_scrape_cleans_projects_and_saves(tmp_path: Path) -> None:
    """One public scrape produces a typed frame and descriptive artifact."""
    start = datetime(2026, 1, 1, tzinfo=UTC)
    result = scrape_economic_calendar(
        ScrapeOptions(
            start=start,
            end=start + timedelta(days=1),
            sites=("forexfactory",),
            transport=_Transport(),
        )
    )

    result.save(tmp_path, "csv")

    assert len(result.events) == 1
    assert len(result.to_dataframe()) == 1
    assert len(tuple(tmp_path.glob("forexfactory_*.csv"))) == 1
