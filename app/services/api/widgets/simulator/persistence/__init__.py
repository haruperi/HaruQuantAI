"""Simulation Workbench catalogue CRUD statement boundary.

The package owns only domain-record CRUD statement construction,
execution delegation through ``app.services.data``, and normalized row
handoff. Authorization, validation, policy, orchestration, and public
behaviour remain in the owning feature modules.
"""

from app.services.api.widgets.simulator.persistence.create import (
    create_simulation_batch_item_records,
    create_simulation_batch_record,
    create_simulation_result_record,
    create_simulation_session_record,
)
from app.services.api.widgets.simulator.persistence.read import (
    read_simulation_batch_items,
    read_simulation_batch_record,
    read_simulation_result_record,
    read_simulation_results_page,
    read_simulation_session_record,
    read_simulation_sessions,
)
from app.services.api.widgets.simulator.persistence.update import (
    annotate_simulation_result_record,
    archive_simulation_result_record,
    cancel_simulation_batch_item_records,
    retry_simulation_batch_item_record,
    transition_simulation_batch_item_record,
    transition_simulation_result_completion,
    update_simulation_batch_record,
    update_simulation_session_record,
)

__all__ = (
    "annotate_simulation_result_record",
    "archive_simulation_result_record",
    "cancel_simulation_batch_item_records",
    "create_simulation_batch_item_records",
    "create_simulation_batch_record",
    "create_simulation_result_record",
    "create_simulation_session_record",
    "read_simulation_batch_items",
    "read_simulation_batch_record",
    "read_simulation_result_record",
    "read_simulation_results_page",
    "read_simulation_session_record",
    "read_simulation_sessions",
    "retry_simulation_batch_item_record",
    "transition_simulation_batch_item_record",
    "transition_simulation_result_completion",
    "update_simulation_batch_record",
    "update_simulation_session_record",
)
