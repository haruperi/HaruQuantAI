"""Public Simulation error taxonomy."""

from app.services.simulator.errors.catalog import SIM_ERROR_CATALOG
from app.services.simulator.errors.exception import SimulationError
from app.services.simulator.errors.payload import to_simulation_error_payload

__all__ = ["SIM_ERROR_CATALOG", "SimulationError", "to_simulation_error_payload"]
