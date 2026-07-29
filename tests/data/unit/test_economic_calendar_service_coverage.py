"""Unit tests for economic_calendar/service.py to reach >80% coverage."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from app.services.data.contracts import DataError
from app.services.data.contracts.responses import unwrap_data_response
from app.services.data.economic_calendar.service import (
    get_economic_events,
    get_persisted_events,
    is_news_restricted,
)

_NOW = datetime.now(UTC)


def _unwrap(response):
    return unwrap_data_response(
        response,
        operation="data.economic_calendar.test",
        request_id="req-00000000-0000-4000-8000-000000000000",
    )


@pytest.mark.anyio
async def test_get_economic_events_invalid_window() -> None:
    """Test get_economic_events raises VALIDATION_FAILED when start >= end or naive."""
    mock_provider = MagicMock()

    with pytest.raises(DataError) as exc_info:
        _unwrap(
            await get_economic_events(
                _NOW, _NOW - timedelta(hours=1), provider=mock_provider
            )
        )
    assert exc_info.value.code == "VALIDATION_FAILED"

    with pytest.raises(DataError) as exc_info:
        _unwrap(
            await get_economic_events(datetime.now(), _NOW, provider=mock_provider)  # noqa: DTZ005
        )
    assert exc_info.value.code == "VALIDATION_FAILED"


@pytest.mark.anyio
async def test_is_news_restricted_invalid_input() -> None:
    """Test is_news_restricted raises DataError for naive datetime or negative minutes."""
    mock_provider = MagicMock()

    with pytest.raises(DataError):
        _unwrap(
            await is_news_restricted("EURUSD", datetime.now(), provider=mock_provider)  # noqa: DTZ005
        )

    with pytest.raises(DataError) as exc_info:
        _unwrap(
            await is_news_restricted(
                "EURUSD", _NOW, provider=mock_provider, minutes_before=-5
            )
        )
    assert exc_info.value.code == "VALIDATION_FAILED"


def test_get_persisted_events_invalid_aware() -> None:
    """Test get_persisted_events raises DataError for naive datetime."""
    mock_store = MagicMock()
    with pytest.raises(DataError) as exc_info:
        _unwrap(get_persisted_events(datetime.now(), _NOW, store=mock_store))  # noqa: DTZ005
    assert exc_info.value.code == "VALIDATION_FAILED"
