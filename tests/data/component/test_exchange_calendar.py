"""Component tests for explicit exchange-calendar session retrieval."""

from datetime import UTC, date

from app.services.data import get_exchange_sessions
from app.services.data.contracts.responses import unwrap_data_response
from app.services.data.time_sessions.contracts import ExchangeSessionRequest
from app.utils import generate_id


def _unwrap(response):
    return unwrap_data_response(
        response,
        operation="data.time_sessions.test",
        request_id="req-00000000-0000-4000-8000-000000000000",
    )


def test_exchange_sessions_require_explicit_calendar_and_return_utc() -> None:
    sessions = _unwrap(
        get_exchange_sessions(
            ExchangeSessionRequest(
                symbol="IBM",
                calendar_code="XNYS",
                start=date(2026, 7, 6),
                end=date(2026, 7, 6),
                request_id=generate_id("req"),
            )
        )
    )

    assert len(sessions) == 1
    assert sessions[0].source == "exchange:XNYS"
    assert sessions[0].opens_at.tzinfo is UTC
    assert sessions[0].closes_at.tzinfo is UTC


def test_exchange_sessions_reject_unbounded_range_before_library_work() -> None:
    resp = get_exchange_sessions(
        ExchangeSessionRequest(
            symbol="IBM",
            calendar_code="XNYS",
            start=date(2024, 1, 1),
            end=date(2026, 7, 6),
            request_id=generate_id("req"),
        )
    )
    assert resp.status == "error"
    assert resp.error is not None
    assert resp.error.code == "LIMIT_EXCEEDED"
