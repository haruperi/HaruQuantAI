"""Tests for explicit exchange-calendar session retrieval."""

from datetime import UTC, date

import pytest
from app.services.data import DataError, ExchangeSessionRequest, get_exchange_sessions
from app.utils import generate_id


def test_exchange_sessions_require_explicit_calendar_and_return_utc() -> None:
    sessions = get_exchange_sessions(
        ExchangeSessionRequest(
            symbol="IBM",
            calendar_code="XNYS",
            start=date(2026, 7, 6),
            end=date(2026, 7, 6),
            request_id=generate_id("req"),
        )
    )

    assert len(sessions) == 1
    assert sessions[0].source == "exchange:XNYS"
    assert sessions[0].opens_at.tzinfo is UTC
    assert sessions[0].closes_at.tzinfo is UTC


def test_exchange_sessions_reject_unbounded_range_before_library_work() -> None:
    with pytest.raises(DataError) as error:
        get_exchange_sessions(
            ExchangeSessionRequest(
                symbol="IBM",
                calendar_code="XNYS",
                start=date(2024, 1, 1),
                end=date(2026, 7, 6),
                request_id=generate_id("req"),
            )
        )

    assert error.value.code == "LIMIT_EXCEEDED"
