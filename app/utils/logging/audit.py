"""Caller-supplied append-only audit sink routing."""

from collections.abc import Callable, Mapping

from app.utils.errors.exceptions import ValidationError


def route_audit_event(
    event: Mapping[str, object] | object, sink: Callable[[object], None]
) -> None:
    """Route one redacted audit event and propagate sink failure.

    Args:
        event: AuditEvent object or EventEnvelope mapping.
        sink: Caller-supplied append-only sink.

    Raises:
        ValidationError: If mapping identity is invalid.
    """
    if isinstance(event, Mapping) and (
        event.get("contract_version") != "v1"
        or not isinstance(event.get("schema_id"), str)
    ):
        raise ValidationError("AUDIT_EVENT_INVALID")
    sink(event)
