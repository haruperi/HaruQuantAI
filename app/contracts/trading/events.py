"""Typed Trading domain event payload for the DomainEvent envelope."""

from typing import Literal

from pydantic import Field

from app.contracts.common.models import JsonObject, Uuid7, WireModel

# The event-kind union is annotation-only for readers, but Pydantic resolves
# it at class-creation time, so it must remain a runtime import.
from app.contracts.trading.models import TradingEventKind  # noqa: TC001

# The single ordered Trading event type of record R28; the stream carries
# replay/resync semantics and is consumed through interfaces.
type TradingEventType = Literal["trading.event"]


class TradingEventPayload(WireModel):
    """Payload for ``trading.event`` DomainEvent envelopes (record R28).

    Events are ordered with replay/resync and keep stable links among
    plan/decision/reservation/operation/order/deal/position/protection/
    ledger/reconciliation records; ``sequence`` is the monotonic session
    sequence.
    """

    session_id: Uuid7
    sequence: int = Field(ge=1)
    kind: TradingEventKind
    operation_id: Uuid7 | None = None
    values: JsonObject
    schema_version: Literal[1] = 1


WIRE_EVENTS: dict[str, type[WireModel]] = {
    "TradingEventPayload": TradingEventPayload,
}
