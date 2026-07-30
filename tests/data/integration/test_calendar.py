"""Integration evidence for FEAT-DATA-11 calendar acquisition and persistence."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.services.data import (
    build_data_settings,
    build_scrape_options,
    data_settings_context,
    save_scrape_result,
    scrape_economic_calendar,
    scrape_result_to_dataframe,
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
        build_scrape_options(
            start=start,
            end=start + timedelta(days=1),
            sites=("forexfactory",),
            transport=_Transport(),
        )
    )

    frame = scrape_result_to_dataframe(result)
    with data_settings_context(build_data_settings(approved_storage_roots=(tmp_path,))):
        save_scrape_result(result, tmp_path, "csv")

    assert len(frame) == 1
    assert len(tuple(tmp_path.glob("forexfactory_*.csv"))) == 1
