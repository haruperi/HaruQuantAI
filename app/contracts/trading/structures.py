"""Platform-neutral trading structures derived from the MQL5 reference."""

from typing import Annotated, Literal

from pydantic import AwareDatetime, Field

from app.contracts.common.wire_model import UtcWireModel
from app.contracts.trading.constants import (  # noqa: TC001
    ENUM_DEAL_TYPE,
    ENUM_ORDER_STATE,
    ENUM_ORDER_TYPE,
    ENUM_ORDER_TYPE_FILLING,
    ENUM_ORDER_TYPE_TIME,
    ENUM_TRADE_REQUEST_ACTIONS,
    ENUM_TRADE_TRANSACTION_TYPE,
)

UInt = Annotated[int, Field(ge=0, le=4_294_967_295)]
ULong = Annotated[int, Field(ge=0, le=18_446_744_073_709_551_615)]
NonNegativeFloat = Annotated[float, Field(ge=0)]


class TradeRequest(UtcWireModel):
    """Canonical provider-neutral trade execution request."""

    action: ENUM_TRADE_REQUEST_ACTIONS
    magic: ULong
    order: ULong
    symbol: str
    volume: NonNegativeFloat
    price: NonNegativeFloat
    stoplimit: NonNegativeFloat
    sl: NonNegativeFloat
    tp: NonNegativeFloat
    deviation: ULong
    type: ENUM_ORDER_TYPE
    type_filling: ENUM_ORDER_TYPE_FILLING
    type_time: ENUM_ORDER_TYPE_TIME
    expiration: AwareDatetime | None = None
    comment: str = ""
    position: ULong = 0
    position_by: ULong = 0
    schema_version: Literal[1] = 1


class TradeTransaction(UtcWireModel):
    """Canonical provider-neutral trade lifecycle transaction."""

    deal: ULong
    order: ULong
    symbol: str
    type: ENUM_TRADE_TRANSACTION_TYPE
    order_type: ENUM_ORDER_TYPE
    order_state: ENUM_ORDER_STATE
    deal_type: ENUM_DEAL_TYPE
    time_type: ENUM_ORDER_TYPE_TIME
    time_expiration: AwareDatetime | None = None
    price: NonNegativeFloat
    price_trigger: NonNegativeFloat
    price_sl: NonNegativeFloat
    price_tp: NonNegativeFloat
    volume: NonNegativeFloat
    position: ULong
    position_by: ULong
    schema_version: Literal[1] = 1


__all__ = ["TradeRequest", "TradeTransaction"]
