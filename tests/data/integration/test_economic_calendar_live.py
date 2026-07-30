"""Opt-in live verification for the licensed FEAT-DATA-11 transport."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import pytest
from app.services.data import (
    build_firecrawl_calendar_transport,
    build_scrape_options,
    scrape_economic_calendar,
    scrape_result_to_dataframe,
)


@pytest.mark.skipif(
    os.getenv("HARU_RUN_LIVE_CALENDAR") != "1",
    reason="Set HARU_RUN_LIVE_CALENDAR=1 for licensed live verification",
)
def test_live_forexfactory_calendar_returns_real_bounded_rows() -> None:
    """Retrieve a real recent calendar window through the licensed transport."""
    end = datetime.now(UTC)
    start = end - timedelta(days=7)
    result = scrape_economic_calendar(
        build_scrape_options(
            start=start,
            end=end,
            sites=("forexfactory",),
            max_parallel_tasks=1,
            transport=build_firecrawl_calendar_transport(
                max_parallel_requests=1,
            ),
        )
    )
    frame = scrape_result_to_dataframe(result)

    assert not frame.empty
    assert tuple(frame.columns) == (
        "site",
        "timestamp",
        "title",
        "country",
        "impact",
        "actual",
        "forecast",
        "previous",
    )
    assert set(frame["site"]) == {"forexfactory"}
    assert frame["title"].astype(str).str.len().gt(0).all()
    assert frame["timestamp"].between(start, end, inclusive="left").all()
