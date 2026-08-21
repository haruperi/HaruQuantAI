"""Tests for FR-DATA-VALIDATE_REQUEST."""

from datetime import UTC, datetime

import pytest

from app.contracts.data.historical_bars import HistoricalBarsRequest
from app.services.data.historical_bars.validate_request import (
    validate_historical_request,
)


def test_validate_request_success() -> None:
    """Test valid historical bar query passes validation."""
    req = HistoricalBarsRequest(
        symbol="EURUSD",
        timeframe="M1",
        start=datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
        end=datetime(2026, 1, 1, 1, 0, tzinfo=UTC),
    )
    validate_historical_request(req)


def test_validate_request_empty_symbol_raises() -> None:
    """Test empty symbol raises ValueError."""
    req = HistoricalBarsRequest(
        symbol="   ",
        timeframe="M1",
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 1, 2, tzinfo=UTC),
    )
    with pytest.raises(ValueError, match="Symbol must not be empty"):
        validate_historical_request(req)


def test_validate_request_inverted_dates_raises() -> None:
    """Test end date before or equal to start date raises ValueError."""
    req = HistoricalBarsRequest(
        symbol="EURUSD",
        timeframe="M1",
        start=datetime(2026, 1, 2, tzinfo=UTC),
        end=datetime(2026, 1, 1, tzinfo=UTC),
    )
    with pytest.raises(
        ValueError, match=r"End datetime .* must be strictly after start"
    ):
        validate_historical_request(req)


def test_validate_request_invalid_timeframe_raises() -> None:
    """Test invalid timeframe format raises ValueError."""
    req = HistoricalBarsRequest(
        symbol="EURUSD",
        timeframe="UNKNOWN",
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 1, 2, tzinfo=UTC),
    )
    with pytest.raises(ValueError, match="Invalid timeframe 'UNKNOWN'"):
        validate_historical_request(req)
