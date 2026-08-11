"""Focused UTC validation for DATA time and session contracts."""

from datetime import datetime, timedelta

from app.services.data.contracts.responses import (
    StandardResponse,
    data_start_time,
)
from app.utils import generate_id


def _require_utc_raw(value: datetime) -> datetime:
    """Return an aware UTC timestamp or reject it without response wrapping.

    Args:
        value: Timestamp to validate.

    Returns:
        The unchanged aware UTC timestamp.

    Raises:
        ValueError: If the timestamp is naive or not UTC.
    """
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("timestamp must be aware UTC")
    return value


def require_utc(value: datetime) -> StandardResponse[datetime]:
    """Return an aware UTC timestamp or reject it.

    Args:
        value: Timestamp to validate.

    Returns:
        Standard response carrying the unchanged aware UTC timestamp.

    Raises:
        (in-band) ``VALIDATION_FAILED`` when the timestamp is naive or not UTC.
    """
    from app.services.data.contracts import DataError
    from app.services.data.contracts.responses import run_data_operation

    def _raw() -> datetime:
        """Validate UTC evidence and translate invalid timestamps.

        Returns:
            The validated aware UTC timestamp.

        Raises:
            DataError: If the timestamp is naive or not UTC.
        """
        try:
            return _require_utc_raw(value)
        except ValueError as error:
            raise DataError(
                "VALIDATION_FAILED",
                safe_details={"field": "timestamp", "reason": "not_aware_utc"},
            ) from error

    return run_data_operation(
        operation="data.time_sessions.require_utc",
        request_id=generate_id("req"),
        start_time=data_start_time(),
        raw=_raw,
    )


__all__ = ["require_utc"]
