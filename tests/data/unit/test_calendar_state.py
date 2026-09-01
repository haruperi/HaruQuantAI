"""Unit tests for calendar-state derivation and MarketContext wiring (FR-DATA-129)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from app.kernel.identity import generate_id
from app.services.data.contracts import DataError
from app.services.data.contracts.responses import unwrap_data_response
from app.services.data.economic_calendar import (
    CALENDAR_STATE_BLACKOUT_BEFORE,
    CALENDAR_STATE_EVENT,
    CALENDAR_STATE_OPEN,
    CALENDAR_STATE_UNKNOWN,
    DEFAULT_MINIMUM_IMPACT,
    EconomicEvent,
    EventImpact,
    calendar_state_provenance,
    derive_calendar_state,
    populate_market_context_calendar,
)
from app.services.data.evidence.market_context_contracts import MarketContextEvidence

_NOW = datetime(2026, 7, 26, 12, tzinfo=UTC)


def _evidence(symbol: str = "EURUSD") -> MarketContextEvidence:
    """Build one minimal calendar-aware evidence with calendar marked missing."""
    return MarketContextEvidence(
        symbol=symbol,
        session_state="open",
        calendar_state=None,
        spread=Decimal("1.0"),
        spread_unit="points",
        liquidity=Decimal(100),
        volatility=Decimal("0.01"),
        correlations={},
        crisis_flags=(),
        timezone="UTC",
        as_of=_NOW,
        expires_at=_NOW + timedelta(minutes=1),
        provenance={"source": "demo"},
        missing_fields=("calendar",),
        request_id=generate_id("req"),
    )


def _event(symbol: str, *, delta: timedelta, impact: EventImpact) -> EconomicEvent:
    """Build one deterministic high-impact USD event at ``_NOW + delta``."""
    currency = {"EURUSD": "USD", "XAUUSD": "USD", "GBPJPY": "GBP"}[symbol]
    country = {"EURUSD": "US", "XAUUSD": "US", "GBPJPY": "GB"}[symbol]
    return EconomicEvent(
        id=f"ff:{symbol}:{delta.total_seconds()}",
        provider="scrape:forexfactory",
        name="CPI",
        category=None,
        country=country,
        currency=currency,
        scheduled_at=_NOW + delta,
        impact=impact,
        actual=None,
        forecast=Decimal("0.3"),
        previous=None,
        actual_raw=None,
        forecast_raw="0.3%",
        previous_raw=None,
        unit="%",
        source="forexfactory",
        source_url=None,
        updated_at=None,
    )


def _unwrap(response):
    return unwrap_data_response(
        response,
        operation="data.economic_calendar.test",
        request_id="req-00000000-0000-4000-8000-000000000000",
    )


def test_derive_calendar_state_blackout_before_writes_provenance_keys() -> None:
    """Derivation returns the canonical state and the two provenance strings."""
    events = [_event("EURUSD", delta=timedelta(minutes=5), impact=EventImpact.HIGH)]
    derived = _unwrap(
        derive_calendar_state(
            "EURUSD", _NOW, events=events, before_minutes=10, after_minutes=10
        )
    )
    assert derived.calendar_state == CALENDAR_STATE_BLACKOUT_BEFORE
    assert derived.event_count == 1
    assert derived.blackout_before_minutes == 10
    assert derived.blackout_after_minutes == 10
    prov = _unwrap(calendar_state_provenance(derived))
    assert prov == {"blackout_before_minutes": "10", "blackout_after_minutes": "10"}


def test_derive_calendar_state_unknown_symbol_raises() -> None:
    """Unregistered symbols fail closed."""
    with pytest.raises(DataError):
        _unwrap(derive_calendar_state("NOTREAL", _NOW, events=[]))


def test_derive_calendar_state_empty_events_returns_open() -> None:
    """A successful empty event set proves that the calendar is open."""
    derived = _unwrap(derive_calendar_state("EURUSD", _NOW, events=[]))
    assert derived.calendar_state == CALENDAR_STATE_OPEN


def test_derive_calendar_state_missing_events_returns_unknown() -> None:
    """Absent acquisition evidence preserves Risk's missing-evidence policy."""
    derived = _unwrap(derive_calendar_state("EURUSD", _NOW, events=None))
    assert derived.calendar_state == CALENDAR_STATE_UNKNOWN


def test_default_minimum_impact_filters_low_events_by_default() -> None:
    """Default minimum impact is HIGH; a LOW event yields open."""
    events = [_event("EURUSD", delta=timedelta(minutes=5), impact=EventImpact.LOW)]
    derived = _unwrap(derive_calendar_state("EURUSD", _NOW, events=events))
    assert derived.calendar_state == CALENDAR_STATE_OPEN
    assert DEFAULT_MINIMUM_IMPACT is EventImpact.HIGH


def test_populate_market_context_calendar_blocks_before_release() -> None:
    """Populating evidence carries the canonical state and merged provenance."""
    evidence = _evidence()
    events = [_event("EURUSD", delta=timedelta(minutes=5), impact=EventImpact.HIGH)]
    new_evidence = _unwrap(
        populate_market_context_calendar(
            evidence, events=events, before_minutes=10, after_minutes=10
        )
    )
    assert new_evidence.calendar_state == CALENDAR_STATE_BLACKOUT_BEFORE
    assert new_evidence.provenance["blackout_before_minutes"] == "10"
    assert new_evidence.provenance["blackout_after_minutes"] == "10"
    assert new_evidence.provenance["source"] == "demo"
    # Once calendar evidence is supplied, "calendar" leaves missing_fields.
    assert "calendar" not in new_evidence.missing_fields
    # The original evidence is preserved (immutable contract).
    assert "calendar" in evidence.missing_fields
    assert new_evidence is not evidence


def test_populate_market_context_calendar_unknown_removes_no_missing_flag() -> None:
    """``unknown`` keeps calendar in Risk's explicit missing-field evidence."""
    evidence = _evidence()
    new_evidence = _unwrap(populate_market_context_calendar(evidence, events=None))
    assert new_evidence.calendar_state == CALENDAR_STATE_UNKNOWN
    assert "calendar" in new_evidence.missing_fields
    assert new_evidence.provenance["blackout_before_minutes"] == "10"


def test_populate_market_context_events_irrelevant_to_symbol_do_not_block() -> None:
    """Events for a different currency are irrelevant to the symbol profile."""
    evidence = _evidence()
    # A GBP event 5 min away has nothing to do with EURUSD (which has EUR and USD).
    gbp_event = EconomicEvent(
        id="ff:gbp",
        provider="scrape:forexfactory",
        name="BoE Rate Decision",
        category=None,
        country="GB",
        currency="GBP",
        scheduled_at=_NOW + timedelta(minutes=5),
        impact=EventImpact.HIGH,
        actual=None,
        forecast=None,
        previous=None,
        actual_raw=None,
        forecast_raw=None,
        previous_raw=None,
        unit=None,
        source="forexfactory",
        source_url=None,
        updated_at=None,
    )
    new_evidence = _unwrap(
        populate_market_context_calendar(evidence, events=[gbp_event])
    )
    assert new_evidence.calendar_state == CALENDAR_STATE_OPEN


def test_calendar_state_event_when_at_release_instant() -> None:
    """An event exactly at the release instant yields the event state."""
    evidence = _evidence(symbol="XAUUSD")
    events = [_event("XAUUSD", delta=timedelta(0), impact=EventImpact.HIGH)]
    new_evidence = _unwrap(populate_market_context_calendar(evidence, events=events))
    assert new_evidence.calendar_state == CALENDAR_STATE_EVENT
