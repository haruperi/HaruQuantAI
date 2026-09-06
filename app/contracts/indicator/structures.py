"""Platform-neutral indicator structures derived from the MQL5 reference."""

from typing import Annotated

from pydantic import Field

from app.contracts.common.wire_model import StrictWireModel
from app.contracts.indicator.constants import ENUM_DATATYPE  # noqa: TC001

Long = Annotated[
    int,
    Field(ge=-9_223_372_036_854_775_808, le=9_223_372_036_854_775_807),
]


class IndicatorParameter(StrictWireModel):
    """One typed input parameter supplied to an indicator factory."""

    type: ENUM_DATATYPE
    integer_value: Long = 0
    double_value: float = 0.0
    string_value: str = ""


__all__ = ["IndicatorParameter"]
