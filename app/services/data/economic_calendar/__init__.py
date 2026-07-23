"""Focused economic-calendar acquisition and normalization."""

from app.services.data.economic_calendar.scraper import (
    CalendarEvent,
    CalendarTransport,
    ScrapeOptions,
    ScrapeResult,
    scrape_economic_calendar,
)

__all__ = [
    "CalendarEvent",
    "CalendarTransport",
    "ScrapeOptions",
    "ScrapeResult",
    "scrape_economic_calendar",
]
