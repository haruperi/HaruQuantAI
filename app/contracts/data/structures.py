"""Platform-neutral market-data structures derived from the MQL5 reference."""

from typing import Annotated, Literal, Self

from pydantic import AwareDatetime, Field, model_validator

from app.contracts.common.wire_model import UtcWireModel, as_utc
from app.contracts.data.calendar_constants import (  # noqa: TC001
    ENUM_CALENDAR_EVENT_FREQUENCY,
    ENUM_CALENDAR_EVENT_IMPACT,
    ENUM_CALENDAR_EVENT_IMPORTANCE,
    ENUM_CALENDAR_EVENT_MULTIPLIER,
    ENUM_CALENDAR_EVENT_SECTOR,
    ENUM_CALENDAR_EVENT_TIMEMODE,
    ENUM_CALENDAR_EVENT_TYPE,
    ENUM_CALENDAR_EVENT_UNIT,
)
from app.contracts.data.market_data_constants import ENUM_BOOK_TYPE  # noqa: TC001

UInt = Annotated[int, Field(ge=0, le=4_294_967_295)]
Int = Annotated[int, Field(ge=-2_147_483_648, le=2_147_483_647)]
ULong = Annotated[int, Field(ge=0, le=18_446_744_073_709_551_615)]
Long = Annotated[
    int,
    Field(ge=-9_223_372_036_854_775_808, le=9_223_372_036_854_775_807),
]
NonNegativeFloat = Annotated[float, Field(ge=0)]


class RateBar(UtcWireModel):
    """One OHLC market-data bar."""

    time: AwareDatetime
    open: NonNegativeFloat
    high: NonNegativeFloat
    low: NonNegativeFloat
    close: NonNegativeFloat
    tick_volume: Long
    spread: Int
    real_volume: Long
    schema_version: Literal[1] = 1

    @model_validator(mode="after")
    def validate_price_range(self) -> Self:
        """Require the high/low envelope to contain open and close.

        Returns:
            The validated bar.

        Raises:
            ValueError: If open or close falls outside the high/low range.
        """
        if self.high < max(self.open, self.close) or self.low > min(
            self.open, self.close
        ):
            raise ValueError("bar high/low must contain open and close")
        return self


class OrderBookEntry(UtcWireModel):
    """One price level in an order-book snapshot."""

    type: ENUM_BOOK_TYPE
    price: NonNegativeFloat
    volume: Long
    volume_real: NonNegativeFloat
    schema_version: Literal[1] = 1


class Tick(UtcWireModel):
    """One provider-neutral market tick."""

    time: AwareDatetime
    bid: NonNegativeFloat
    ask: NonNegativeFloat
    last: NonNegativeFloat
    volume: ULong
    time_msc: Long
    flags: UInt
    volume_real: NonNegativeFloat
    schema_version: Literal[1] = 1


class CalendarCountry(UtcWireModel):
    """Economic-calendar country metadata."""

    id: ULong
    name: str
    code: str
    currency: str
    currency_symbol: str
    url_name: str
    schema_version: Literal[1] = 1


class CalendarEvent(UtcWireModel):
    """Economic-calendar event definition."""

    id: ULong
    type: ENUM_CALENDAR_EVENT_TYPE
    sector: ENUM_CALENDAR_EVENT_SECTOR
    frequency: ENUM_CALENDAR_EVENT_FREQUENCY
    time_mode: ENUM_CALENDAR_EVENT_TIMEMODE
    country_id: ULong
    unit: ENUM_CALENDAR_EVENT_UNIT
    importance: ENUM_CALENDAR_EVENT_IMPORTANCE
    multiplier: ENUM_CALENDAR_EVENT_MULTIPLIER
    digits: UInt
    source_url: str
    event_code: str
    name: str
    schema_version: Literal[1] = 1


class CalendarValue(UtcWireModel):
    """One versioned observation for an economic-calendar event."""

    id: ULong
    event_id: ULong
    time: AwareDatetime
    period: AwareDatetime
    revision: Int
    actual_value: Long
    prev_value: Long
    revised_prev_value: Long
    forecast_value: Long
    impact_type: ENUM_CALENDAR_EVENT_IMPACT
    schema_version: Literal[1] = 1


__all__ = [
    "CalendarCountry",
    "CalendarEvent",
    "CalendarValue",
    "OrderBookEntry",
    "RateBar",
    "Tick",
    "as_utc",
]
