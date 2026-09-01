"""Tests for analytical named sessions and DST-aware regional definitions."""

from datetime import UTC, datetime, time

from app.kernel.identity import generate_id
from app.services.data import get_active_market_sessions
from app.services.data.contracts.responses import unwrap_data_response
from app.services.data.time_sessions.contracts import (
    ActiveMarketSessionsRequest,
    NamedSessionDefinition,
)


def _unwrap(response):
    return unwrap_data_response(
        response,
        operation="data.time_sessions.test",
        request_id="req-00000000-0000-4000-8000-000000000000",
    )


def test_forex_overlap_is_analytical_and_dst_aware() -> None:
    result = _unwrap(
        get_active_market_sessions(
            ActiveMarketSessionsRequest(
                symbol="EURUSD",
                at=datetime(2026, 7, 20, 13, tzinfo=UTC),
                request_id=generate_id("req"),
            )
        )
    )

    assert result.sessions == ("London", "New York")


def test_named_session_supports_cross_midnight_definition() -> None:
    result = _unwrap(
        get_active_market_sessions(
            ActiveMarketSessionsRequest(
                symbol="BTCUSD",
                at=datetime(2026, 7, 20, 23, tzinfo=UTC),
                request_id=generate_id("req"),
            ),
            definitions=(
                NamedSessionDefinition(
                    name="Overnight",
                    timezone="UTC",
                    opens_at=time(22),
                    closes_at=time(2),
                ),
            ),
        )
    )

    assert result.sessions == ("Overnight",)
