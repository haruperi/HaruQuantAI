"""Platform-neutral common structures derived from the MQL5 reference."""

from typing import Annotated, Literal

from pydantic import Field

from app.contracts.common.wire_model import StrictWireModel

Year = Annotated[int, Field(ge=1970, le=9999)]


class DateTimeParts(StrictWireModel):
    """Validated UTC calendar components for a point in time."""

    year: Year
    month: int = Field(ge=1, le=12)
    day: int = Field(ge=1, le=31)
    hour: int = Field(ge=0, le=23)
    min: int = Field(ge=0, le=59)
    sec: int = Field(ge=0, le=59)
    day_of_week: int = Field(ge=0, le=6)
    day_of_year: int = Field(ge=0, le=365)
    schema_version: Literal[1] = 1


__all__ = ["DateTimeParts"]
