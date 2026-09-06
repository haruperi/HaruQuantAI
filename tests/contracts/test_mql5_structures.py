"""Construction, strictness, and round-trip tests for neutral structures."""

import subprocess
import sys
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest
from app.contracts.broker.models import WIRE_MODELS as BROKER_MODELS
from app.contracts.broker.structures import TradeResult
from app.contracts.common.models import WIRE_MODELS as COMMON_MODELS
from app.contracts.common.models import WireModel as CompatibilityWireModel
from app.contracts.common.structures import DateTimeParts
from app.contracts.common.wire_model import WireModel
from app.contracts.data.calendar_constants import (
    CALENDAR_FREQUENCY_NONE,
    CALENDAR_IMPACT_NA,
    CALENDAR_IMPORTANCE_NONE,
    CALENDAR_MULTIPLIER_NONE,
    CALENDAR_SECTOR_NONE,
    CALENDAR_TIMEMODE_DATETIME,
    CALENDAR_TYPE_EVENT,
    CALENDAR_UNIT_NONE,
)
from app.contracts.data.models import WIRE_MODELS as DATA_MODELS
from app.contracts.data.models import Tick as RichTick
from app.contracts.data.structures import (
    CalendarCountry,
    CalendarEvent,
    CalendarValue,
    OrderBookEntry,
    RateBar,
)
from app.contracts.data.structures import (
    Tick as ExactTick,
)
from app.contracts.indicator.constants import TYPE_INT
from app.contracts.indicator.structures import IndicatorParameter
from app.contracts.risk.models import WIRE_MODELS as RISK_MODELS
from app.contracts.risk.structures import TradeCheckResult
from app.contracts.trading.constants import (
    DEAL_TYPE_BUY,
    ORDER_FILLING_FOK,
    ORDER_STATE_STARTED,
    ORDER_TIME_GTC,
    ORDER_TYPE_BUY,
    TRADE_ACTION_DEAL,
    TRADE_TRANSACTION_ORDER_ADD,
)
from app.contracts.trading.models import WIRE_MODELS as TRADING_MODELS
from app.contracts.trading.structures import TradeRequest, TradeTransaction
from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_structures_are_strict_frozen_and_registered() -> None:
    """Transported neutral records are registered under semantic owners."""
    assert COMMON_MODELS["DateTimeParts"] is DateTimeParts
    assert DATA_MODELS["RateBar"] is RateBar
    assert DATA_MODELS["OrderBookEntry"] is OrderBookEntry
    assert DATA_MODELS["CalendarCountry"] is CalendarCountry
    assert DATA_MODELS["CalendarEvent"] is CalendarEvent
    assert DATA_MODELS["CalendarValue"] is CalendarValue
    assert DATA_MODELS["Tick"] is RichTick
    assert DATA_MODELS["Tick"] is not ExactTick
    assert BROKER_MODELS["TradeResult"] is TradeResult
    assert RISK_MODELS["TradeCheckResult"] is TradeCheckResult
    assert TRADING_MODELS["TradeRequest"] is TradeRequest
    assert TRADING_MODELS["TradeTransaction"] is TradeTransaction
    value = DateTimeParts(
        year=2026,
        month=9,
        day=6,
        hour=12,
        min=0,
        sec=0,
        day_of_week=0,
        day_of_year=248,
    )
    with pytest.raises(ValidationError):
        DateTimeParts(
            year=2026,
            month="9",  # type: ignore[arg-type]
            day=6,
            hour=12,
            min=0,
            sec=0,
            day_of_week=0,
            day_of_year=248,
        )
    with pytest.raises(ValidationError):
        value.month = 10  # type: ignore[misc]


def test_structure_modules_are_independently_importable() -> None:
    """Each focused structure module imports cleanly in a fresh process."""
    modules = (
        "app.contracts.common.structures",
        "app.contracts.indicator.structures",
        "app.contracts.data.structures",
        "app.contracts.risk.structures",
        "app.contracts.trading.structures",
        "app.contracts.broker.structures",
    )
    for module in modules:
        subprocess.run(  # noqa: S603  # Fixed local interpreter and module list.
            [sys.executable, "-c", f"import {module}"],
            cwd=REPO_ROOT,
            check=True,
        )
    assert CompatibilityWireModel is WireModel


