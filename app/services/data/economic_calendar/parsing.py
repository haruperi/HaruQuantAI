"""Economic-calendar parsing boundary."""

from collections.abc import Mapping

from app.services.data.economic_calendar.scraper import CalendarEvent, _clean_row


def parse_calendar_row(site: str, row: Mapping[str, object]) -> CalendarEvent | None:
    """Parse and validate one provider calendar row."""
    return _clean_row(site, row)


__all__ = ["parse_calendar_row"]
