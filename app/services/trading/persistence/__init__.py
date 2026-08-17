"""Private Trading-owned CRUD persistence boundary."""

from app.services.trading.persistence.create import (
    create_closed_position_record,
    create_event_record,
    create_execution_session_record,
    create_idempotency_record,
    create_projection_record,
    create_trading_runtime_store,
)
from app.services.trading.persistence.delete import archive_execution_session_record
from app.services.trading.persistence.read import (
    read_all_event_records,
    read_event_records,
    read_execution_session_events,
    read_execution_session_record,
    read_execution_session_records,
    read_idempotency_record,
    read_idempotency_record_with_revision,
    read_projection_record,
    read_projection_record_with_revision,
)
from app.services.trading.persistence.update import (
    assign_simulation_session_identity_record,
    complete_simulation_session_configuration_record,
    set_default_execution_session_record,
    update_event_projection_records,
    update_execution_session_record,
    update_idempotency_record,
    update_projection_record,
)

__all__ = [
    "archive_execution_session_record",
    "assign_simulation_session_identity_record",
    "complete_simulation_session_configuration_record",
    "create_closed_position_record",
    "create_event_record",
    "create_execution_session_record",
    "create_idempotency_record",
    "create_projection_record",
    "create_trading_runtime_store",
    "read_all_event_records",
    "read_event_records",
    "read_execution_session_events",
    "read_execution_session_record",
    "read_execution_session_records",
    "read_idempotency_record",
    "read_idempotency_record_with_revision",
    "read_projection_record",
    "read_projection_record_with_revision",
    "set_default_execution_session_record",
    "update_event_projection_records",
    "update_execution_session_record",
    "update_idempotency_record",
    "update_projection_record",
]
