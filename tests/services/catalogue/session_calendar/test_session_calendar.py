"""Unit and functional tests for Sessions and Calendars service."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import override

import pytest
from app.contracts.catalogue.errors import CatalogueFailure
from app.contracts.catalogue.events import (
    MarketCalendarChanged,
    TradingSessionChanged,
)
from app.contracts.catalogue.models import (
    CalendarEarlyClose,
    DefineSessionsRequest,
    DefineSessionsSuccess,
    MarketCalendarVersion,
    TradingInterval,
    TradingSessionDefinition,
)
from app.kernel.events import EventBus
from app.services.catalogue.session_calendar.config import SessionCalendarConfig
from app.services.catalogue.session_calendar.session_calendar import (
    SessionCalendarService,
    fr_cat_define_market_calendars,
    fr_cat_define_trading_sessions,
    fr_cat_preview_trading_intervals,
    main,
)

_REQ_ID = "00000000-0000-7000-8000-000000000001"
_SNAP_ID = "00000000-0000-7000-8000-000000000002"
_CAL_ID = "00000000-0000-7000-8000-000000000010"
_SESS_ID = "00000000-0000-7000-8000-000000000020"


def _make_calendar(
    calendar_id: str = _CAL_ID,
    *,
    version: int = 1,
    timezone: str = "America/New_York",
    holiday_dates: tuple[date, ...] = (date(2026, 7, 3),),
    early_closes: tuple[CalendarEarlyClose, ...] = (
        CalendarEarlyClose(date=date(2026, 11, 27), close_local="13:00:00"),
    ),
) -> MarketCalendarVersion:
    return MarketCalendarVersion(
        calendar_id=calendar_id,
        version=version,
        timezone=timezone,
        holiday_dates=holiday_dates,
        early_closes=early_closes,
        content_hash="c" * 64,
    )


def _make_session(
    session_id: str = _SESS_ID,
    *,
    version: int = 1,
    name: str = "US Equity Regular Trading Hours",
    timezone: str = "America/New_York",
    calendar: MarketCalendarVersion | None = None,
    intervals: tuple[TradingInterval, ...] | None = None,
) -> TradingSessionDefinition:
    if calendar is None:
        calendar = _make_calendar()
    if intervals is None:
        intervals = (
            TradingInterval(
                day_of_week=1, open_local="09:30:00", close_local="16:00:00"
            ),
            TradingInterval(
                day_of_week=2, open_local="09:30:00", close_local="16:00:00"
            ),
            TradingInterval(
                day_of_week=3, open_local="09:30:00", close_local="16:00:00"
            ),
            TradingInterval(
                day_of_week=4, open_local="09:30:00", close_local="16:00:00"
            ),
            TradingInterval(
                day_of_week=5, open_local="09:30:00", close_local="16:00:00"
            ),
        )
    return TradingSessionDefinition(
        session_id=session_id,
        version=version,
        name=name,
        timezone=timezone,
        intervals=intervals,
        calendar=calendar,
        end_of_day_policy="SESSION_CLOSE",
        content_hash="b" * 64,
    )


@pytest.mark.asyncio
async def test_cat_define_market_calendars_upsert_and_event() -> None:
    """FR-CAT-DEFINE_MARKET_CALENDARS: Upsert calendar and publish event."""
    published_events = []

    class MockEventBus(EventBus):
        @override
        async def publish(self, event: object) -> None:
            published_events.append(event)

    service = SessionCalendarService(event_bus=MockEventBus())
    cal = _make_calendar()

    req = DefineSessionsRequest(
        request_id=_REQ_ID,
        capability_snapshot_id=_SNAP_ID,
        operation="UPSERT_CALENDAR",
        calendar=cal,
    )
    res = await fr_cat_define_market_calendars(service, req)
    assert isinstance(res, DefineSessionsSuccess)
    assert res.calendar is not None
    assert res.calendar.timezone == "America/New_York"
    assert res.calendar is not None
    assert res.calendar.calendar_id == _CAL_ID
    assert res.calendar.version == 1

    assert len(published_events) == 1
    assert isinstance(published_events[0], MarketCalendarChanged)
    assert published_events[0].calendar_id == _CAL_ID
    assert published_events[0].version == 1


@pytest.mark.asyncio
async def test_cat_define_trading_sessions_upsert_get_and_event() -> None:
    """FR-CAT-DEFINE_TRADING_SESSIONS: Upsert session, query via GET, and publish event."""
    published_events = []

    class MockEventBus(EventBus):
        @override
        async def publish(self, event: object) -> None:
            published_events.append(event)

    service = SessionCalendarService(event_bus=MockEventBus())
    sess = _make_session()

    upsert_req = DefineSessionsRequest(
        request_id=_REQ_ID,
        capability_snapshot_id=_SNAP_ID,
        operation="UPSERT_SESSION",
        session=sess,
    )
    res_upsert = await fr_cat_define_trading_sessions(service, upsert_req)
    assert isinstance(res_upsert, DefineSessionsSuccess)
    assert res_upsert.session is not None
    assert res_upsert.session.session_id == _SESS_ID
    assert res_upsert.session.name == "US Equity Regular Trading Hours"

    assert len(published_events) == 1
    assert isinstance(published_events[0], TradingSessionChanged)
    assert published_events[0].session_id == _SESS_ID

    get_req = DefineSessionsRequest(
        request_id=_REQ_ID,
        capability_snapshot_id=_SNAP_ID,
        operation="GET",
        session_id=_SESS_ID,
    )
    res_get = await fr_cat_define_trading_sessions(service, get_req)
    assert isinstance(res_get, DefineSessionsSuccess)
    assert res_get.session is not None
    assert res_get.session.session_id == _SESS_ID
    assert res_get.session.timezone == "America/New_York"


@pytest.mark.asyncio
async def test_cat_preview_trading_intervals_normal_and_holiday() -> None:
    """FR-CAT-PREVIEW_TRADING_INTERVALS: Preview intervals with holiday exclusion and early close."""
    service = SessionCalendarService()
    cal = _make_calendar(
        holiday_dates=(date(2026, 7, 3),),
        early_closes=(
            CalendarEarlyClose(date=date(2026, 7, 2), close_local="13:00:00"),
        ),
    )
    sess = _make_session(calendar=cal)

    await service.define_sessions(
        DefineSessionsRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="UPSERT_SESSION",
            session=sess,
        )
    )

    prev_req = DefineSessionsRequest(
        request_id=_REQ_ID,
        capability_snapshot_id=_SNAP_ID,
        operation="PREVIEW",
        session_id=_SESS_ID,
        from_at="2026-06-29T00:00:00.000000Z",
        to_at="2026-07-04T00:00:00.000000Z",
    )
    res = await fr_cat_preview_trading_intervals(service, prev_req)
    assert isinstance(res, DefineSessionsSuccess)
    assert len(res.effective_intervals) == 4

    iv_thu = res.effective_intervals[3]
    assert iv_thu.from_at == "2026-07-02T13:30:00.000000Z"
    assert iv_thu.to_at == "2026-07-02T17:00:00.000000Z"


@pytest.mark.asyncio
async def test_cat_preview_trading_intervals_dst_transition() -> None:
    """FR-CAT-PREVIEW_TRADING_INTERVALS: Preview intervals across DST fallback transition."""
    service = SessionCalendarService()
    sess = _make_session()
    await service.define_sessions(
        DefineSessionsRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="UPSERT_SESSION",
            session=sess,
        )
    )

    prev_req = DefineSessionsRequest(
        request_id=_REQ_ID,
        capability_snapshot_id=_SNAP_ID,
        operation="PREVIEW",
        session_id=_SESS_ID,
        from_at="2026-10-30T00:00:00.000000Z",
        to_at="2026-11-04T00:00:00.000000Z",
    )
    res = await fr_cat_preview_trading_intervals(service, prev_req)
    assert isinstance(res, DefineSessionsSuccess)
    assert len(res.effective_intervals) == 3

    assert res.effective_intervals[0].from_at == "2026-10-30T13:30:00.000000Z"
    assert res.effective_intervals[0].to_at == "2026-10-30T20:00:00.000000Z"

    assert res.effective_intervals[1].from_at == "2026-11-02T14:30:00.000000Z"
    assert res.effective_intervals[1].to_at == "2026-11-02T21:00:00.000000Z"


@pytest.mark.asyncio
async def test_cat_define_sessions_not_found_error() -> None:
    """Verify that unknown session returns CATALOGUE_NOT_FOUND."""
    service = SessionCalendarService()
    get_req = DefineSessionsRequest(
        request_id=_REQ_ID,
        capability_snapshot_id=_SNAP_ID,
        operation="GET",
        session_id="00000000-0000-7000-8000-000000000999",
    )
    res = await service.define_sessions(get_req)
    assert isinstance(res, CatalogueFailure)
    assert res.code == "CATALOGUE_NOT_FOUND"
    assert res.problem.status == 404

    prev_req = DefineSessionsRequest(
        request_id=_REQ_ID,
        capability_snapshot_id=_SNAP_ID,
        operation="PREVIEW",
        session_id="00000000-0000-7000-8000-000000000999",
        from_at="2026-01-01T00:00:00.000000Z",
        to_at="2026-01-02T00:00:00.000000Z",
    )
    res_prev = await service.define_sessions(prev_req)
    assert isinstance(res_prev, CatalogueFailure)
    assert res_prev.code == "CATALOGUE_NOT_FOUND"


@pytest.mark.asyncio
async def test_cat_session_calendar_persistence(tmp_path: Path) -> None:
    """Verify SQLite persistence across service reconnects."""
    db_file = tmp_path / "sessions.db"
    cfg = SessionCalendarConfig(database_path=db_file)
    service1 = SessionCalendarService(config=cfg)
    sess = _make_session()

    await service1.define_sessions(
        DefineSessionsRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="UPSERT_SESSION",
            session=sess,
        )
    )

    service2 = SessionCalendarService(config=cfg)
    res = await service2.define_sessions(
        DefineSessionsRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="GET",
            session_id=_SESS_ID,
        )
    )
    assert isinstance(res, DefineSessionsSuccess)
    assert res.session is not None
    assert res.session.session_id == _SESS_ID


@pytest.mark.asyncio
async def test_main_usage_harness() -> None:
    """Verify executable main usage harness completes without error."""
    await main()


def test_fallback_timezones_direct():
    from datetime import UTC, datetime

    from app.services.catalogue.session_calendar.session_calendar import (
        _CentralEuropeTz,
        _LondonTz,
        _resolve_timezone,
        _USEasternTz,
    )

    # US Eastern
    us_tz = _USEasternTz()
    assert us_tz.tzname(None) == "EST"
    assert us_tz.dst(None).total_seconds() == 0
    assert us_tz.utcoffset(None).total_seconds() == -5 * 3600

    summer_us = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
    winter_us = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    assert us_tz.tzname(summer_us) == "EDT"
    assert us_tz.tzname(winter_us) == "EST"
    assert us_tz.utcoffset(summer_us).total_seconds() == -4 * 3600
    assert us_tz.utcoffset(winter_us).total_seconds() == -5 * 3600
    assert us_tz.dst(summer_us).total_seconds() == 3600
    assert us_tz.dst(winter_us).total_seconds() == 0

    # London
    lon_tz = _LondonTz()
    assert lon_tz.tzname(None) == "GMT"
    assert lon_tz.dst(None).total_seconds() == 0
    assert lon_tz.utcoffset(None).total_seconds() == 0

    summer_lon = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
    winter_lon = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    assert lon_tz.tzname(summer_lon) == "BST"
    assert lon_tz.tzname(winter_lon) == "GMT"
    assert lon_tz.utcoffset(summer_lon).total_seconds() == 3600
    assert lon_tz.utcoffset(winter_lon).total_seconds() == 0
    assert lon_tz.dst(summer_lon).total_seconds() == 3600
    assert lon_tz.dst(winter_lon).total_seconds() == 0

    # Central Europe
    cet_tz = _CentralEuropeTz()
    assert cet_tz.tzname(None) == "CET"
    assert cet_tz.dst(None).total_seconds() == 0
    assert cet_tz.utcoffset(None).total_seconds() == 3600

    summer_cet = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
    winter_cet = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    assert cet_tz.tzname(summer_cet) == "CEST"
    assert cet_tz.tzname(winter_cet) == "CET"
    assert cet_tz.utcoffset(summer_cet).total_seconds() == 2 * 3600
    assert cet_tz.utcoffset(winter_cet).total_seconds() == 3600
    assert cet_tz.dst(summer_cet).total_seconds() == 3600
    assert cet_tz.dst(winter_cet).total_seconds() == 0

    # Resolve timezone
    from datetime import UTC

    assert _resolve_timezone("UTC") == UTC
    assert _resolve_timezone("GMT") == UTC
    assert _resolve_timezone("Etc/UTC") == UTC
    assert _resolve_timezone("America/New_York") is not None
    assert _resolve_timezone("Asia/Tokyo") is not None
    assert _resolve_timezone("NonExistentTz") == UTC


@pytest.mark.asyncio
async def test_spans_next_day_and_early_close():
    service = SessionCalendarService()
    cal = _make_calendar(
        early_closes=(
            CalendarEarlyClose(date=date(2026, 11, 27), close_local="12:00:00"),
        )
    )
    sess = _make_session(
        calendar=cal,
        intervals=(
            TradingInterval(
                day_of_week=5,
                open_local="22:00:00",
                close_local="04:00:00",
                spans_next_day=True,
            ),
        ),
    )
    await service.define_sessions(
        DefineSessionsRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="UPSERT_SESSION",
            session=sess,
        )
    )
    prev = await service.define_sessions(
        DefineSessionsRequest(
            request_id=_REQ_ID,
            capability_snapshot_id=_SNAP_ID,
            operation="PREVIEW",
            session_id=sess.session_id,
            from_at="2026-11-20T00:00:00.000000Z",
            to_at="2026-11-30T00:00:00.000000Z",
        )
    )
    assert isinstance(prev, DefineSessionsSuccess)
    assert len(prev.effective_intervals) > 0
