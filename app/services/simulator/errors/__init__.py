"""Public Simulation error taxonomy."""

from app.services.simulator.errors.catalog import SIM_ERROR_CATALOG
from app.services.simulator.errors.exception import SimulationError
from app.services.simulator.errors.payload import (
    to_simulation_error_payload as _to_simulation_error_payload,
)
from app.services.simulator.errors.responses import (
    async_operation_guard,
    guard_async_operation,
    guard_operation,
    operation_guard,
    unwrap_simulation_response,
)

to_simulation_error_payload = guard_operation(
    _to_simulation_error_payload,
    operation="simulation.errors.to_simulation_error_payload",
    risk_level="low",
    read_only=True,
)

__all__ = [
    "SIM_ERROR_CATALOG",
    "SimulationError",
    "async_operation_guard",
    "guard_async_operation",
    "guard_operation",
    "operation_guard",
    "to_simulation_error_payload",
    "unwrap_simulation_response",
]
