"""Economic-calendar numeric normalization boundary."""

from decimal import Decimal

from app.services.data.economic_calendar.scraper import _decimal


def normalize_calendar_number(value: object) -> Decimal | None:
    """Normalize one bounded provider number to Decimal.

    Args:
        value: The ``value`` argument.

    Returns:
        The result produced by the operation.
    """
    return _decimal(value)


__all__ = ["normalize_calendar_number"]
