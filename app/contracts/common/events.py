"""Common event envelope for typed owner payloads."""

from typing import Literal

from app.contracts.common.models import JsonObject, UtcTimestamp, Uuid7, WireModel


class DomainEvent(WireModel):
    """Causally linked, ordered cross-boundary event envelope."""

    event_id: Uuid7
    sequence: int
    event_type: str
    occurred_at: UtcTimestamp
    request_id: Uuid7
    capability_snapshot_id: Uuid7
    payload: JsonObject
    project_run_id: Uuid7 | None = None
    task_run_id: Uuid7 | None = None
    job_id: Uuid7 | None = None
    component_instance_id: Uuid7 | None = None
    reconciliation_id: Uuid7 | None = None
    schema_version: Literal[1] = 1


WIRE_EVENTS: dict[str, type[WireModel]] = {
    "DomainEvent": DomainEvent,
}
