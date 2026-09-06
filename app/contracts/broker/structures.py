"""Platform-neutral broker structures derived from the MQL5 reference."""

from typing import Annotated, Literal

from pydantic import Field

from app.contracts.common.wire_model import StrictWireModel

UInt = Annotated[int, Field(ge=0, le=4_294_967_295)]
Int = Annotated[int, Field(ge=-2_147_483_648, le=2_147_483_647)]
ULong = Annotated[int, Field(ge=0, le=18_446_744_073_709_551_615)]
NonNegativeFloat = Annotated[float, Field(ge=0)]


class TradeResult(StrictWireModel):
    """Provider-neutral result returned for an execution request."""

    retcode: UInt
    deal: ULong
    order: ULong
    volume: NonNegativeFloat
    price: NonNegativeFloat
    bid: NonNegativeFloat
    ask: NonNegativeFloat
    comment: str
    request_id: UInt
    retcode_external: Int
    schema_version: Literal[1] = 1


__all__ = ["TradeResult"]
