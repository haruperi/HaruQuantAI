"""Typed Simulator domain event payload for the DomainEvent envelope."""

from typing import Literal

from pydantic import Field

from app.contracts.common.models import JsonObject, Uuid7, WireModel

# Closed simulation event-kind discriminator from ratified record R6.
type SimulationEventKind = Literal[
    "SIGNAL",
    "ORDER_SUBMITTED",
    "ORDER_FILLED",
    "ORDER_CANCELLED",
    "STOP_UPDATE",
    "FORCED_EXIT",
    "ERROR",
]

# The single observational Simulator event type of record R6. Batch progress
# is bounded observational publication, so no subscription surface exists.
type SimulationEventType = Literal["simulation.event"]


class SimulationEventPayload(WireModel):
    """Payload for ``simulation.event`` DomainEvent envelopes (record R6).

    ``sequence`` is the monotonic simulation sequence; first-divergence
    tooling identifies the earliest divergent event by comparing two
    ordered payloads without parsing logs.
    """

    sequence: int = Field(ge=0)
    kind: SimulationEventKind
    node_id: Uuid7 | None = None
    values: JsonObject
    schema_version: Literal[1] = 1


WIRE_EVENTS: dict[str, type[WireModel]] = {
    "SimulationEventPayload": SimulationEventPayload,
}
