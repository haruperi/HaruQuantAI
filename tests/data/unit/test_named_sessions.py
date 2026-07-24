"""Tests for analytical named sessions and DST-aware regional definitions."""

from datetime import UTC, datetime, time

from app.services.data import (
    ActiveMarketSessionsRequest,
    NamedSessionDefinition,
    get_active_market_sessions,
)
from app.utils import generate_id


def test_forex_overlap_is_analytical_and_dst_aware() -> None:
    result = get_active_market_sessions(
        ActiveMarketSessionsRequest(
            symbol="EURUSD",
            at=datetime(2026, 7, 20, 13, tzinfo=UTC),
            request_id=generate_id("req"),
        )
    )

    assert result.sessions == ("London", "New York")


def test_named_session_supports_cross_midnight_definition() -> None:
    result = get_active_market_sessions(
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

    assert result.sessions == ("Overnight",)
