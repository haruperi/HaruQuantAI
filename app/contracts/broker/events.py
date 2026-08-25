"""Typed Broker domain event payloads for the DomainEvent envelope."""

from typing import Literal

from pydantic import Field

from app.contracts.common.models import (
    ContentHash,
    JsonObject,
    UtcTimestamp,
    Uuid7,
    ValidationIssue,
    WireModel,
)

# Closed provider-event kind union from the ratified Broker R10 record.
type ProviderEventKind = Literal[
    "QUOTE",
    "TICK",
    "DEAL",
    "ORDER_UPDATE",
    "POSITION_UPDATE",
    "MARKET_STATUS",
    "HEARTBEAT",
]


class ProviderEventPayload(WireModel):
    """Payload for broker.provider-event DomainEvent envelopes.

    The normalized observational event retains the raw provider identity
    hash and the fenced session generation; ``findings`` records sequence
    gaps, duplicates, late events, and decode failures as classified
    evidence. There are no subscriptions; consumers receive these events
    through the Interfaces trading stream.
    """

    session_id: Uuid7
    generation: int = Field(ge=1)
    kind: ProviderEventKind
    raw_provider_hash: ContentHash
    provider_sequence: int | None = Field(ge=0)
    event_time: UtcTimestamp | None
    receipt_time: UtcTimestamp
    values: JsonObject
    findings: tuple[ValidationIssue, ...] = ()
    schema_version: Literal[1] = 1


# Closed event-type discriminator for the broker provider event.
type ProviderEventType = Literal["broker.provider-event"]

WIRE_EVENTS: dict[str, type[WireModel]] = {
    "ProviderEventPayload": ProviderEventPayload,
}