def test_all_classified_structure_fields_are_implemented() -> None:
    """Every classified structure and field has one exact neutral record."""
    expected_fields = {
        DateTimeParts: (
            "year",
            "month",
            "day",
            "hour",
            "min",
            "sec",
            "day_of_week",
            "day_of_year",
            "schema_version",
        ),
        IndicatorParameter: (
            "type",
            "integer_value",
            "double_value",
            "string_value",
        ),
        RateBar: (
            "time",
            "open",
            "high",
            "low",
            "close",
            "tick_volume",
            "spread",
            "real_volume",
            "schema_version",
        ),
        OrderBookEntry: ("type", "price", "volume", "volume_real", "schema_version"),
        ExactTick: (
            "time",
            "bid",
            "ask",
            "last",
            "volume",
            "time_msc",
            "flags",
            "volume_real",
            "schema_version",
        ),
        CalendarCountry: (
            "id",
            "name",
            "code",
            "currency",
            "currency_symbol",
            "url_name",
            "schema_version",
        ),
        CalendarEvent: (
            "id",
            "type",
            "sector",
            "frequency",
            "time_mode",
            "country_id",
            "unit",
            "importance",
            "multiplier",
            "digits",
            "source_url",
            "event_code",
            "name",
            "schema_version",
        ),
        CalendarValue: (
            "id",
            "event_id",
            "time",
            "period",
            "revision",
            "actual_value",
            "prev_value",
            "revised_prev_value",
            "forecast_value",
            "impact_type",
            "schema_version",
        ),
        TradeRequest: (
            "action",
            "magic",
            "order",
            "symbol",
            "volume",
            "price",
            "stoplimit",
            "sl",
            "tp",
            "deviation",
            "type",
            "type_filling",
            "type_time",
            "expiration",
            "comment",
            "position",
            "position_by",
            "schema_version",
        ),
        TradeTransaction: (
            "deal",
            "order",
            "symbol",
            "type",
            "order_type",
            "order_state",
            "deal_type",
            "time_type",
            "time_expiration",
            "price",
            "price_trigger",
            "price_sl",
            "price_tp",
            "volume",
            "position",
            "position_by",
            "schema_version",
        ),
        TradeCheckResult: (
            "retcode",
            "balance",
            "equity",
            "profit",
            "margin",
            "margin_free",
            "margin_level",
            "comment",
            "schema_version",
        ),
        TradeResult: (
            "retcode",
            "deal",
            "order",
            "volume",
            "price",
            "bid",
            "ask",
            "comment",
            "request_id",
            "retcode_external",
            "schema_version",
        ),
    }
    assert len(expected_fields) == 12
    for model, fields in expected_fields.items():
        assert tuple(model.model_fields) == fields


def test_rate_bar_and_trade_request_round_trip() -> None:
    """Representative exact structures round-trip through JSON."""
    bar = RateBar(
        time=datetime(2026, 9, 6, tzinfo=UTC),
        open=10.0,
        high=11.0,
        low=9.0,
        close=10.5,
        tick_volume=3,
        spread=2,
        real_volume=3,
    )
    assert RateBar.model_validate_json(bar.model_dump_json()) == bar
    request = TradeRequest(
        action=TRADE_ACTION_DEAL,
        magic=0,
        order=0,
        symbol="EURUSD",
        volume=1.0,
        price=1.1,
        stoplimit=0.0,
        sl=0.0,
        tp=0.0,
        deviation=10,
        type=ORDER_TYPE_BUY,
        type_filling=ORDER_FILLING_FOK,
        type_time=ORDER_TIME_GTC,
    )
    assert TradeRequest.model_validate_json(request.model_dump_json()) == request


def test_indicator_and_calendar_value_records() -> None:
    """Indicator slice and calendar enum fields use canonical enum types."""
    parameter = IndicatorParameter(type=TYPE_INT, integer_value=14)
    assert parameter.type is TYPE_INT
    event = CalendarEvent(
        id=1,
        type=CALENDAR_TYPE_EVENT,
        sector=CALENDAR_SECTOR_NONE,
        frequency=CALENDAR_FREQUENCY_NONE,
        time_mode=CALENDAR_TIMEMODE_DATETIME,
        country_id=1,
        unit=CALENDAR_UNIT_NONE,
        importance=CALENDAR_IMPORTANCE_NONE,
        multiplier=CALENDAR_MULTIPLIER_NONE,
        digits=0,
        source_url="https://example.invalid",
        event_code="TEST",
        name="Test",
    )
    assert event.type is CALENDAR_TYPE_EVENT


