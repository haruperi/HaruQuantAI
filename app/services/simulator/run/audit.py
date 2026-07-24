"""Governed Simulation audit-event emission."""

from collections.abc import Mapping
from datetime import datetime
from typing import TYPE_CHECKING

from app.services.simulator.errors import SimulationError
from app.utils import AuditEvent, AuthContext, generate_id, logger

if TYPE_CHECKING:
    from app.services.simulator.run.contracts import SimulationRunDependencies

type AuditJsonValue = (
    None
    | bool
    | int
    | float
    | str
    | tuple["AuditJsonValue", ...]
    | Mapping[str, "AuditJsonValue"]
)


def emit_simulation_audit(
    dependencies: SimulationRunDependencies,
    auth_context: AuthContext,
    action: str,
    timestamp: datetime,
    payload: Mapping[str, AuditJsonValue],
) -> None:
    """Construct and persist one bounded Simulation audit event.

    Args:
        dependencies: Explicit composition supplying durable audit persistence.
        auth_context: Authenticated trace and principal context.
        action: Cataloged Simulation action.
        timestamp: Deterministic UTC event time.
        payload: Bounded secret-safe action facts.

    Raises:
        SimulationError: If construction or persistence fails.
    """
    logger.info("Persisting Simulation audit action %s", action)
    try:
        event = AuditEvent(
            contract_version="v1",
            schema_id="utils.audit_event.v1",
            event_id=generate_id("evt"),
            timestamp=timestamp,
            domain="simulation",
            action=action,
            principal_id=auth_context.principal_id,
            request_id=auth_context.request_id,
            correlation_id=auth_context.correlation_id,
            payload=payload,
        )
        dependencies.persist_audit_event(event)
    except SimulationError:
        raise
    except Exception as error:
        raise SimulationError(
            "SIM_PERSISTENCE_FAILED",
            "Simulation audit persistence failed",
            request_id=auth_context.request_id,
            correlation_id=auth_context.correlation_id,
        ) from error


__all__ = ["emit_simulation_audit"]
