"""Platform-neutral risk structures derived from the MQL5 reference."""

from typing import Annotated, Literal

from pydantic import Field

from app.contracts.common.wire_model import StrictWireModel

UInt = Annotated[int, Field(ge=0, le=4_294_967_295)]


class TradeCheckResult(StrictWireModel):
    """Provider-neutral pre-trade funds and margin check result."""

    retcode: UInt
    balance: float
    equity: float
    profit: float
    margin: float
    margin_free: float
    margin_level: float
    comment: str
    schema_version: Literal[1] = 1


__all__ = ["TradeCheckResult"]