def test_classified_integer_fields_enforce_primitive_bounds() -> None:
    """Signed MQL integer and long fields retain their exact widths."""
    schemas = {
        (IndicatorParameter, "integer_value"): (-(2**63), 2**63 - 1),
        (CalendarValue, "revision"): (-(2**31), 2**31 - 1),
        (TradeResult, "retcode_external"): (-(2**31), 2**31 - 1),
        (RateBar, "spread"): (-(2**31), 2**31 - 1),
    }
    for (model, field), (minimum, maximum) in schemas.items():
        property_schema = model.model_json_schema()["properties"][field]
        assert property_schema["minimum"] == minimum
        assert property_schema["maximum"] == maximum

    assert IndicatorParameter(type=TYPE_INT, integer_value=-(2**63)).integer_value == -(
        2**63
    )
    with pytest.raises(ValidationError):
        IndicatorParameter(type=TYPE_INT, integer_value=2**63)

    calendar = {
        "id": 1,
        "event_id": 1,
        "time": datetime(2026, 9, 6, tzinfo=UTC),
        "period": datetime(2026, 9, 6, tzinfo=UTC),
        "actual_value": 0,
        "prev_value": 0,
        "revised_prev_value": 0,
        "forecast_value": 0,
        "impact_type": CALENDAR_IMPACT_NA,
    }
    assert CalendarValue(revision=-(2**31), **calendar).revision == -(2**31)
    with pytest.raises(ValidationError):
        CalendarValue(revision=2**31, **calendar)

    result = {
        "retcode": 0,
        "deal": 0,
        "order": 0,
        "volume": 0.0,
        "price": 0.0,
        "bid": 0.0,
        "ask": 0.0,
        "comment": "",
        "request_id": 0,
    }
    assert TradeResult(retcode_external=-(2**31), **result).retcode_external == -(2**31)
    with pytest.raises(ValidationError):
        TradeResult(retcode_external=2**31, **result)


def test_structure_datetimes_normalize_to_utc_and_reject_naive_values() -> None:
    """Every classified datetime-bearing structure applies one UTC rule."""
    offset_value = datetime(2026, 9, 6, 15, 0, tzinfo=timezone(timedelta(hours=2)))
    expected = datetime(2026, 9, 6, 13, 0, tzinfo=UTC)
    bar = RateBar(
        time=offset_value,
        open=1.0,
        high=1.0,
        low=1.0,
        close=1.0,
        tick_volume=0,
        spread=0,
        real_volume=0,
    )
    tick = ExactTick(
        time=offset_value,
        bid=1.0,
        ask=1.0,
        last=1.0,
        volume=0,
        time_msc=0,
        flags=0,
        volume_real=0.0,
    )
    calendar = CalendarValue(
        id=1,
        event_id=1,
        time=offset_value,
        period=offset_value,
        revision=0,
        actual_value=0,
        prev_value=0,
        revised_prev_value=0,
        forecast_value=0,
        impact_type=CALENDAR_IMPACT_NA,
    )
    request = TradeRequest(
        action=TRADE_ACTION_DEAL,
        magic=0,
        order=0,
        symbol="EURUSD",
        volume=1.0,
        price=1.0,
        stoplimit=0.0,
        sl=0.0,
        tp=0.0,
        deviation=0,
        type=ORDER_TYPE_BUY,
        type_filling=ORDER_FILLING_FOK,
        type_time=ORDER_TIME_GTC,
        expiration=offset_value,
    )
    transaction = TradeTransaction(
        deal=0,
        order=0,
        symbol="EURUSD",
        type=TRADE_TRANSACTION_ORDER_ADD,
        order_type=ORDER_TYPE_BUY,
        order_state=ORDER_STATE_STARTED,
        deal_type=DEAL_TYPE_BUY,
        time_type=ORDER_TIME_GTC,
        time_expiration=offset_value,
        price=1.0,
        price_trigger=0.0,
        price_sl=0.0,
        price_tp=0.0,
        volume=1.0,
        position=0,
        position_by=0,
    )
    assert (
        bar.time,
        tick.time,
        calendar.time,
        calendar.period,
        request.expiration,
        transaction.time_expiration,
    ) == (expected,) * 6
    assert RateBar.model_validate_json(bar.model_dump_json()).time == expected

    naive = offset_value.replace(tzinfo=None)
    with pytest.raises(ValidationError):
        RateBar(
            time=naive,
            open=1.0,
            high=1.0,
            low=1.0,
            close=1.0,
            tick_volume=0,
            spread=0,
            real_volume=0,
        )
    with pytest.raises(ValidationError):
        TradeRequest(**(request.model_dump() | {"expiration": naive}))
