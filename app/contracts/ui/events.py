"""Typed UI domain event payloads for the DomainEvent envelope."""

from typing import Literal

# This payload alias is annotation-only for readers but Pydantic resolves it
# at class-creation time, so it must remain a runtime import.
from app.contracts.common.models import Uuid7, WireModel
from app.contracts.ui.models import NonEmptyStr  # noqa: TC001


class WidgetLifecycleEventPayload(WireModel):
    """Payload for ui.widget-lifecycle events (record R36).

    Observational PUBLISH evidence for widget registration, mounting,
    quiescing, replacement, and removal; it is runtime diagnostics, never
    a port stream or authoritative business state.
    """

    instance_id: Uuid7
    widget_type: NonEmptyStr
    phase: Literal["REGISTERED", "MOUNTED", "QUIESCED", "REPLACED", "REMOVED"]
    schema_version: Literal[1] = 1


# Closed event-type discriminator union for the UI lifecycle event.
type WidgetEventType = Literal["ui.widget-lifecycle"]

WIRE_EVENTS: dict[str, type[WireModel]] = {
    "WidgetLifecycleEvent": WidgetLifecycleEventPayload,
}
